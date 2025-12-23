# Data Pipeline Workflow

이 문서는 K-MOOC 데이터 수집부터 정제, 가공, 그리고 DB 적재까지의 전체 흐름을 설명합니다.

## 📂 디렉토리 구조

```
data/
├── raw_data/           # 원본 데이터 수집
│   ├── save_data_to_csv.py  # K-MOOC API 호출 및 원본 저장
│   └── kmooc_courses_final.csv (생성됨)
├── cleaned_data/       # 1차 정제 데이터
│   ├── clean_data.py        # 필터링 및 JSON 변환
│   └── kmooc_courses_public.json (생성됨)
├── processing/         # 2차 가공 (파생변수 등)
│   ├── process_data.py      # 최종 DB 적재용 포맷으로 변환
│   └── data_processing.ipynb (분석용 노트북)
└── backups/            # 최종 산출물
    └── kmooc_processed_data.csv (DB 적재용)
```

## 🚀 실행 순서 (Workflow)

프로젝트 루트 디렉토리(`project-moduway`)에서 아래 명령어를 순서대로 실행하세요.

### 1. 데이터 수집 (Collection)
K-MOOC API를 호출하여 최신 강좌 정보를 수집합니다. HTML 태그가 포함된 원본 요약(`raw_summary`)도 함께 저장됩니다.

```bash
python data/raw_data/save_data_to_csv.py
```
- **입력:** K-MOOC Open API
- **출력:** `data/raw_data/kmooc_courses_final.csv`
- **주의:** API 호출에 시간이 소요될 수 있습니다. `SERVICE_KEY` 설정이 필요합니다.

### 2. 데이터 정제 (Cleaning)
수집된 CSV 파일에서 불필요한 데이터를 필터링하고(결측치 제거 등), 중간 단계인 JSON 형식으로 변환합니다.

```bash
python data/clean_data.py
```
- **입력:** `data/raw_data/kmooc_courses_final.csv`
- **출력:** `data/cleaned_data/kmooc_courses_public.json`

### 3. 데이터 가공 (Processing)
정제된 데이터를 기반으로 파생 변수(content_key 등)를 생성하고, DB 적재에 필요한 최종 CSV 포맷을 생성합니다.

```bash
python data/processing/process_data.py
```
- **입력:** `data/cleaned_data/kmooc_courses_public.json`
- **출력:** `data/backups/kmooc_processed_data.csv`

### 4. DB 적재 (Loading)
최종 가공된 CSV 파일을 Django 관리 명령어를 통해 DB(`Course` 테이블)에 적재합니다.
기존 데이터가 있을 경우 `kmooc_id`를 기준으로 매칭하여, 비어있는 `raw_summary` 등의 필드를 업데이트합니다.

```bash
python backend/manage.py load_courses
# 컨테이너 환경인 경우
docker exec -it moduway-backend python manage.py load_courses
```
- **입력:** `data/backups/kmooc_processed_data.csv`
- **출력:** PostgreSQL Database Update

---

## 🛠️ 주요 변경 사항 (2025-12-22)
- **HTML 원본 저장:** `Course` 모델에 `raw_summary` 필드가 추가되었습니다.
- **스크립트 업데이트:** `save_data_to_csv.py`, `clean_data.py`, `process_data.py`, `load_courses.py`가 모두 `raw_summary`를 처리하도록 수정되었습니다.
