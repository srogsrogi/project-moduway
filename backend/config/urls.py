"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# backend/config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    # REST API용 accounts 엔드포인트
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/community/', include('apps.community.urls')),

    # django-allauth가 내부적으로'만' 사용하는 URL들
    # (socialaccount_login, socialaccount_signup 등 포함)
    path('accounts/', include('allauth.urls')),
]

# API 문서화 도구용 엔드포인트
# 보안을 위해 개발 환경에서만 노출
if settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

    urlpatterns += [
        # API 스키마와 문서화.
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        # 둘 중 편한 것으로 선택해서 보기.
        path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]        
