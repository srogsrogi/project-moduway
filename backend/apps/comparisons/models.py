from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CourseAIReview(models.Model):
    """
    LLM이 생성한 강좌 평가 데이터

    - 0.0 ~ 5.0 점수 체계 (FloatField 사용)
    - 0: 매우 낮음/쉬움/짧음
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

    # 평가 점수 (0.0 - 5.0) - 소수점 1자리(0.1f) 반영을 위해 FloatField 사용
    average_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="종합 평점 (0.0-5.0)"
    )

    theory_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="이론적 깊이 (0: 얕음, 5: 깊음)"
    )

    practical_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="실무적 활용도 (0: 낮음, 5: 높음)"
    )

    difficulty_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="학습 난이도 (0: 쉬움, 5: 어려움)"
    )

    duration_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="학습 기간 (0: 짧음, 5: 김)"
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