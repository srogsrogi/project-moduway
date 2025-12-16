# backend/config/settings/prod.py

from .base import *
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

env_file = Path("/home/ubuntu/.env.prod")
if not env_file.exists():
    raise RuntimeError(".env.prod file not found")


load_dotenv(env_file, override=True)

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

# 운영용은 postgresql 사용
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PROD_DB_NAME"),
        "USER": os.environ.get("PROD_DB_USER"),
        "PASSWORD": os.environ.get("PROD_DB_PASSWORD"),
        "HOST": os.environ.get("PROD_DB_HOST", "localhost"),
        "PORT": int(os.environ.get("PROD_DB_PORT", 5432)),
        "CONN_MAX_AGE": int(os.environ.get("PROD_DB_CONN_MAX_AGE", 60)),
    }
}

# 로그 디렉토리 생성
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Django 로깅: 콘솔 + 파일(7일 보관)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}:{lineno} | {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file_rotating": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "django.log"),
            "when": "D",
            "interval": 1,
            "backupCount": 7,
            "encoding": "utf-8",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file_rotating"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console", "file_rotating"], "level": "WARNING", "propagate": False},
        "django.request": {"handlers": ["console", "file_rotating"], "level": "ERROR", "propagate": False},
    },
}