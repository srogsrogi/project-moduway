from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CourseAIReview(models.Model):
    """
    LLM이 생성한 강좌 평가 데이터

    - Rating 점수: 1 ~ 5 정수 (IntegerField)
    - Average 점수: 1.0 ~ 5.0 실수 (FloatField, 둘째 자리 반올림)
    - 1: 매우 낮음/쉬움/짧음
    - 5: 매우 높음/어려움/김
    """

    course = models.OneToOneField(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='ai_review',
        help_text="평가 대상 강좌"
    )

    # LLM 생성 요약 (CharField로 변경하여 길이 제한 명시)
    course_summary = models.CharField(
        max_length=1000,  # 한글 기준 3문장 내외(공백 포함 약 200~300자) 고려
        blank=True,
        help_text="LLM이 생성한 강좌 요약 (2-3문장 제한)"
    )

    # 평가 점수 - 4개 항목 평균 (1.0 - 5.0, 둘째 자리 반올림)
    average_rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="종합 평점 (1.0-5.0)"
    )

    # 개별 평가 점수 (1 - 5 정수)
    theory_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="이론적 깊이 (1: 매우 기초적, 5: 고급)"
    )

    practical_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="실무적 활용도 (1: 이론 중심, 5: 프로젝트 중심)"
    )

    difficulty_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="학습 난이도 (1: 입문자용, 5: 고급)"
    )

    duration_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="학습 기간 (1: 1-4주, 5: 17주 이상)"
    )

    # 메타데이터 및 추적
    model_version = models.CharField(
        max_length=50,
        default='gpt-4o-mini',
        help_text="사용된 LLM 모델 버전"
    )
    
    prompt_version = models.CharField(
        max_length=20,
        default='v1.0.0',
        help_text="사용된 프롬프트 템플릿 버전"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_ai_review'
        verbose_name = '강좌 AI 평가'
        verbose_name_plural = '강좌 AI 평가 목록'
        indexes = [
            models.Index(fields=['average_rating']),
            models.Index(fields=['theory_rating']),
            models.Index(fields=['practical_rating']),
        ]

    def __str__(self):
        return f"{self.course.name} ({self.average_rating})"