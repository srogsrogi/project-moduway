from django.urls import path
from .views import CourseDetailView  # 우리가 만들 뷰

urlpatterns = [
    # 프론트가 요청한 api/v1/courses/1/ 주소 중 '1/' 부분을 처리합니다.
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
]