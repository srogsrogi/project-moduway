# backend/config/settings/dev.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'backend', 'moduway-backend']

# DB : PostgreSQL (Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'moduway',
        'USER': 'moduway',
        'PASSWORD': 'moduway',
        'HOST': 'db',  # 로컬에서 실행 시 Docker 포트 포워딩(5432) 사용
        'PORT': '5432',
    }
}

#TODO 개발용: 이메일을 실제 발송하지 않고 콘솔에 출력
# - 회원가입 / 비밀번호 재설정 / 이메일 인증 플로우 테스트 목적
# - SMTP 서버 설정 없이도 인증 메일 내용 및 링크 확인 가능
# - 운영 환경에서는 SMTP 또는 외부 이메일 서비스로 교체 필요
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
#TODO 개발용: 이메일 인증 강제 해제 (API 테스트 편의)
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

ELASTICSEARCH_URL = "http://elasticsearch:9200"