# backend/apps/community/views.py

from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Exists, Subquery, OuterRef, Prefetch, Value, BooleanField # Q : 복잡한 조회 조건을 조합할 때 사용, Count : 집계 함수
from django.db.models.functions import Coalesce
from rest_framework import generics, status # generics : 제네릭 뷰 제공, status : HTTP 상태 코드
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.views import APIView # APIView : 기본 뷰 클래스, 좋아요 및 스크랩 토글에 사용

from .models import Board, Post, Comment, Scrap, PostLike
from .serializers import (
    BoardSerializer, PostListSerializer, PostSerializer,
    CommentSerializer, ScrapSerializer
)
from .permissions import IsOwnerOrReadOnly
        

# 개요
"""
1. Board
- 1.1 BoardListView          | 게시판 목록

2. Post
- 2.1 PostListView           | 게시글 목록 + 생성
- 2.2 PostDetailView         | 게시글 단건 조회/수정/삭제 (작성자만)
- 2.3 PostSearchView         | 게시글 검색 + 게시판 필터링

3. Comment
- 3.1 CommentListView        | 댓글 목록 + 생성
- 3.2 CommentDetailView      | 댓글 단건 조회/수정/삭제 (작성자만)

4. Like / Scrap
- 4.1 PostLikeView           | 게시글 좋아요 토글
- 4.2 PostScrapView          | 게시글 스크랩 토글
"""


# =========================
# 1) Board Views
# =========================

# 1.1 BoardListView | 게시판 목록
class BoardListView(generics.ListAPIView):
    """
    [설계의도]
    - 커뮤니티에 존재하는 모든 게시판 목록을 조회하기 위한 엔드포인트

    [상세고려사항]
    - 게시판은 인증 여부와 무관하게 접근 가능
    - annotate(posts_count)를 통해 게시판별 게시글 수를 한 번의 쿼리로 계산
    - Serializer가 이 annotate 결과를 직접 사용하도록 설계

    [최적화 내용]
    - annotate로 집계한 posts_count를 Serializer에서 그대로 사용
    - N+1 문제 완전 제거 (Board 10개 → 쿼리 1개)
    """
    queryset = Board.objects.annotate(posts_count=Count('posts')).all()
    serializer_class = BoardSerializer
    permission_classes = []
    # TODO: 캐싱 적용 시 cache_page 데코레이터 또는 get_queryset에서 cache 사용

# =========================
# 2) Post Views
# =========================

# 2.1 PostListView | 게시글 목록 + 생성
class PostListView(generics.ListCreateAPIView):
    # ↑ ListCreateAPIView: GET(목록) + POST(생성)을 한 엔드포인트에서 처리
    """
    [설계의도]
    - 특정 게시판에 속한 게시글 목록 조회 및 게시글 생성 담당

    [상세고려사항]
    - GET과 POST를 하나의 View로 묶어 게시판 단위 책임을 명확히 함
    - board_name, board_id 두 방식 모두 지원하여 URL 유연성 확보
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    # ↑ 비로그인: GET만 허용 / 로그인: POST도 허용
    #   - "읽기는 공개, 쓰기는 인증 필요" 패턴

    def get_serializer_class(self):
        # ↑ 같은 View라도 요청에 따라 serializer를 바꿔 쓰고 싶을 때 오버라이드
        """
        [설계의도]
        - 요청 메서드에 따라 serializer를 분리하여 사용

        [상세고려사항]
        - GET: 목록은 응답 payload 최소화를 위해 PostListSerializer 사용
        - POST: 입력 필드와 상세 필드가 필요하므로 PostSerializer 사용
        """
        if self.request.method == 'POST':
            return PostSerializer
        return PostListSerializer

    def get_queryset(self):
        """
        [설계의도]
        - 게시판 기준으로 게시글 목록을 조회
        - 모든 집계 필드를 queryset 단계에서 미리 계산하여 Serializer N+1 방지

        [상세고려사항]
        - board_id, board_name 중 하나만 존재해도 조회 가능
        - 최상위 댓글 기준 comments_count 집계
        - 좋아요 수를 annotate로 미리 계산
        - select_related로 author, board 조인하여 추가 쿼리 방지

        [최적화 내용]
        - annotate 필드를 Serializer가 직접 사용하도록 설계
        - 단일 쿼리로 모든 집계 완료
        """
        board_name = self.kwargs.get('board_name')
        board_id = self.kwargs.get('board_id')

        # 기본 queryset 구성
        queryset = Post.objects.select_related('author', 'board').annotate(
            likes_count=Count('post_likes', distinct=True),
            comments_count=Count('comments', distinct=True)
        )

        # 게시판 필터링
        if board_id:
            board = get_object_or_404(Board, pk=board_id)
            queryset = queryset.filter(board=board)
        elif board_name:
            board = get_object_or_404(Board, name=board_name)
            queryset = queryset.filter(board=board)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # ↑ CreateAPIView 계열에서 "저장 직전"에 서버가 강제로 값을 주입하고 싶을 때 오버라이드
        """
        [설계의도]
        - 게시글 생성 시 작성자와 게시판을 서버에서 명시적으로 지정

        [상세고려사항]
        - URL 기준(board_id / board_name)을 우선 신뢰
        - 요청 본문에 board_id가 포함된 경우도 fallback으로 허용
        """
        # board_id로 게시글 생성 (API 설계 문서 기준)
        board_id = self.kwargs.get('board_id')
        board_name = self.kwargs.get('board_name')

        if board_id:
            board = get_object_or_404(Board, pk=board_id)
        elif board_name:
            board = get_object_or_404(Board, name=board_name)
        else:
            # 요청 본문에서 board_id를 받을 수도 있음
            board = serializer.validated_data.get('board')

        serializer.save(author=self.request.user, board=board)

# 2.2 PostDetailView | 게시글 단건 조회/수정/삭제
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    [설계의도]
    - 게시글 단건 조회, 수정, 삭제를 담당하는 View

    [상세고려사항]
    - 작성자만 수정/삭제 가능하도록 IsOwnerOrReadOnly 적용
    - 댓글, 좋아요, 스크랩을 함께 prefetch하여 성능 최적화
    - 사용자별 상태(is_liked, is_scrapped)를 annotate로 미리 계산

    [최적화 내용]
    - Subquery를 활용하여 is_liked, is_scrapped를 단일 쿼리에서 계산
    - Prefetch를 활용하여 댓글 트리를 효율적으로 로드
    """
    serializer_class = PostSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_url_kwarg = 'post_id'

    def get_queryset(self):
        """
        [설계의도]
        - 게시글 상세 조회 시 필요한 모든 데이터를 한 번의 쿼리로 로드

        [상세고려사항]
        - is_liked, is_scrapped를 Subquery로 계산하여 N+1 방지
        - 댓글 및 대댓글을 Prefetch로 효율적으로 로드
        """
        

        user = self.request.user

        # [설계의도]
        # - 현재 사용자가 해당 게시글에 좋아요를 눌렀는지 여부를 Subquery로 계산
        # [상세고려사항]
        # - 로그인하지 않은 사용자는 항상 False
        # - Exists를 사용하여 효율적인 boolean 연산
        if user.is_authenticated:
            user_liked_subquery = Exists(
                PostLike.objects.filter(
                    post=OuterRef('pk'),
                    user=user
                )
            )
            user_scrapped_subquery = Exists(
                Scrap.objects.filter(
                    post=OuterRef('pk'),
                    user=user
                )
            )
        else:
            user_liked_subquery = Value(False, output_field=BooleanField())
            user_scrapped_subquery = Value(False, output_field=BooleanField())

        return Post.objects.select_related('author', 'board').prefetch_related(
            # [설계의도]
            # - 최상위 댓글과 그 작성자를 미리 로드
            # - 대댓글과 대댓글 작성자도 함께 로드하여 N+1 방지
            Prefetch(
                'comments',
                queryset=Comment.objects.filter(parent=None).select_related('author').prefetch_related(
                    Prefetch(
                        'replies',
                        queryset=Comment.objects.select_related('author').order_by('created_at')
                    )
                ).order_by('created_at')
            )
        ).annotate(
            likes_count=Count('post_likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            is_liked=user_liked_subquery,
            is_scrapped=user_scrapped_subquery
        )

# 2.3 PostSearchView | 게시글 검색 + 게시판 필터링
class PostSearchView(generics.ListAPIView):
    # 검색은 "조회만" 하므로 ListAPIView
    """
    [설계의도]
    - 게시글 검색 전용 엔드포인트

    [상세고려사항]
    - 제목/내용 기준 부분 검색
    - 게시판 필터(board_id)는 선택 사항
    - 정규화 수행 (공백 제거, 키워드 분리)
    """
    serializer_class = PostListSerializer
    permission_classes = []  # 누구나 검색 가능

    def get_queryset(self):
        """
        [설계의도]
        - 검색 조건을 조합하여 queryset 구성

        [상세고려사항]
        - 검색어가 없을 경우 전체 게시글 반환
        - annotate를 통해 집계 필드 사전 계산

        [로직 개선]
        1. 검색어 앞뒤 공백 제거 (strip)
        2. board_id가 숫자인지 확인 (isdigit)
        3. 검색어를 공백 기준으로 쪼개서(split) AND 조건으로 검색 (검색 정규화)
        """
        # 1. 입력값 가져오기 및 1차 정규화 (공백 제거)
        query = self.request.query_params.get('q', '').strip()
        board_id = self.request.query_params.get('board_id')

        # 2. 기본 queryset 준비
        queryset = Post.objects.select_related('author', 'board').annotate(
            likes_count=Count('post_likes', distinct=True),
            comments_count=Count('comments', distinct=True)
        )

        # 3. 게시판 필터링 (유효성 검증 추가)
        # board_id가 존재하고, 실제로 숫자로만 구성되어 있을 때만 필터 적용
        if board_id and board_id.isdigit():
            queryset = queryset.filter(board_id=board_id)

        # 4. 검색어 필터링 (다중 키워드 처리 정규화)
        if query:
            # "파이썬 장고" 입력 시 -> ['파이썬', '장고'] 로 분리
            keywords = query.split()
            
            # 모든 키워드가 포함된 게시글을 찾기 위한 Q 객체 생성 (AND 조건)
            # 하나라도 포함되면 되는 OR 조건을 원하면 아래 &= 를 |= 로 변경
            search_filter = Q()
            for keyword in keywords:
                search_filter &= (Q(title__icontains=keyword) | Q(content__icontains=keyword))
            
            queryset = queryset.filter(search_filter)

        return queryset.order_by('-created_at') # 최신순


# ====================
# 3) Comment Views
# ====================

# 3.1 CommentListView | 댓글 목록 + 생성
class CommentListView(generics.ListCreateAPIView):
    # ↑ 댓글도 목록 + 생성이 필요하니 ListCreateAPIView
    """
    [설계의도]
    - 게시글에 속한 댓글 목록 조회 및 댓글 생성 담당

    [상세고려사항]
    - 최상위 댓글만 직접 조회
    - 대댓글은 replies 관계를 통해 포함
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        [설계의도]
        - 특정 게시글의 최상위 댓글만 조회
        - 대댓글을 Prefetch로 한 번에 로드하여 N+1 방지

        [상세고려사항]
        - parent=None 조건으로 댓글 depth 1만 반환
        - 대댓글은 serializer에서 재귀 처리하되, 이미 prefetch로 로드됨
        - 대댓글의 대댓글까지 고려한 Prefetch 구성

        [최적화 내용]
        - Prefetch를 중첩하여 대댓글 트리를 효율적으로 로드
        - 최대 depth 2~3까지 지원 (필요 시 확장 가능)
        """

        post_id = self.kwargs.get('post_id')

        return Comment.objects.filter(
            post_id=post_id,
            parent=None
        ).select_related('author').prefetch_related(
            # [설계의도]
            # - 대댓글과 대댓글 작성자를 미리 로드
            # - 대댓글의 대댓글도 필요 시 로드 (depth 3)
            Prefetch(
                'replies',
                queryset=Comment.objects.select_related('author').prefetch_related(
                    Prefetch(
                        'replies',
                        queryset=Comment.objects.select_related('author').order_by('created_at')
                    )
                ).order_by('created_at')
            )
        ).order_by('created_at')

    def perform_create(self, serializer):
        # ↑ 댓글 생성 시 post/author/parent를 서버에서 고정해 무결성 유지
        """
        [설계의도]
        - 댓글 및 대댓글 생성 로직 통합 처리

        [상세고려사항]
        - parent 값이 존재하면 대댓글로 처리
        - parent는 반드시 동일 게시글의 댓글이어야 함
        """
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, pk=post_id)

        # 대댓글인 경우 parent 설정
        parent_id = self.request.data.get('parent')
        parent_comment = None
        if parent_id:
            parent_comment = get_object_or_404(Comment, pk=parent_id, post=post)

        serializer.save(author=self.request.user, post=post, parent=parent_comment)
        # ↑ 댓글 작성자/게시글/부모댓글을 서버가 확정해서 저장
        #   - 최상위 댓글이면 parent=None으로 저장됨

# 3.2 CommentDetailView | 댓글 단건 조회/수정/삭제
class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    [API]
    - GET: /community/comments/<comment_id>/
    - PUT/PATCH: /community/comments/<comment_id>/
    - DELETE: /community/comments/<comment_id>/

    [설계의도]
    - 댓글 단건 조회, 수정, 삭제 담당

    [상세고려사항]
    - 댓글 작성자만 수정/삭제 가능
    - 게시글 하위 URL과 단독 URL 모두 대응 가능
    """
    queryset = Comment.objects.select_related('author', 'post').all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_url_kwarg = 'comment_id'


# =========================
# 4) Like / Scrap Views
# =========================

# 4.1 PostLikeView | 게시글 좋아요 토글
class PostLikeView(APIView):
    # ↑ 좋아요는 "토글 액션"이라 제네릭보다 APIView가 직관적(메서드 하나로 처리)
    """
    [API]
    - POST: /community/posts/<post_id>/likes/

    [설계의도]
    - 게시글 좋아요 상태를 토글 방식으로 처리

    [상세고려사항]
    - POST 단일 메서드로 프론트엔드 구현 단순화
    - 멱등성보다는 UX 편의성을 우선한 실무형 설계
    """
    permission_classes = [IsAuthenticated] # 로그인 필요

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        user = request.user

        # 이미 좋아요를 눌렀다면,
        if post.likes.filter(pk=user.pk).exists():
            post.likes.remove(user)
            message = "좋아요를 취소했습니다."
            is_liked = False
        # 아직 좋아요를 누르지 않았다면,
        else:
            post.likes.add(user)
            message = "좋아요를 눌렀습니다."
            is_liked = True

        return Response({
            "detail": message,
            "is_liked": is_liked,
            "likes_count": post.likes.count()
        }, status=status.HTTP_200_OK)

# 4.2 PostScrapView | 게시글 스크랩 토글
class PostScrapView(APIView):
    # ↑ 스크랩도 토글 액션 성격이라 APIView로 처리
    """
    [설계의도]
    - 게시글 스크랩 상태를 토글 방식으로 처리

    [상세고려사항]
    - Scrap 모델을 사용하여 중복 스크랩 방지
    - 생성/삭제 결과에 따라 상태 코드 분리 반환
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        user = request.user

        # 중복 스크랩 방지
        scrap, created = Scrap.objects.get_or_create(user=user, post=post)

        if created:
            return Response({
                "detail": "스크랩했습니다.",
                "is_scrapped": True
            }, status=status.HTTP_201_CREATED)
        else:
            scrap.delete()
            return Response({
                "detail": "스크랩을 취소했습니다.",
                "is_scrapped": False
            }, status=status.HTTP_200_OK)
