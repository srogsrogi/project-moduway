# backend/config/settings/dev.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# DB : 개발용은 SQLite 사용
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 개발용: 이메일을 실제 발송하지 않고 콘솔에 출력
# - 회원가입 / 비밀번호 재설정 / 이메일 인증 플로우 테스트 목적
# - SMTP 서버 설정 없이도 인증 메일 내용 및 링크 확인 가능
# - 운영 환경에서는 SMTP 또는 외부 이메일 서비스로 교체 필요
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"