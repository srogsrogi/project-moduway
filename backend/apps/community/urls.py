from django.urls import path
from apps.community import views

app_name = 'community'

urlpatterns = [

    # ==================================================
    # Board API (C01)
    # ==================================================
    # [GET]
    # /community/boards/
    # - 기능: 전체 게시판 목록 조회
    # - 비고: 게시판별 게시글 수(posts_count) 포함
    path(
        'boards/',
        views.BoardListView.as_view(),
        name='board-list'
    ),

    # ==================================================
    # Post API (C02, C03, C04)
    # ==================================================
    
    # [설계 의도]
    # 장고 공식 문서 | "More specific patterns should be listed before less specific patterns."
    # 숫자열 우선 탐색하도록 하기 위하여 순서 지정.

    # [GET, POST]
    # /community/<board_id>/posts/
    # - GET : 특정 게시판의 게시글 목록 조회
    # - POST: 특정 게시판에 게시글 작성
    # - 예시: /community/3/posts/
    path(
        '<int:board_id>/posts/',
        views.PostListView.as_view(),
        name='post-list-by-id'
    ),

    # [GET]
    # /community/<board_name>/posts/
    # - 기능: 특정 게시판의 게시글 목록 조회 (board_name 기준)
    # - 예시: /community/인문_소통방/posts/
    path(
        '<str:board_name>/posts/',
        views.PostListView.as_view(),
        name='post-list-by-name'
    ),

    

    # [GET, PUT, PATCH, DELETE]
    # /community/posts/<post_id>/
    # - GET    : 게시글 상세 조회
    # - PUT    : 게시글 전체 수정
    # - PATCH  : 게시글 부분 수정
    # - DELETE : 게시글 삭제
    # - 예시: /community/posts/1/
    path(
        'posts/<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post-detail'
    ),

    # ==================================================
    # Search API (C08)
    # ==================================================

    # [GET]
    # /community/posts/search/
    # - 기능: 게시글 검색
    # - 쿼리 파라미터:
    #   - q        : 검색어
    #   - board_id : 게시판 필터 (선택)
    # - 예시: /community/posts/search/?q=테스트&board_id=3
    path(
        'posts/search/',
        views.PostSearchView.as_view(),
        name='post-search'
    ),

    # ==================================================
    # Comment API (C05)
    # ==================================================

    # [GET, POST]
    # /community/posts/<post_id>/comments/
    # - GET : 특정 게시글의 댓글 목록 조회
    # - POST: 특정 게시글에 댓글 작성
    # - 예시: /community/posts/1/comments/
    path(
        'posts/<int:post_id>/comments/',
        views.CommentListView.as_view(),
        name='comment-list'
    ),

    # [DELETE, PUT, PATCH]
    # /community/posts/<post_id>/comments/<comment_id>/
    # - 예시: /community/posts/1/comments/5/
    path(
        'posts/<int:post_id>/comments/<int:comment_id>/',
        views.CommentDetailView.as_view(),
        name='comment-detail'
    ),

    # ==================================================
    # Like & Scrap API (C06, C07)
    # ==================================================

    # [POST]
    # /community/posts/<post_id>/likes/
    # - 기능: 게시글 좋아요 토글
    # - 예시: /community/posts/1/likes/
    path(
        'posts/<int:post_id>/likes/',
        views.PostLikeView.as_view(),
        name='post-like'
    ),

    # [POST]
    # /community/posts/<post_id>/scrap/
    # - 기능: 게시글 스크랩 토글
    # - 예시: /community/posts/1/scrap/
    path(
        'posts/<int:post_id>/scrap/',
        views.PostScrapView.as_view(),
        name='post-scrap'
    ),
]
