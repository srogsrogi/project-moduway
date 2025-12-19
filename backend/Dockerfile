# python:3.11-slim 이미지를 기반으로 함
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (PostgreSQL 연결 등을 위함)
# [시스템 도구 설치] - psql 명령어 사용을 위해 postgresql-client 포함
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \ 
    && rm -rf /var/lib/apt/lists/*

# 요구사항 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 실행 명령어 (manage.py runserver를 사용하거나 gunicorn 사용 가능)
# docker-compose에서 command를 덮어쓸 수 있음
# 현재는 compose up시 migrations 후 gunicorn 실행하고 있으므로 아래 코드는 실행되지 않음
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "config.wsgi:application"]