from rest_framework import serializers
# Django ORM의 집계 / 필터링 도구
# - Count: annotate()에서 개수 집계할 때 사용
# - Q: AND/OR/NOT 같은 복합 조건 필터링할 때 사용
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

# community
from apps.community.models import Post, Comment, Scrap
from apps.community.serializers import UserSerializer, PostListSerializer
# accounts
from apps.accounts.models import UserConsent
# courses
from apps.courses.models import Course, Enrollment, Wishlist, CourseReview

User = get_user_model() # 커스텀 유저 모델 가져오기

# 개요
"""
1. 대시보드
  - 1. DashboardStatsSerializer | 학습 현황 요약

2. 학습현황
  - 1. SimpleCourseSerializer           | 간단한 강좌 정보
  - 2. EnrollmentListSerializer          | 수강 목록
  - 3. EnrollmentDetailSerializer       | 수강 상세 정보
  - 4. CourseReviewSerializer           | 수강평
  - 5. WishlistSerializer               | 위시리스트

3. 커뮤니티
  - 1. CommunityStatsSerializer | 커뮤니티 활동 통계
  - 2. MyPostSerializer         | 내가 쓴 글 목록
  - 3. MyCommentSerializer      | 내가 쓴 댓글 목록
  - 4. MyScrapSerializer        | 내가 스크랩한 게시글 목록

4. 내 계정
 - 1. ProfileSerializer        | 내 정보 조회/수정

참고:
- 관심분야 설정 탭은 MVP 범위 제외로 이번 구현에 포함하지 않음 (추후 구현 예정)
"""


# =========================
# 1. 대시보드
#   - 1. DashboardStatsSerializer         | 학습 현황 요약
# =========================
class DashboardStatsSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 마이페이지 최상단 대시보드의 통계 데이터 제공
    - View에서 집계한 데이터를 구조화하여 반환

    [상세 고려 사항]
    - 모델에 직접 매핑되지 않는 집계 데이터이므로 Serializer 사용
    - 각 필드는 read_only로 View에서 계산된 값만 반환
    """
    # view에서 집계한 값을 필드로 정의
    # read_only : 입력으로는 받지 않고, 출력으로만 사용
    enrolled_count = serializers.IntegerField(read_only=True) # 수강 중인 강좌 수
    completed_count = serializers.IntegerField(read_only=True) # 완료한 강좌 수
    wishlist_count = serializers.IntegerField(read_only=True) # 찜한 강좌 수
    my_review_count = serializers.IntegerField(read_only=True) # 작성한 리뷰 수



# =========================
# 2. 학습현황
#   - 1. SimpleCourseSerializer           | 간단한 강좌 정보
#   - 2. EnrollmentListSerializer         | 수강 목록
#   - 3. EnrollmentDetailSerializer       | 수강 상세 정보
#   - 4. CourseReviewSerializer           | 수강평
#   - 5. WishlistSerializer               | 위시리스트
# =========================


# 2.1 SimpleCourseSerializer
class SimpleCourseSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 목록, 찜한 강좌, 수강 중인 강좌, 마이페이지 등에서
    '강좌카드` 형태로 재사용되는 간단한 강좌 정보 제공
    - 불필요한 필드는 제거해서 Payload 최소화 및 성능 최적화

    [상세 고려 사항]
    - 강좌의 핵심 정보만 선별적으로 제공 -> UI 기준으로!
    - 중첩 사용 시 N+1 문제 방지를 위해 필드 최소화
    """
    class Meta:
        model = Course
        fields = (
            'id',                 # 강좌 고유 ID (식별자)
            'name',               # 강좌명
            'professor',          # 교수/강사명
            'org_name',           # 운영 기관명 (ex. 대학, 플랫폼)
            'course_image',       # 강좌 썸네일 이미지 URL
            'enrollment_start',   # 수강신청 시작일
            'enrollment_end',     # 수강신청 종료일
            'study_start',        # 학습 시작일
            'study_end',          # 학습 종료일
            'week',               # 총 학습 주차 수
            'course_playtime'     # 총 강의 재생 시간
        )
        read_only_fields = fields # 조회 전용



# 2.2 EnrollmentListSerializer
class EnrollmentListSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 마이페이지 / 수강 목록 화면에서 사용
    - 사용자가 '어떤 강좌를 어떤 상태로 수강 중인지' 한 번에 보여주기 위함
    - Enrollment(수강 메타데이터) + Course(강좌 정보)를 함께 제공

    [상세 고려 사항]
    - course 필드를 SimpleCourseSerializer로 중첩하여 강좌 상세 포함
        - course 필드는 FK이지만, 단순 ID가 아니라
          강좌 카드 렌더링에 필요한 정보가 필요하므로 중첩 Serializer 사용
    - progress_rate는 DB에서는 DecimalField지만,
      API 응답(JSON)에서는 float 형태로 직렬화됨
    """
    course = SimpleCourseSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            'id',               # 수강(Enrollment) 레코드 고유 ID
            'course',           # 중첩된 강좌 정보 (SimpleCourseSerializer 결과)
            'status',           # 수강 상태 (예: ENROLLED / COMPLETED / DROPPED)
            'progress_rate',    # 학습 진도율 (0~100)
            'last_studied_at',  # 마지막 학습 시각
            'enrolled_at'       # 수강 등록 시각
        )
        read_only_fields = fields # 조회 전용



# 2.3 EnrollmentDetailSerializer
class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 특정 강좌의 "수강 상세 정보" 제공
    - 강좌의 모든 정보 + 사용자의 수강 상태/진도/시점 등 메타데이터를 한 번에 반환

    [상세 고려 사항]
    - Course 전체 필드를 중첩으로 포함
      - 프론트에서 추가 API 호출 없이 렌더링 가능하도록
    - 이어듣기 URL은 course.url 필드 활용
    """

    # Enrollment 모델의 course(ForeignKey)를
    # SimpleCourseSerializer로 중첩 직렬화
    #
    # 의미:
    # - Enrollment 객체 1개를 JSON으로 변환할 때
    #   course_id 숫자 대신
    #   강좌 카드 렌더링에 필요한 핵심 정보 묶음을 함께 반환
    course = SimpleCourseSerializer(read_only=True)

    # 강좌 이어듣기 링크
    # course 모델의 url 필드를 참조
    # Enrollement 모델에는 url 필드가 없으므로
    # source 옵션을 통해 related 객체의 url 필드를 참조

    # source='course.url' 동작 방식:
    # - serializer가 enrollment.course.url 값을 읽어서
    #   continue_url이라는 이름으로 응답에 포함

    # URLField:
    # - 문자열이지만 URL 형식 검증을 포함한 Field
    continue_url = serializers.URLField(source='course.url', read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            'id',               # Enrollment 레코드 ID
            'course',           # 중첩된 강좌 정보
            'status',           # 수강 상태
            'progress_rate',    # 진도율
            'last_studied_at',  # 마지막 학습 시점
            'enrolled_at',      # 수강 시작 시점
            'created_at',       # 레코드 생성 시각
            'updated_at',       # 레코드 수정 시각
            'continue_url'      # 이어듣기 링크 (course.url)
        )
        read_only_fields = fields # 상세 조회 전용



# 2.4 CourseReviewSerializer
class CourseReviewSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 수강평(CourseReview)의
      등록(Create), 수정(Update), 조회(Read)를 담당하는 Serializer

    [상세 고려 사항]
    - rating 범위 검증 (1~5) 필요 → validate_rating() 메서드 활용
    - review_text 필수 + 100자 이상 강제 → 필드 옵션 + validate_review_text() 활용
    - user, course는 보안/무결성 이슈 방지를 위해
      클라이언트 입력이 아닌 View에서 강제로 주입
    """
    # review_text를 "필수"로 강제하기 위한 필드 재정의
    # - ModelSerializer는 기본적으로 Model의 필드 설정(blank 등)을 참고하지만,
    #   API 스펙 수준에서 "반드시 입력"을 더 강하게 보장하고 싶다면
    #   Serializer 필드를 명시적으로 재정의하는 것이 가장 확실하기에, 여기서 재정의함.
    #   #NOTE: 추천 로직에서 리뷰 텍스트가 반드시 필요하기 때문임!
    #
    # required=True:
    # - 요청 body에 review_text 키가 반드시 존재해야 함
    #
    # allow_blank=False:
    # - review_text="" (빈 문자열) 허용하지 않음
    #
    # trim_whitespace=True:
    # - "   ....   " 같은 입력은 앞뒤 공백을 제거한 후 검증(길이 검사)하게 됨
    review_text = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        error_messages={
            # review_text 자체가 누락된 경우
            "required": "리뷰를 작성해주세요.",
            # review_text가 "" 이거나 공백만 있는 형태로 들어온 경우
            "blank": "리뷰를 작성해주세요.",
            "null": "리뷰를 작성해주세요.",
        }
    )

    class Meta:
        model = CourseReview
        fields = (
            'id',           # 수강평 고유 ID (식별자)
            'rating',       # 평점 (1~5)
            'review_text',  # 후기 내용 (필수, 최소 100자)
            'created_at',   # 생성 시각
            'updated_at'    # 수정 시각
        )
        read_only_fields = (
            'id',                      # DB에서 자동으로 관리
            'created_at', 'updated_at' # 서버에서 자동 관리
        )

    # 평점 범위를 검증하는 메서드
    def validate_rating(self, value):
        """
        평점 범위 검증 (1~5)

        DRF 동작 흐름:
        1. serializer.is_valid() 호출
        2. rating 값이 존재하면
        3. validate_rating(value) 자동 호출
        4. ValidationError 발생 시 is_valid() = False
        """
        if not (1 <= value <= 5):
            # validation error 발생 시
            # DRF는 자동으로 400 Bad Request 응답 생성
            raise serializers.ValidationError("평점은 1~5 사이여야 합니다.")
        
        # 정상 범위인 경우
        return value
    
    # 후기 내용 길이를 검증하는 메서드
    def validate_review_text(self, value):
        """
        review_text 검증 (필수 + 100자 이상)

        DRF 동작 흐름:
        1. serializer.is_valid() 호출
        2. review_text 값이 존재하면
        3. validate_review_text(value) 자동 호출
        4. ValidationError 발생 시 is_valid() = False

        [검증 포인트]
        - 공백만 입력되는 경우를 막기 위해 strip() 후 길이를 검사
        - 100자 미만이면 사용자에게 명확한 에러 메시지 반환
        """
        text = value.strip()

        # 100자 이상 강제
        if len(text) < 100:
            raise serializers.ValidationError("리뷰는 100자 이상 작성해주세요.")

        return text


# 2.5 WishlistSerializer
class WishlistSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 위시리스트 조회 시 강좌 정보를 함께 제공
    - 사용자가 위시리스트(찜 목록)을 확인할 때
        단순히 course_id만 있는 것보다
        강좌명, 기간, 썸네일 등 강좌 카드 렌더링에 필요한 핵심 정보를 함께 보여주기 위함

    [상세 고려 사항]
    - course를 SimpleCourseSerializer로 중첩하여
        프론트에서 추가 API 호출 없이 강좌 정보 렌더링 가능
    - Community앱의 ScrapSerializer와 동일한 설계 패턴을 사용함
    """
    course = SimpleCourseSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = (
            'id',          # Wishlist 레코드 고유 ID
            'course',      # 중첩된 강좌 정보 (SimpleCourseSerializer 결과)
            'created_at'   # 위시리스트에 추가된 시각
        )
        read_only_fields = (
            'id',          # DB에서 자동 생성
            'created_at'   # 서버에서 자동 기록
        )



# =========================
# 3. 커뮤니티
#   - 1. CommunityStatsSerializer         | 커뮤니티 활동 통계
#   - 2. MyPostSerializer                 | 내가 쓴 글 목록
#   - 3. MyCommentSerializer              | 내가 쓴 댓글 목록
#   - 4. MyScrapSerializer                | 내가 스크랩한 게시글 목록
# =========================


# 3.1 CommunityStatsSerializer
class CommunityStatsSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 마이페이지 커뮤니티 탭에서
        커뮤니티 활동 통계 데이터 제공을 위함
    - View에서 집계한 데이터를 구조화
        게시글/댓글/스크랩/받은 좋아요 수를 한 번에 반환

    [상세 고려 사항]
    - 단일 모델에 대응되지 않는 집계 데이터이므로 
      ModelSerializer가 아닌 Serializer 사용
    - received_likes_count는 내가 쓴 글(댓글 미포함)이 받은 좋아요 총합
    - 각 필드는 read_only로 View에서 계산된 값만 반환
    """
    post_count = serializers.IntegerField(read_only=True) # 내가 쓴 게시글 수
    comment_count = serializers.IntegerField(read_only=True) # 내가 쓴 댓글 수
    scrap_count = serializers.IntegerField(read_only=True) # 내가 스크랩한 게시글 수
    # 의미 정의:
    # - 내가 작성한 Post에 달린 좋아요의 총합
    # - Comment에 달린 좋아요는 포함하지 않음
    #
    # View 예시 로직:
    # PostLike.objects.filter(post__author=user).count()
    #
    # 설계 의도:
    # - "콘텐츠 생산자로서의 영향력"을 직관적으로 보여주기 위함
    # - 댓글 좋아요까지 포함할 경우 지표의 의미가 모호해질 수 있어 제외
    received_likes_count = serializers.IntegerField(read_only=True) # 내가 쓴 글이 받은 좋아요 총합



# 3.2 MyPostSerializer
class MyPostSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 마이페이지에서 "내가 작성한 글 목록"을 조회하기 위한 전용 Serializer
    - PostListSerializer와 유사하지만 마이페이지 UX에 맞춰 필요한 정보만 선별하여 제공.

    [상세 고려 사항]
    - board객체 전체를 중첩하지 않고,
      board_name만 문자열로 제공하여 응답 payload 최소화
    - likes_count, comments_count는
      View의 annotate로 미리 계산해서 그 값을 그대로 제공
    """
    # 마이페이지에서도 작성자 정보 UI가 필요한 경우 재사용
    author = UserSerializer(read_only=True) # 작성자 정보
    # board 객체 전체를 중첩하지 않고,
    # board.name 값만 추출해서 board_name이라는 별도의 필드로 제공함!
    # source = 'board.name' 동작 방식:
    # - serializer가 post.board.name 값을 읽어서
    #   board_name이라는 이름으로 응답에 포함
    # 설계 의도:
    # - 마이페이지에서는 게시판 전체 정보보다 이름만 있으면 충분함
    # - 응답 payload를 최소화하여 성능 최적화
    board_name = serializers.CharField(source='board.name', read_only=True) # 게시판 이름
    likes_count = serializers.IntegerField(read_only=True) # 좋아요 수
    comments_count = serializers.IntegerField(read_only=True) # 댓글 수

    class Meta:
        model = Post
        fields = (
            'id',              # 게시글 ID
            'author',          # 작성자 정보
            'board_name',      # 게시판 이름 (문자열)
            'title',           # 게시글 제목
            'created_at',      # 작성일
            'updated_at',      # 수정일
            'likes_count',     # 좋아요 수 (annotate 결과)
            'comments_count'   # 댓글 수 (annotate 결과)
        )
        read_only_fields = fields\
        


# 3.3 MyCommentSerializer | 내가 쓴 댓글 목록 조회
class MyCommentSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 마이페이지에서 "내가 작성한 댓글 목록"을 조회하기 위한 전용 Serializer
    - 댓글 자체 정보뿐만 아니라, 댓글이 달린 게시글의
      핵심 정보도 함께 제공하여 문맥 파악에 도움을 줌

    [상세 고려 사항]
    - post 전체를 중첩 Serializer로 포함하지 않고,
      필요한 필드만 source 옵션으로 직접 참조하여 payload 최소화
    - post_id는 원문 게시글 상세 페이지로 이동하기 위한 링크 생성용
    """
    # comment.author(FK)를 
    # UserSerializer로 중첩 직렬화
    # 의미:
    # - 댓글 객체 1개를 JSON으로 변환할 때
    #   author 필드에 작성자 정보 묶음을 함께 반환
    # 의도:
    # - 마이페이지에서 내가 쓴 댓글 목록을 볼 때
    #   댓글 작성자 정보도 함께 보여주기 위함
    #   마이페이지에서는 항상 "나"지만,
    #   구조적 일관성과 확장성(관리자/공유페이지 등)을 고려해 재사용
    author = UserSerializer(read_only=True) # 댓글 작성자 정보

    # Comment 모델의 post(FK)에서
    # 필요한 필드만 직접 참조하여 별도의 필드로 제공
    # Comment → Post(FK) → id
    #
    # source='post.id':
    # - serializer가 comment.post.id 값을 읽어서
    #   post_id 필드로 응답에 포함
    #
    # 사용 목적:
    # - 프론트엔드에서
    #   /posts/{post_id}/ 형태의 링크 생성용
    post_id = serializers.IntegerField(source='post.id', read_only=True) # 원문 게시글 id
    # Comment → Post(FK) → title
    # source='post.title':
    # - serializer가 comment.post.title 값을 읽어서
    #   post_title 필드로 응답에 포함
    #
    # 사용 목적:
    # - 마이페이지에서 내가 쓴 댓글이
    #   어떤 게시글에 달린 댓글인지 문맥 파악용
    # 중첩 Serializer 대신
    # 문자열만 추출하여 payload 최소화
    post_title = serializers.CharField(source='post.title', read_only=True) # 원문 게시글 제목
    # Comment → Post → Board → name
    post_board_name = serializers.CharField(source='post.board.name', read_only=True) # 원문 게시글 게시판 이름

    class Meta:
        model = Comment
        fields = (
            'id',                # 댓글 ID
            'author',            # 작성자 정보
            'content',           # 댓글 내용
            'created_at',        # 생성 시각
            'updated_at',        # 수정 시각
            'post_id',           # 원문 게시글 ID
            'post_title',        # 원문 게시글 제목
            'post_board_name'    # 원문 게시글 게시판 이름
        )
        read_only_fields = fields



# 3.4 MyScrapSerializer | 내가 스크랩한 게시글 목록 조회
class MyScrapSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 마이페이지에서 "내가 스크랩한 게시글 목록"을 조회하기 위한 전용 Serializer
    - 기존 ScrapSerializer 활용하되 필요 정보 추가
        - Scrap(스크랩 메타데이터) + Post(게시글 정보)를 함께 제공

    [상세 고려 사항]
    - post를 PostListSerializer로 중첩하여 게시글 카드 렌더링에 필요한 정보만 포함
    - 기존 community.serializers.ScrapSerializer와 동일 패턴으로 작성.
    """

    # 스크랩한 게시글 정보를
    # PostListSerializer로 중첩 직렬화
    # 의미:
    # - Scrap 객체 1개를 JSON으로 변환할 때
    #   post_id 숫자만 내려주는 대신
    #   게시글 제목, 작성자, 좋아요 수 등
    #   "게시글 카드"에 필요한 정보를 함께 반환
    # 의도:
    # - 마이페이지에서 내가 스크랩한 게시글 목록을 볼 때
    #   게시글 카드 형태로 렌더링하기 위함
    post = PostListSerializer(read_only=True)

    class Meta:
        model = Scrap
        fields = (
            'id',          # Scrap 레코드 ID
            'post',        # 중첩된 게시글 정보 (PostListSerializer 결과)
            'created_at'   # 스크랩한 시각
        )
        read_only_fields = fields # 조회 전용



# =========================
# 4. 프로필 관련 Serializer
#   - 1. ProfileSerializer        | 내 정보 조회/수정
# =========================


# 4.1 ProfileSerializer
class ProfileSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 마이페이지에서 "내 프로필" 정보 조회 및 수정에 사용하는 Serializer
    - User 테이블의 기본 프로필 필드 + UserConsent의 마케팅 동의 상태를 함께 제공

    [상세 고려 사항]
    - marketing_opt_in은 UserConsent에서 가져와야 함 → SerializerMethodField 활용
    - email 수정 시 중복 검증 필요
    - 비밀번호 변경은 보안상 별도 API(PasswordChange 등)로 분리하는 것이 원칙이므로 제외
    """
    # SerializerMethodField:
    # - 모델 필드가 아닌 값을 응답에 포함시키고 싶을 때 사용
    # - get_<필드명>(obj) 메서드를 구현하면 그 반환값이 응답에 들어감
    # - UserConsent 모델에서 marketing_opt_in 값을 조회하여 반환

    # 즉, model을 User로 지정했지만,
    # marketing_opt_in 필드는 User 모델에 없고
    # UserConsent 모델에서 확인할 수 있으니까
    # SerializerMethodField를 사용해야한다는 것!!
    # 
    # User
    #  └─ 1:1
    #     UserConsent
    #       └─ marketing_opt_in
    marketing_opt_in = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',              # 사용자 식별자 (DB PK)
            'username',        # 로그인 ID/유저네임 (보통 변경 불가)
            'name',            # 사용자 실명/표시명 (수정 가능)
            'email',           # 이메일 (수정 가능, 중복 검증 필요)
            'date_joined',     # 가입일(서버 기록, 변경 불가)
            'marketing_opt_in' # 마케팅 수신 동의 여부(UserConsent에서 조회)
        )
        read_only_fields = ('id', 'username', 'date_joined')


    # marketing_opt_in 필드 값을 반환하는 메서드
    def get_marketing_opt_in(self, obj):
        """
        [설계 의도]
        - UserConsent에서 marketing_opt_in 값을 조회해서 응답에 포함해야됨

        [상세 고려 사항]
        `backend/apps/accounts/models.py` 에 related_name="consent"로 설정되어 있음
        - 동의 레코드(UserConsent)가 아직 생성되지 않았을 수 있으므로 예외 처리 필요 (구글 로그인 등등...)
        - consent가 없으면 기본값 False로 반환
        """
        try:
            # 동의 레코드가 있다면
            return obj.consent.marketing_opt_in
        except UserConsent.DoesNotExist:
            # 없다면 기본값은 False
            return False

    # 이메일 중복 검증 메서드
    def validate_email(self, value):
        """
        [설계 의도]
        - 프로필 수정 시 이메일 중복 체크

        [상세 고려 사항]
        - "내가 사용하는 이메일"은 제외하고 중복 검사해야하므로
          현재 사용자(=self.instance)는 제외하고 필터링
        """
        # self.instance:
        # - update 상황에서 serializer가 들고 있는 "기존 User 객체"
        user = self.instance
        # User 테이블에서 동일 email이 존재하는지 확인하되,
        # 현재 사용자(user.pk)는 제외
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            # 중복이면 ValidationError → DRF가 400 응답으로 변환
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        # 문제 없으면 그대로 반환 → validated_data['email']에 반영됨
        return value

    def update(self, instance, validated_data):
        """
        [설계 의도]
        - PATCH/PUT로 들어온 프로필 수정 요청을 반영하고 싶은데,
        - #TODO 프로필 수정 시 UserConsent도 함께 업데이트하게끔 하려면 별도의 로직이 필요하다.

        [상세 고려 사항]
        - 현재 구현은 User의 email, name만 업데이트
        - marketing_opt_in은 SerializerMethodField라서 validated_data에 들어오지 않음
        - 입력받고 저장하고 싶다면, 두 가지 정도 방법이 있을 것 같다.
        1) Serializer에 write 가능한 필드를 따로 둔다.
        2) View에서 request.data['marketing_opt_in']을 읽어서 UserConsent를 갱신한다.
        """
        # validated_data에서 email 값이 오면 갱신, 없으면 기존 값 유지
        instance.email = validated_data.get('email', instance.email)
        # validated_data에서 name 값이 오면 갱신, 없으면 기존 값 유지
        instance.name = validated_data.get('name', instance.name)
        # 변경사항 DB 반영
        instance.save()

        # marketing_opt_in 업데이트 (request.data에서 추출 필요)
        # View에서 처리하는 것이 더 명확할 수 있음

        return instance
    


