# backend/apps/accounts/signals.py

from django.urls import path, include
from dj_rest_auth.views import PasswordChangeView

urlpatterns = [
    # 기본 | 로그인, 로그아웃, 상세정보
    path('', include('dj_rest_auth.urls')),

    # 회원가입
    path('registration/', include('dj_rest_auth.registration.urls')),
    
    # 기능정의서 U02 (비밀번호 변경)
    path('mypage/profile/password/change/', PasswordChangeView.as_view(), name='password_change_custom'),
]