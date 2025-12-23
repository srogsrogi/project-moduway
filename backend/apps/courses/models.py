from django.db import models
from pgvector.django import VectorField 

class Course(models.Model):
    # K-MOOC 원본 데이터의 식별자 (CSV의 id 컬럼)
    kmooc_id = models.CharField(max_length=50, unique=True)
    
    # 강좌 기본 정보
    name = models.CharField(max_length=500)  # 강좌명
    content_key = models.CharField(max_length=500, blank=True, null=True)
    professor = models.CharField(max_length=500, blank=True, null=True)  # 교수자
    org_name = models.CharField(max_length=100, blank=True, null=True)   # 운영기관(대학 등)
    certificate_yn = models.CharField(max_length=1, blank=True, null=True) # 수료증 발급 여부
    
    # 분류
    classfy_name = models.CharField(max_length=100, blank=True, null=True)        # 대분류
    middle_classfy_name = models.CharField(max_length=100, blank=True, null=True) # 중분류
    
    # 상세 정보
    summary = models.TextField("강좌 요약/소개", blank=True, null=True)
    raw_summary = models.TextField("강좌 소개(HTML 원본)", blank=True, null=True) # HTML 포함 원본
    course_image = models.URLField("강좌 썸네일", max_length=500, blank=True, null=True)
    url = models.URLField("강좌 URL", max_length=500, blank=True, null=True)
    
    # 일정 정보 (NULL 허용)
    enrollment_start = models.DateField(blank=True, null=True) # 수강신청 시작일
    enrollment_end = models.DateField(blank=True, null=True)   # 수강신청 종료일
    study_start = models.DateField(blank=True, null=True)      # 수강 시작일
    study_end = models.DateField(blank=True, null=True)        # 수강 종료일
    
    # 기타 메타데이터
    week = models.FloatField(blank=True, null=True)            # 주차 수
    course_playtime = models.FloatField(blank=True, null=True) # 총 재생 시간 (분 단위 등)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 1536차원 벡터 필드 (임베딩 저장용, openai text-embedding-3-small 모델 사용 예정)
    embedding = VectorField(dimensions=1536, blank=True, null=True)



    def __str__(self):
        return self.name

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        #TODO 3. 벡터 검색 최적화를 위한 인덱스 추가(데이터 적재 완료 후 테스트 및 활성화 검토)
        # indexes = [
        #     models.Index(fields=['embedding'], name='course_embedding_idx'),
        # ]


# merge 충돌을 피하기 위해 import 임시 위치 변경 #TEMP
from django.conf import settings


class Enrollment(models.Model):
    """
    [설계의도]
    - 사용자(User)가 특정 강좌(Course)를 "수강중/완료/수강취소" 등 상태로 관리하기 위한 테이블
    - 진도율(progress_rate), 마지막 학습 시점(last_studied_at) 등
      '사용자-강좌' 관계에서만 의미가 있는 학습 메타데이터를 저장

    [상세고려사항]
    - User ↔ Course는 논리적으로 N:M 관계이지만,
      status/progress/last_studied_at 같은 부가 컬럼이 필요하므로
      중간테이블(Enrollment)로 분리하여 관리
    - (user, course) 조합은 1개만 존재해야 하므로 UniqueConstraint 적용
    - progress_rate는 0~100 범위 사용을 전제로 DecimalField로 저장
      (정밀도/반올림 이슈를 줄이기 위해 float 대신 decimal 사용)
    """

    # 상태값을 "문자열 enum"처럼 쓰기 위한 Django 내장 도우미
    # - DB에는 enrolled/completed/dropped 같은 '값(value)'가 저장되고
    # - 관리자/폼 등 표시에는 "수강중/수강완료/수강취소" 같은 '라벨(label)'이 사용됨
    class Status(models.TextChoices):
        ENROLLED = "enrolled", "수강중" # DB 저장값: enrolled, 사람이 보는 라벨: 수강중
        COMPLETED = "completed", "수강완료" # DB 저장값: completed, 사람이 보는 라벨: 수강완료
        DROPPED = "dropped", "수강취소" # DB 저장값: dropped, 사람이 보는 라벨: 수강취소

    # FK: Enrollment.user -> 사용자 테이블(커스텀 유저 포함)
    # on_delete=models.CASCADE:
    #   - 사용자가 삭제되면, 그 사용자의 수강(Enrollment) 기록도 같이 삭제됨(참조 무결성 유지)
    # related_name="enrollments":
    #   - User 인스턴스에서 user.enrollments 로 역참조 가능
    # help_text:
    #   - Admin/DRF 스키마/문서화에서 필드 설명으로 활용됨
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        help_text="수강 사용자"
    )

    # FK: Enrollment.course -> courses 앱의 Course 모델
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
        help_text="수강 강좌"
    )


    # 수강 상태를 저장하는 문자열 필드
    # choices=Status.choices:
    #   - 위 TextChoices에서 정의한 값만 허용(폼/어드민에서 드롭다운으로 표시)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED,
        help_text="수강 상태 (enrolled/completed/dropped)"
    )

    # 진도율을 %로 저장(예: 0.00 ~ 100.00)
    # DecimalField를 쓰는 이유:
    #   - float(부동소수점)은 0.1 같은 값이 정확히 표현되지 않아 반올림/비교에서 오차가 생길 수 있음
    # max_digits=5, decimal_places=2:
    #   - 전체 자리수 5, 소수점 2자리 -> 100.00(= 5자리)까지 표현 가능
    progress_rate = models.DecimalField(
        max_digits=5,        # 100.00 까지 표현 가능
        decimal_places=2,
        default=0,
        help_text="진도율(%) - 0~100 범위"
    )

    # 마지막 학습 시점
    last_studied_at = models.DateTimeField(
        null=True, # 아직 학습 기록이 없으면 값이 없을 수 있음. 
        blank=True,
        help_text="마지막 학습 시점"
    )

    # 수강 신청 시점 (외부 이벤트 시각 보존용)
    enrolled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="수강 신청 시점(외부 이벤트 시각 보존용)"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="레코드 생성 시각")
    updated_at = models.DateTimeField(auto_now=True, help_text="레코드 수정 시각")


    # 모델의 메타데이터(테이블 이름, 정렬, 제약조건 등) 설정
    class Meta:
        db_table = "enrollment"
        verbose_name = "수강"
        verbose_name_plural = "수강 목록"
        ordering = ["-created_at"]
        constraints = [
            # (user, course) 조합이 유일해야 함
            # -> 같은 사용자가 같은 강좌를 중복 수강 레코드로 만들지 못하게 막음
            models.UniqueConstraint(fields=["user", "course"], name="uq_enrollment_user_course"),
        ]

    # Django에서 객체를 문자열로 표현할 때(관리자, shell 등) 보여줄 형태
    def __str__(self):
        # f-string으로 "유저 enrolls 강좌 (상태)" 형태로 출력
        return f"{self.user} enrolls {self.course} ({self.status})"


class Wishlist(models.Model):
    """
    [설계의도]
    - 사용자가 관심 있는 강좌를 '찜'으로 저장하는 기능
    - 강좌 추천/재방문/개인화 UX를 위한 최소 단위 데이터

    [상세고려사항]
    - User ↔ Course 간 N:M 관계를 Wishlist 조인 테이블로 분리
      (created_at으로 찜한 시점/정렬 제공)
    - (user, course) 중복 찜을 방지하기 위해 UniqueConstraint 적용
    - 향후 메모, 폴더, 태그 등 확장 가능성을 고려해 별도 테이블로 유지
    """

    # 찜을 누른 사용자
    # related_name="wishlists" -> user.wishlists 로 접근
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
        help_text="찜한 사용자"
    )

    # 찜된 강좌
    # related_name="wishlists" -> course.wishlists 로 접근
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="wishlists",
        help_text="찜된 강좌"
    )

    # 찜한 시각
    created_at = models.DateTimeField(auto_now_add=True, help_text="찜한 시각")

    class Meta:
        db_table = "wishlist"
        verbose_name = "찜"
        verbose_name_plural = "찜 목록"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="uq_wishlist_user_course"),
        ]

    def __str__(self):
        return f"{self.user} wishes {self.course}"


class CourseReview(models.Model):
    """
    [설계의도]
    - 사용자(User)가 강좌(Course)에 대해 평점/리뷰를 남기는 기능
    - 강좌 품질 지표, 추천 로직(평점 기반), 사용자 피드백 수집에 활용

    [상세고려사항]
    - (user, course) 당 리뷰는 1개만 허용하는 정책을 기본값으로 가정하여
      UniqueConstraint 적용 (필요 시 정책 변경 가능)
    - rating은 정수형 점수(예: 1~5)를 전제로 PositiveSmallIntegerField 사용
      (검증은 Serializer/Model clean 또는 validators로 강화 가능)
    - review_text는 선택 입력 가능(평점만 남기는 UX 허용)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_reviews",
        help_text="리뷰 작성자"
    )

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="리뷰 대상 강좌"
    )

    rating = models.PositiveSmallIntegerField(
        help_text="평점 (예: 1~5)"
    )

    review_text = models.TextField(
        help_text="리뷰 내용"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="리뷰 생성 시각")
    updated_at = models.DateTimeField(auto_now=True, help_text="리뷰 수정 시각")

    class Meta:
        db_table = "course_review"
        verbose_name = "강좌 리뷰"
        verbose_name_plural = "강좌 리뷰 목록"
        ordering = ["-created_at"]
        constraints = [
            # 한 사용자당 한 강좌에 리뷰 1개만 허용(정책)
            models.UniqueConstraint(fields=["user", "course"], name="uq_course_review_user_course"),
        ]

    def __str__(self):
        return f"{self.user} reviews {self.course} ({self.rating})"
