from django.urls import path
from .views import (
    CourseDetailView,
    CourseReviewListView,
    CourseRecommendationView,
    CourseListView,
    CourseKeywordSearchView,
    CourseSemanticSearchView,
)

# 개요
"""
```
/api/v1/courses/
├── /                               # 강좌 목록
├── <int:pk>/                       # 강좌 상세
├── <int:course_id>/reviews/        # 리뷰 목록
└── <int:course_id>/recommendations/ # 추천 강좌
```

#### 강좌 목록 API
1. 쿼리 파라미터
| 파라미터              | 타입   | 설명                         | 예시                          |
| --------------------- | ------ | ---------------------------- | ----------------------------- |
| `search`              | string | 강좌명/소개 검색 (icontains) | `?search=파이썬`              |
| `classfy_name`        | string | 대분류 필터링                | `?classfy_name=인문`          |
| `middle_classfy_name` | string | 중분류 필터링                | `?middle_classfy_name=교육학` |
| `org_name`            | string | 운영기관 필터링              | `?org_name=서울대학교`        |
| `professor`           | string | 교수 필터링                  | `?professor=김교수`           |
| `ordering`            | string | 정렬 기준                    | `?ordering=-average_rating`   |
| `page`                | int    | 페이지 번호                  | `?page=2`                     |
| `page_size`           | int    | 페이지 크기                  | `?page_size=20`               |

2. Ordering 옵션

- `-average_rating`: 평점 높은순 **(기본값)**
- `average_rating`: 평점 낮은순
- `-created_at`: 최신순
- `created_at`: 오래된순
- `name`: 이름 오름차순
- `-name`: 이름 내림차순
- `-review_count`: 리뷰 많은순

"""

urlpatterns = [
    # 0. 강의 목록 조회: /api/v1/courses/
    path('', CourseListView.as_view(), name='course-list'),
    
    # 1. 강의 상세 정보 조회: /api/v1/courses/<id>/
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    
    # 2. 강의 리뷰 목록 조회: /api/v1/courses/<id>/reviews/
    path('<int:course_id>/reviews/', CourseReviewListView.as_view(), name='course-reviews'),
    
    # 3. 추천 강의 조회: /api/v1/courses/<id>/recommendations/
    path('<int:course_id>/recommendations/', CourseRecommendationView.as_view(), name='course-recommendations'),

    # 4. 키워드 검색 (ES + Fuzzy): /api/v1/courses/search/keyword/?search=...
    path('search/keyword/', CourseKeywordSearchView.as_view(), name='course-keyword-search'),

    # 5. 의미 기반 검색: /api/v1/courses/search/semantic/?query=...
    path('search/semantic/', CourseSemanticSearchView.as_view(), name='course-semantic-search'),
]
