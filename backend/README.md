# Backend

Django REST Framework 기반의 백엔드 서버입니다.

## 프로젝트 구조

```
backend/
├── apps/                 # Django 앱 디렉토리
│   ├── accounts/         # 사용자 인증 및 계정 관리
│   ├── community/        # 커뮤니티 기능
│   ├── comparisons/      # AI강좌 비교분석 기능
│   ├── courses/          # 강좌 관리
│   └── mypage/           # 마이페이지 - 집계 전용 앱
│
├── config/               # Django 설정
│   ├── settings/         # 환경별 설정
|   |   ├── base.py       # 공통
|   |   ├── dev.py        # 로컬
|   |   └── prod.py       # 운영
|   |  
│   ├── urls.py           # URL 라우팅
│   ├── wsgi.py          
│   └── asgi.py          
│
├── templates/            # HTML 템플릿 - 백엔드 작업을 위한 목업
├── manage.py           
├── requirements.txt     
└── Dockerfile            # Docker 이미지 빌드 설정
```

## 시작하기

### 사전 요구사항
- Python
- pip

### 설치 및 실행

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **환경 변수 설정**
```bash
cp ../.env.example ../.env
```

3. **마이그레이션 실행**
```bash
python manage.py migrate --settings=config.settings.dev
```

4. **개발 서버 실행**
```bash
python manage.py runserver --settings=config.settings.dev
```

서버는 `http://localhost:8000`에서 시작됩니다.

## Docker로 실행

```bash
docker-compose up backend
```

## 주요 명령어

- `python manage.py makemigrations` - 데이터베이스 마이그레이션 파일 생성
- `python manage.py migrate` - 마이그레이션 적용
- `python manage.py createsuperuser` - 관리자 계정 생성

## API 엔드포인트

각 앱의 주요 엔드포인트는 [config/urls.py](../config/urls.py) 또는 각 앱의 `urls.py`에서 확인할 수 있습니다.

## 개발 가이드

자세한 내용은 [docs/](../docs/)를 참조하세요.
- [커밋 컨벤션](../docs/commit-convention.md)
- [Git 브랜치 규칙](../docs/git-branch-rule.md)

## 라이선스

이 프로젝트는 [LICENSE](../LICENSE) 파일을 참조하세요.