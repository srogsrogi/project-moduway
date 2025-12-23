# apps/comparisons/urls.py

"""
[설계 의도]
- Comparisons 앱의 URL 라우팅
- RESTful 설계 원칙 준수

[URL 패턴]

```
/api/v1/comparisons/
├── analyze/                              # POST: 강좌 비교 분석
└── courses/
    └── {course_id}/
        └── ai-review/                    # GET: 강좌 AI 평가 상세 조회
```

- /api/v1/comparisons/analyze/ - 강좌 비교 분석
- /api/v1/comparisons/courses/<int:course_id>/ai-review/ - AI 평가 조회
"""

from django.urls import path
from .views import (
    ComparisonAnalyzeView,
    CourseAIReviewDetailView,
    CourseReviewSummaryView
)

app_name = 'comparisons'

urlpatterns = [
    # 강좌 비교 분석
    path(
        'analyze/',
        ComparisonAnalyzeView.as_view(),
        name='comparison-analyze'
    ),

    # 강좌 AI 평가 조회
    path(
        'courses/<int:course_id>/ai-review/',
        CourseAIReviewDetailView.as_view(),
        name='course-ai-review-detail'
    ),

    # 강좌 리뷰 요약 조회
    path(
        'courses/<int:course_id>/review-summary/',
        CourseReviewSummaryView.as_view(),
        name='course-review-summary'
    ), 
]