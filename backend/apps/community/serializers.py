from rest_framework import serializers
from .models import Board, Post, Comment, Scrap
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_field, OpenApiTypes

# 현재 settings에 등록된 User 모델을 가져오는 함수 
# - 커스텀 유저 모델을 사용하는 상황에서도 호환되게끔
User = get_user_model()

# 개요
"""
0. 공통
- 0.1. UserSerializer         | 작성자 표시용으로 최소한의 정보.

1. Board
- 1.1. BoardSerializer        | 게시판 목록

2. Post
- 2.1. PostListSerializer     | 게시글 목록용
- 2.2. PostSerializer         | 게시글 상세용

3. Comment
- 3.1. CommentSerializer      | 댓글 + 대댓글 재귀 표현

4. Scrap
- 4.1. ScrapSerializer        | 스크랩 목록용

"""


# 0.1 UserSerializer | 작성자 표시용 최소 정보
class UserSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 게시글/댓글 작성자 정보 노출용 최소 단위 시리얼라이저

    [상세고려사항]
    - 개인정보 최소화 원칙에 따라 필드 제한
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name')
        read_only_fields = ('id', 'username', 'email', 'name')


# 1.1 BoardSerializer | 게시판 목록
class BoardSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 게시판 목록 화면에서 사용하는 전용 Serializer
    - 게시판의 기본 정보와 함께, 해당 게시판에 속한 게시글 수(post_count)를
      요약 정보로 제공하기 위함

    [상세고려사항]
    - posts_count는 View 단계에서 annotate로 미리 계산된 값을 사용
    - source='posts.count' 방식은 N+1 문제를 유발하므로 제거
    - View의 annotate 결과를 그대로 사용하여 성능 최적화

    [최적화 내용]
    - 기존: source='posts.count' → 각 Board마다 COUNT 쿼리 실행 (N+1)
    - 변경: View의 annotate 필드 직접 사용 → 단일 쿼리로 처리
    """
    # source='posts.count' 대신 View에서 주입된 annotate 필드 사용
    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = ('id', 'name', 'description', 'created_at', 'posts_count')
        read_only_fields = ('id', 'created_at', 'posts_count')


# 2.1 PostListSerializer | 게시글 목록용
class PostListSerializer(serializers.ModelSerializer):
    # ↑ 목록용 serializer는 일반적으로 "필드 최소화 + 빠른 응답"이 목적
    """
    [설계의도]
    - 게시글 목록 화면 최적화 시리얼라이저
    - 게시글의 기본 정보 + 작성자 + 게시판 이름 + 좋아요 수 + 최상위 댓글 수 제공
    - 목록 응답에서 불필요한 필드(예: content)를 제외하여 경량화
    - N+1 문제를 완전히 제거하여 성능 최적화

    [상세고려사항]
    - content 제외로 응답 payload 최소화
    - board_name, likes_count, comments_count는 별도 필드로 제공
    - comments_count는 최상위 댓글 수만 집계
    - like_count, comments_count는 View의 annotate결과 직접 사용
    """
    author = UserSerializer(read_only=True)
    board_name = serializers.CharField(source='board.name', read_only=True)
    # ↑ Post.board.name을 board_name이라는 문자열 필드로 노출
    #   - board 전체 객체를 내려주기엔 목록 응답이 무거울 수 있으니 이름만 제공하는 설계
    # [설계의도]
    # - View에서 annotate(likes_count=Count('likes'))로 계산한 값을 직접 사용
    # [상세고려사항]
    # - 기존: source='likes.count' → N+1 문제 (각 Post마다 COUNT 쿼리)
    # - 변경: annotate 필드 직접 사용 → 단일 쿼리로 처리
    likes_count = serializers.IntegerField(read_only=True)

    # [설계의도]
    # - View에서 annotate(comments_count=Count(...))로 계산한 값을 직접 사용
    # [상세고려사항]
    # - 기존: SerializerMethodField + count() → N+1 문제
    # - 변경: annotate 필드 직접 사용 → 성능 개선
    # SerializerMethodField 대신 IntegerField로 변경
    comments_count = serializers.IntegerField(read_only=True)

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
        - #TODO 목록에서 각 Post마다 count() 호출 시 N+1 가능성 주의, 실수로 호출될 경우 N+1 문제를 유발할 수 있음.
        """
        return obj.comments.filter(parent=None).count()

# 2.2 PostSerializer | 게시글 상세용
class PostSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 게시글 상세 화면에서 필요한 모든 정보를 한 번에 제공하기 위한 시리얼라이저
    - 게시글 본문 + 작성자 + 게시판 정보 + 댓글 트리 + 사용자 개인 상태(좋아요/스크랩)를 포함

    [상세고려사항]
    - 목록용(PostListSerializer)과 분리하여 payload 크기 및 책임을 명확히 구분
    - request context를 활용해 사용자별 상태(is_liked, is_scrapped)를 계산
    - 댓글은 별도 API로 제공하므로 포함하지 않음 (또는 최상위만 제공)

    [최적화 내용]
    - likes_count: annotate 필드 직접 사용
    - is_liked: View에서 Subquery로 미리 계산된 값 사용
    - is_scrapped: View에서 Subquery로 미리 계산된 값 사용
    """
    author = UserSerializer(read_only=True)
    board = BoardSerializer(read_only=True)
    board_id = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.all(),
        source='board',
        write_only=True,
        required=False
    )

    comments = serializers.SerializerMethodField()

    # [설계의도]
    # - View에서 annotate로 계산된 좋아요 수 사용
    # [상세고려사항]
    # - N+1 방지를 위해 source 제거
    likes_count = serializers.IntegerField(read_only=True)

    # [설계의도]
    # - View에서 annotate로 계산된 댓글 수 사용
    # [상세고려사항]
    # - N+1 방지를 위해 source 제거
    comments_count = serializers.IntegerField(read_only=True)

    # [설계의도]
    # - View에서 Subquery 또는 prefetch로 미리 계산된 값 사용
    # [상세고려사항]
    # - 기존: 각 Post마다 exists() 쿼리 실행 (N+1)
    # - 변경: View의 annotate 결과 직접 사용
    # - View에서 user_has_liked 같은 필드로 annotate 해야 함
    is_liked = serializers.BooleanField(read_only=True)

    # [설계의도]
    # - View에서 Subquery 또는 prefetch로 미리 계산된 값 사용
    # [상세고려사항]
    # - 기존: 각 Post마다 Scrap.objects.filter().exists() 실행 (N+1)
    # - 변경: View의 annotate 결과 직접 사용
    is_scrapped = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = (
            'id', 'author', 'board', 'board_id', 'title', 'content',
            'created_at', 'updated_at', 'likes_count', 'comments_count', 'is_liked',
            'is_scrapped', 'comments'
        )
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

    def get_comments(self, obj):
        """
        [설계의도]
        - View의 Prefetch 객체를 통해 미리 로드(parent=None 필터링됨)된 데이터를 사용

        [Fix] .filter(parent=None) 대신 .all() 사용
        - 이유: filter()는 무조건 DB 쿼리를 다시 날림.
        - View에서 Prefetch('comments', queryset=Comment.objects.filter(parent=None)...)을
          사용했다고 가정하면, .all()을 해야 캐시된(이미 필터링된) 리스트를 반환함.
        """
        # View에서 Prefetch 설정을 잘 했다면 .all()에 최상위 댓글만 들어있음
        top_level_comments = obj.comments.all()
        return CommentSerializer(top_level_comments, many=True).data

# 3.1 CommentSerializer | 댓글 + 대댓글 재귀 표현
class CommentSerializer(serializers.ModelSerializer):
    """
    [설계의도]
    - 댓글 + 대댓글을 재귀적으로 표현하기 위한 시리얼라이저
    - prefetch_related로 미리 로드된 대댓글 사용하여 N+1 방지

    [상세고려사항]
    - replies는 SerializerMethodField로 동적 계산
    - View에서 prefetch_related('replies__author')로 미리 로드 필요
    """
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'author', 'post', 'parent', 'content', 'created_at', 'updated_at', 'replies')
        read_only_fields = ('id', 'author', 'post', 'created_at', 'updated_at')

    def get_replies(self, obj):
        """
        [설계의도]
        - 대댓글을 재귀 구조로 포함
        - prefetch_related로 미리 로드된 데이터 활용

        [상세고려사항]
        - 기존: obj.replies.exists() → 각 댓글마다 EXISTS 쿼리 실행 (N+1)
        - 변경: obj.replies.all() 직접 사용 → prefetch로 이미 로드된 데이터 활용
        - exists() 체크 제거로 쿼리 감소
        """
        # prefetch_related로 미리 로드되어 있으므로 추가 쿼리 없음
        replies = obj.replies.all()
        if replies:
            return CommentSerializer(replies, many=True).data
        return []

# 4.1 ScrapSerializer | 스크랩 목록용
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
