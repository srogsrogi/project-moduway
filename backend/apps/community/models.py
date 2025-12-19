# backend/apps/community/models.py

from django.db import models
from django.conf import settings

# Create your models here.
class Board(models.Model):
    """
    [설계의도]
    - 커뮤니티 내 게시글을 주제/용도별로 구분하기 위한 최상위 분류 단위
    - 게시글(Post)이 반드시 하나의 게시판(Board)에 속하도록 강제

    [상세고려사항]
    - name은 URL 및 조회 기준으로 사용되므로 unique 제약 적용
    - description은 UI 표시용이므로 선택 입력 허용
    """
    name = models.CharField(max_length=50, unique=True, help_text="게시판 이름 (예: 자유게시판)")
    description = models.CharField(max_length=150, blank=True, help_text="게시판 설명")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_board'
        verbose_name = '게시판'
        verbose_name_plural = '게시판 목록'

    def __str__(self):
        return self.name


class Post(models.Model):
    """
    [설계의도]
    - 커뮤니티의 핵심 콘텐츠 단위
    - 작성자, 게시판, 좋아요, 댓글과의 관계를 중심으로 설계

    [상세고려사항]
    - Article 모델을 확장/대체하는 개념
    - 좋아요는 단순 관계이므로 별도 테이블 없이 M:N 관계 사용
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="작성자"
    )
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="게시판"
    )
    title = models.CharField(max_length=200, help_text="게시글 제목")
    content = models.TextField(help_text="게시글 내용")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # [설계의도] 좋아요 기능을 위한 사용자-게시글 M:N 관계
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='PostLike', # through 옵션을 사용하여 중개 모델(PostLike)을 지정, 이것이 있어야 좋아요 누른 시점을 기록 가능
        related_name='liked_posts',
        blank=True,
        help_text="좋아요한 사용자"
    )

    class Meta:
        db_table = 'community_post'
        verbose_name = '게시글'
        verbose_name_plural = '게시글 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.board.name}] {self.title}"

    @property
    def get_likes_count(self):
        """
        [설계의도]
        - annotate와 충돌을 피하기 위해 메서드 이름 변경
        - serializer/관리자 화면에서 좋아요 수를 직관적으로 제공
        """
        return self.likes.count()

    @property
    def get_comments_count(self):
        """
        [설계의도]
        - 최상위 댓글 기준으로 댓글 수 계산
        [상세고려사항]
        - 대댓글은 UI에서 하위로 묶이므로 제외
        - annotate와 충돌을 피하기 위해 메서드 이름 변경
        """
        return self.comments.filter(parent=None).count()


class Comment(models.Model):
    """
    [설계의도]
    - 게시글에 대한 사용자 반응을 표현하는 모델
    - 대댓글 구조를 허용하여 토론 흐름을 유지

    [상세고려사항]
    - parent를 self-FK로 두어 무한 depth 확장 가능
    - 기본 조회는 parent=None 기준으로 설계
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="댓글 작성자"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="게시글"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="부모 댓글 (대댓글인 경우)"
    )
    content = models.TextField(help_text="댓글 내용")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community_comment'
        verbose_name = '댓글'
        verbose_name_plural = '댓글 목록'
        ordering = ['created_at']

    def __str__(self):
        if self.parent:
            return f'대댓글 by {self.author.username} on {self.post.title}'
        return f'댓글 by {self.author.username} on {self.post.title}'


class Scrap(models.Model):
    """
    [설계의도]
    - 사용자가 다시 보고 싶은 게시글을 저장하는 기능

    [상세고려사항]
    - 좋아요와 달리, 향후 메모/폴더 등 확장을 고려해 별도 테이블로 분리
    - unique Constraint로 중복 스크랩 방지
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='scraps',
        help_text="스크랩한 사용자"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='scraps',
        help_text="스크랩된 게시글"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_scrap'
        verbose_name = '스크랩'
        verbose_name_plural = '스크랩 목록'
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_user_post_scrap'
            )
        ]

    def __str__(self):
        return f'{self.user.username} scraps {self.post.title}'



class PostLike(models.Model):
    """
    [설계의도]
    - 게시글 좋아요 기능의 실체 테이블 (중개 모델)
    - 단순 M:N 관계 테이블과 달리 '좋아요를 누른 시점(created_at)'을 기록하기 위해 별도 모델로 정의

    [ 왜 필요한가? ]
    - 좋아요 누른 시점을 기록하여 활동 로그, 통계 등에 활용 가능
    - 기능 구현: '최근에 좋아요한 글 모아보기'나 알림에 정확한 시간을 표시하는 등 시점 기반의 UX를 제공하기 위해서
    - 서비스 확장: 단시간에 좋아요가 급등하는 '실시간 인기글' 알고리즘을 만들거나, 비정상적인 매크로 활동을 탐지하기 위해서
    
    [상세고려사항]
    - Post 모델의 likes 필드에서 through='PostLike' 옵션을 통해 사용됨
    - 한 사용자가 같은 글에 중복으로 좋아요를 누를 수 없도록 UniqueConstraint 적용
    """
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='post_likes',
        help_text="좋아요 대상 게시글"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
        help_text="좋아요를 누른 사용자"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="좋아요 누른 시간")

    class Meta:
        db_table = 'community_post_likes'
        verbose_name = '게시글 좋아요'
        verbose_name_plural = '게시글 좋아요 목록'
        ordering = ['-created_at']
        
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'], # fields: 유니크 조합을 체크할 필드 목록
                name='unique_user_post_like' # name: 데이터베이스 내에서 이 제약조건을 식별할 고유 이름 (필수)
            )
        ]

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"