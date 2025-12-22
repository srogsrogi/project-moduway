from django.urls import path
from .views import (
    CourseDetailView, 
    CourseReviewListView, 
    CourseRecommendationView
)

urlpatterns = [
    # 1. 강의 상세 정보 조회: /api/v1/courses/<id>/
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    
    # 2. 강의 리뷰 목록 조회: /api/v1/courses/<id>/reviews/
    path('<int:course_id>/reviews/', CourseReviewListView.as_view(), name='course-reviews'),
    
    # 3. 추천 강의 조회: /api/v1/courses/<id>/recommendations/
    path('<int:course_id>/recommendations/', CourseRecommendationView.as_view(), name='course-recommendations'),
]
