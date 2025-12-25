# 데이터 파이프라인 & 커맨드

이 디렉토리는 강좌 데이터의 생애주기(적재 -> 처리 -> 서비스 연동)를 관리하는 관리자 명령어(Management Commands)들을 포함하고 있습니다.

> **⚠️ Note**: 본 디렉토리 내의 모든 모듈은 생성형 AI의 도움을 받아 작성 및 최적화되었습니다.

---

## 1. 명령어 목록 및 상세 명세

### 1.1 `setup_es.py`
- **기능**: Elasticsearch 인덱스 초기화 및 매핑 설정
- **실행**: `python manage.py setup_es`
- **상세 동작**:
  - `kmooc_courses` 인덱스를 생성합니다. (기존 인덱스 존재 시 삭제 후 재생성)
  - **Nori 형태소 분석기**(`nori_tokenizer`)를 설정하여 한국어 검색 성능을 최적화합니다.
  - 벡터 검색을 위한 `dense_vector` 필드(1536차원, 코사인 유사도)를 정의합니다.

### 1.2 `load_courses.py`
- **기능**: 초기 데이터 적재 (CSV -> DB)
- **실행**: `python manage.py load_courses`
- **소스**: `data/backups/kmooc_processed_data.csv`
- **상세 동작**:
  - 전처리된 K-MOOC CSV 파일을 읽어 PostgreSQL DB에 저장합니다.
  - `kmooc_id`를 기준으로 중복을 체크하며, HTML 태그가 포함된 `raw_summary` 등의 상세 데이터를 처리합니다.
  - 날짜 및 숫자 데이터의 타입 변환과 예외 처리를 수행합니다.

### 1.3 `import_courses.py`
- **기능**: 백업 데이터 복구 (JSON -> DB)
- **실행**: `python manage.py import_courses [--input <filename>]`
- **소스**: `data/backups/courses_backup.json` (기본값)
- **상세 동작**:
  - **임베딩 벡터가 포함된** JSON 백업 파일을 DB로 복원합니다.
  - 이 명령어로 데이터를 복구한 경우, 이미 벡터 데이터가 존재하므로 `make_embeddings` 단계를 건너뛸 수 있습니다.

### 1.4 `make_embeddings.py`
- **기능**: 강좌 텍스트 벡터화 (Embedding Generation)
- **실행**: `python manage.py make_embeddings`
- **모델**: `text-embedding-3-small` (OpenAI)
- **상세 동작**:
  - DB에서 임베딩이 없는(`embedding__isnull=True`) 강좌만 추출하여 처리합니다.
  - **전처리 전략**:
    - 불용어(email, 날짜, 공통 단어 등) 제거.
    - **Title Boosting**: 강좌명의 중요도를 높이기 위해 3회 반복.
    - 카테고리와 요약을 결합하고, 최대 길이(3000자)를 제한하여 토큰 초과를 방지합니다.
  - **Batch Processing**: API 호출 효율성을 위해 2개씩 묶어서 배치 처리합니다.

### 1.5 `push_to_es.py`
- **기능**: 검색 엔진 동기화 (DB -> Elasticsearch)
- **실행**: `python manage.py push_to_es`
- **상세 동작**:
  - DB에 저장된 강좌 메타데이터와 생성된 임베딩 벡터를 Elasticsearch로 전송합니다.
  - 대량 데이터 처리를 위해 `/_bulk` API를 사용하여 500개 단위로 전송합니다.
  - JSON 직렬화 시 numpy 등의 호환성 문제를 방지하기 위해 `float` 형변환을 수행합니다.

---

## 2. 데이터 파이프라인 실행 가이드

전체 시스템 구축을 위해 아래 순서대로 실행하는 것을 권장합니다.

컨테이너 내에서 서버를 실행하는 경우 `docker exec -it` 명령어를 포함하여 실행해야 합니다.

1.  **인덱스 초기화**: `python manage.py setup_es`
2.  **데이터 적재**:
    *   초기 구축 시: `python manage.py load_courses`
    *   백업 복구 시: `python manage.py import_courses`
3.  **임베딩 생성** (초기 구축 시에만): `python manage.py make_embeddings`
4.  **검색 엔진 동기화**: `python manage.py push_to_es`
