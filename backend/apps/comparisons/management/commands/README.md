# AI 비교 분석 및 감성 분석 커맨드

이 디렉토리는 강좌의 AI 평가(요약/평점) 생성과 리뷰 감성 분석 모델의 학습 및 평가를 관리하는 관리자 명령어(Management Commands)들을 포함하고 있습니다.

> **⚠️ Note**: 본 디렉토리 내의 모든 모듈은 생성형 AI의 도움을 받아 작성 및 최적화되었습니다.

---

## 1. 명령어 목록 및 상세 명세

### 1.1 `generate_ai_reviews.py`
- **기능**: LLM 기반 강좌 AI 평가 생성 (요약 및 평점)
- **실행**: `python manage.py generate_ai_reviews`
- **모델**: `gpt-4o-mini`
- **상세 동작**:
  - 모든 강좌(Course) 또는 특정 강좌에 대해 OpenAI LLM을 호출하여 요약과 평점(이론/실무/난이도)을 생성합니다.
  - 강좌 주차 수를 기반으로 학습 기간(Duration) 평점을 자동으로 계산합니다.
  - 생성된 데이터는 `CourseAIReview` 모델에 저장되며, `--output` 옵션 사용 시 CSV로 백업할 수 있습니다.

### 1.2 `load_ai_reviews.py`
- **기능**: AI 리뷰 백업 데이터 로드 (CSV -> DB)
- **실행**: `python manage.py load_ai_reviews [--file <filename>]`
- **소스**: `data/backups/ai_reviews.csv` (기본값)
- **상세 동작**:
  - CSV 형식으로 백업된 AI 평가 데이터를 DB로 복원합니다.
  - `course_id`를 기준으로 매칭하며, 기존 데이터가 있을 경우 덮어쓰기(Upsert)를 수행합니다.

### 1.3 `generate_dummy_reviews.py`
- **기능**: 감성 분석 학습용 더미 데이터 생성
- **실행**: `python manage.py generate_dummy_reviews`
- **상세 동작**:
  - 실제 강의 리뷰와 유사한 문장 구조를 가진 긍정/부정 텍스트 데이터를 생성합니다.
  - 감성 분석 모델의 초기 학습 및 테스트를 위한 `fixtures/sentiment_training_data.csv` 파일을 생성합니다.

### 1.4 `train_model.py`
- **기능**: 감성 분석 모델 학습 및 저장
- **실행**: `python manage.py train_model`
- **모델/라이브러리**: `Kiwi` (토크나이저), `LogisticRegression` (분류기)
- **상세 동작**:
  - 한국어 강의 리뷰 데이터를 로드하여 형태소 분석 및 TF-IDF 벡터화를 수행합니다.
  - 로지스틱 회귀 모델을 학습하고 파이프라인 형태로 저장합니다.
  - **출력 파일**: `sentiment_pipeline.joblib` (모델), `model_metadata.json` (성능 및 설정)

### 1.5 `evaluate_model.py`
- **기능**: 감성 분석 모델 성능 평가
- **실행**: `python manage.py evaluate_model`
- **상세 동작**:
  - 저장된 모델을 로드하여 테스트 데이터셋에 대해 정확도, 정밀도, 재현율 등 지표를 산출합니다.
  - 평가 결과를 JSON 형식으로 저장하여 시계열 성능 모니터링에 활용합니다.

---

## 2. 데이터 및 모델 파이프라인 실행 가이드

강좌 AI 분석 및 감성 분석 시스템 가동을 위한 권장 실행 순서입니다.

### [A] 강좌 AI 평가 구축
1.  **AI 평가 생성**: `python manage.py generate_ai_reviews` (LLM 비용 발생 주의)
2.  (선택) **백업 데이터 로드**: `python manage.py load_ai_reviews` (기존 백업이 있는 경우)

### [B] 감성 분석 모델 구축
1.  **학습 데이터 준비**: `python manage.py generate_dummy_reviews` (실제 데이터가 없는 경우)
2.  **모델 학습**: `python manage.py train_model`
3.  **모델 검증**: `python manage.py evaluate_model`
