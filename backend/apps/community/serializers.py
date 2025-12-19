from rest_framework import serializers
from .models import Board, Post, Comment, Scrap
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_field, OpenApiTypes

# 현재 settings에 등록된 User 모델을 가져오는 함수 
# - 커스텀 유저 모델을 사용하는 상황에서도 호환되게끔
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 게시글/댓글 작성자 정보 노출용 최소 단위 시리얼라이저

    [상세고려사항]
    - 개인정보 최소화 원칙에 따라 필드 제한
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id', 'username', 'email')


class BoardSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 게시판 목록 화면에서 사용하는 전용 Serializer
    - 게시판의 기본 정보와 함께, 해당 게시판에 속한 게시글 수(post_count)를
      요약 정보로 제공하기 위함

    [상세 고려 사항]
    - post_count는 Board ↔ Post 간 역참조 관계를 활용하여 계산됨
    - source='posts.count'는 Board 객체 기준으로
      obj.posts.count()를 내부적으로 호출해 게시글 개수를 반환
    - 구현이 간단하고 가독성이 좋지만,
      리스트 조회 시 객체 수만큼 count 쿼리가 발생할 수 있어(N+1 문제)
      #TODO 대규모 트래픽 환경에서는 queryset 단계에서 annotate로 대체하는 것이 바람직함
    """
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)

    class Meta:
        model = Board
        fields = ('id', 'name', 'description', 'created_at', 'posts_count')
        read_only_fields = ('id', 'created_at', 'posts_count')


class CommentSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 댓글 + 대댓글을 재귀적으로 표현하기 위한 시리얼라이저

    [상세고려사항]
    - replies는 SerializerMethodField로 동적 계산
    """
    author = UserSerializer(read_only=True)
    # ↑ Comment.author를 그대로 id로만 주지 않고, UserSerializer로 "중첩(nested)" 출력
    #   - read_only라서 댓글 생성 시 author를 body로 받지 않음(서버에서 넣어야 함)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'author', 'post', 'parent', 'content', 'created_at', 'updated_at', 'replies')
        read_only_fields = ('id', 'author', 'post', 'created_at', 'updated_at')

    def get_replies(self, obj):
        """
        [설계의도]
        - 대댓글을 재귀 구조로 포함

        [상세고려사항]
        # TODO
        - 이 구조는 "깊이"가 깊거나 댓글이 많으면 호출이 많이 발생할 수 있음
        - prefetch_related('replies__author') 같은 최적화 고도화 필요.
        - views.py에서 어느 정도는 하고 있음.
        """
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


class PostListSerializer(serializers.ModelSerializer):
    # ↑ 목록용 serializer는 일반적으로 "필드 최소화 + 빠른 응답"이 목적
    """
    [설계의도]
    - 게시글 목록 화면 최적화 시리얼라이저

    [상세고려사항]
    - content 제외로 응답 payload 최소화
    """
    author = UserSerializer(read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)
    # ↑ Post.board.name을 board_name이라는 문자열 필드로 노출
    #   - board 전체 객체를 내려주기엔 목록 응답이 무거울 수 있으니 이름만 제공하는 설계
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    # ↑ 좋아요 수를 likes.count로 노출
    #TODO: source='likes_count'(annotate 필드)를 쓰는 편이 N+1 방지에 더 좋음
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'author', 'board_name', 'title',
            'created_at', 'updated_at', 'likes_count', 'comments_count'
        )
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

    @extend_schema_field(OpenApiTypes.INT)
    def get_comments_count(self, obj):
        """
        [설계의도]
        - 최상위 댓글 수만 노출

        [상세고려사항]
        - #TODO 목록에서 각 Post마다 count() 호출 시 N+1 가능성 주의
        """
        return obj.comments.filter(parent=None).count()

class PostSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 게시글 상세 화면에서 필요한 모든 정보를 한 번에 제공하기 위한 시리얼라이저
    - 게시글 본문 + 작성자 + 게시판 정보 + 댓글 트리 + 사용자 개인 상태(좋아요/스크랩)를 포함

    [상세고려사항]
    - 목록용(PostListSerializer)과 분리하여 payload 크기 및 책임을 명확히 구분
    - request context를 활용해 사용자별 상태(is_liked, is_scrapped)를 계산
    - 댓글은 별도 API로 제공하므로 포함하지 않음
    """
    # 게시글 작성자 정보
    author = UserSerializer(read_only=True)
    # 게시글이 속한 게시판 정보
    board = BoardSerializer(read_only=True)

    # [설계의도]
    # - 게시글 생성/수정 시 게시판을 ID로만 지정할 수 있도록 하기 위한 필드
    # [상세고려사항]
    # - source='board'로 실제 board FK와 매핑
    # - write_only=True로 응답에는 노출하지 않음
    board_id = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        source='board',
        write_only=True
    )

    # [설계의도]
    # - 게시글 상세 조회 시 댓글 트리를 함께 반환
    # [상세고려사항]
    # - 최상위 댓글만 직접 조회하고, 대댓글은 CommentSerializer 내부에서 재귀 처리
    comments = serializers.SerializerMethodField()

    # 게시글의 좋아요 수를 집계 값으로 제공
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)

    # [설계의도]
    # - 현재 로그인한 사용자가 해당 게시글에 좋아요를 눌렀는지 여부 제공
    # [상세고려사항]
    # - 비로그인 사용자의 경우 항상 False 반환
    is_liked = serializers.SerializerMethodField()

    # [설계의도]
    # - 현재 로그인한 사용자가 게시글을 스크랩했는지 여부 제공
    # [상세고려사항]
    # - Scrap 테이블을 직접 조회하여 상태 판단
    is_scrapped = serializers.SerializerMethodField()

    class Meta:
        """
        [설계의도]
        - 게시글 상세 화면에서 필요한 필드만 명시적으로 관리
        """
        model = Post
        fields = (
            'id', 'author', 'board', 'board_id', 'title', 'content',
            'created_at', 'updated_at', 'likes_count', 'is_liked',
            'is_scrapped', 'comments'
        )
        # [설계의도] 서버에서 자동 관리되는 필드는 수정 불가 처리
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')
    
    def get_comments(self, obj):
        """
        [설계의도]
        - 댓글 트리의 진입점 역할
        - 게시글에 속한 최상위 댓글만 조회

        [상세고려사항]
        - parent=None 조건으로 1depth 댓글만 조회
        - 대댓글은 CommentSerializer.get_replies()에서 재귀적으로 포함
        - # TODO 성능 최적화 필요
            - 댓글/대댓글이 많으면 payload가 커질 수 있음(페이지네이션 고려 대상)
        """
        top_level_comments = obj.comments.filter(parent=None)
        return CommentSerializer(top_level_comments, many=True).data

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_liked(self, obj):
        """
        [설계의도]
        - 사용자 맞춤 UI 렌더링을 위한 좋아요 상태 제공

        [상세고려사항]
        - serializer context에 request가 주입되어야 정상 동작
        - 인증되지 않은 사용자는 False 처리
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(pk=request.user.pk).exists()
        return False

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_scrapped(self, obj):
        """
        [설계의도]
        - 사용자 맞춤 UI 렌더링을 위한 스크랩 상태 제공

        [상세고려사항]
        - Scrap 테이블 기준으로 존재 여부만 확인
        - 인증되지 않은 사용자는 False 처리
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Scrap.objects.filter(user=request.user, post=obj).exists()
        return False


class ScrapSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 마이페이지 등에서 사용자의 스크랩 목록을 조회하기 위한 시리얼라이저

    [상세고려사항]
    - 스크랩 자체 정보보다 '어떤 게시글을 스크랩했는지'가 핵심이므로
      PostListSerializer를 중첩 사용
    """
    # 스크랩된 게시글 정보를 목록 형태로 제공
    post = PostListSerializer(read_only=True)

    class Meta:
        """
        [설계의도]
        - 스크랩 관계의 최소 정보만 노출
        """
        model = Scrap
        fields = ('id', 'user', 'post', 'created_at')
        # 사용자 및 생성 시점은 서버에서 관리
        read_only_fields = ('id', 'user', 'created_at')
