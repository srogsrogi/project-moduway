# 강좌 관리 및 검색·추천 (Courses)

<br>

## 1. 개요
Courses 앱은 프로젝트의 핵심 데이터인 **강좌(Course) 정보**를 관리하고, 사용자가 원하는 강좌를 빠르고 정확하게 찾을 수 있도록 **다각화된 검색 및 추천 기능**을 제공합니다.

DB 기반의 전통적인 필터링부터 Elasticsearch와 AI 임베딩을 활용한 지능형 검색/추천까지 아우르는 하이브리드 시스템을 갖추고 있습니다.

---

<br>

## 2. 주요 기능 및 API

### 2.1 강좌 조회
- **강좌 목록 조회 (`/api/v1/courses/`):** 
  - **필터링:** 대분류, 중분류, 운영기관, 교수명 등 다양한 조건 조합 가능.
  - **정렬:** 평점순, 리뷰 많은순, 최신순 등 제공.
  - **중복 제거:** 동일 강좌(이름+교수)가 여러 기수로 개설된 경우, 최신 강좌 1개만 노출하여 목록 깔끔화.
  - **최적화:** `annotate` 및 `Window Function` 활용하여 N+1 문제 방지 및 DB단 중복 처리.

### 2.2 검색 시스템
- **키워드 검색 (Keyword Search):** DB `icontains`를 이용한 단순 매칭.
  - **API:** `/api/v1/courses/search/keyword/`
  - **특징:** Elasticsearch의 `fuzziness` 기능을 활용하여 오타가 있어도(예: "파이선") 정확한 결과("파이썬") 반환.
- **의미 기반 검색 (Semantic Search):**
  - **API:** `/api/v1/courses/search/semantic/`
  - **특징:** 사용자의 의도("데이터 분석 입문하기 좋은 강의")를 벡터로 변환하여 맥락이 일치하는 강좌 검색.

### 2.3 추천 시스템 (Content-based Filtering)
- **유사 강좌 추천:**
  - **API:** `/api/v1/courses/<id>/recommendations/`
  - **로직:** 현재 보고 있는 강좌의 벡터와 코사인 유사도가 가장 높은 상위 강좌 4개를 실시간 추천.
  - **목적:** 사용자의 탐색 경험을 끊김 없이 연결.

---

<br>

## 3. 기술 상세

### 3.1 하이브리드 데이터 아키텍처
대규모 데이터의 효율적 관리와 고속 검색을 위해 RDBMS와 검색 엔진을 병행 사용합니다.

| 구성 요소 | 역할 | 비고 |
| :--- | :--- | :--- |
| **PostgreSQL** | 메인 데이터 저장소 (강좌 상세, 리뷰, 수강 이력) | `Window Function`으로 중복 관리 |
| **pgvector** | 강좌 벡터(`embedding`) 원본 저장 및 관리 | 데이터 무결성 보장 |
| **Elasticsearch** | 고속 검색, 오타 보정, 벡터 유사도 검색 | `kmooc_courses` 인덱스 사용 |

### 3.2 데이터 전처리 및 임베딩 전략
- **모델:** `OPENAI text-embedding-3-small` (1536차원)
- **전처리:**
  - **Title Boosting:** 강좌명의 중요도를 반영하기 위해 텍스트 내 3회 반복.
  - **Rich Context:** 강좌명 + 대분류 + 중분류 + 요약을 결합하여 풍부한 정보 벡터화.

---

<br>

## 4. 데이터 파이프라인 명령어

검색 및 추천 시스템 구축을 위해 데이터 적재와 인덱싱 과정이 필요합니다.

### 4.1 초기 데이터 적재
데이터 소스의 상태에 따라 적절한 명령어를 선택하세요.

컨테이너 내에서 서버를 실행하는 경우 `docker exec -it` 명령어를 포함하여 실행해야 합니다.

```bash
# CASE A: 초기 구축 (Raw Data)
# - K-MOOC 원본 CSV 데이터를 DB에 적재합니다.
# - 임베딩이 없으므로 후속 단계(make_embeddings)가 반드시 필요합니다.
python manage.py load_courses

# CASE B: 백업 복구 (Processed Data)
# - 임베딩이 포함된 JSON 백업 데이터를 복구합니다.
# - 이미 벡터가 존재하므로 make_embeddings 단계를 건너뛸 수 있습니다.
python manage.py import_courses
```

### 4.2 시스템 초기화 및 연동
데이터 적재 후 아래 과정을 순차적으로 진행합니다.

```bash
# 1. Elasticsearch 인덱스 생성 (Index Setup)
python manage.py setup_es

# 2. 임베딩 생성 (Vectorize)
# - CASE A(load_courses)로 적재한 경우에만 실행합니다.
# - CASE B(import_courses)인 경우 이미 임베딩이 있으므로 생략 가능합니다.
python manage.py make_embeddings

# 3. Elasticsearch 데이터 동기화 (DB -> ES)
# - DB의 강좌 정보와 임베딩 벡터를 검색 엔진으로 전송합니다.
python manage.py push_to_es
```

---

<br>

## 5. 시스템 아키텍처 (Architecture)

```text
                 ┌─────────────────────┐
                 │    Frontend (Vue)   │
                 │   - 강좌 검색/목록    │
                 │   - 강좌 상세/리뷰    │
                 └──────────┬──────────┘
                            │ RESTful API
                            ▼
     ┌──────────────────────────────────────────────┐
     │           Django REST Framework              │
     │                                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │     API Layer (Views + Serializers)     │ │
     │  │       - CourseList / DetailView         │ │
     │  │       - CourseRecommendationView        │ │
     │  │       - Semantic/Keyword Search         │ │
     │  └────────────┬────────────────────────────┘ │
     │               ▼                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │      Logic Layer (Search & Embed)       │ │
     │  │     ┌──────────┐  ┌──────────┐          │ │
     │  │     │ ES Client│  │ GMS Client│         │ │
     │  │     │ (Search) │  │ (Embed)  │          │ │
     │  │     └──────────┘  └──────────┘          │ │
     │  └────────────┬────────────────────────────┘ │
     │               ▼                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │     Data Access Layer (ORM Models)      │ │
     │  │             - Course                    │ │
     │  │             - Enrollment / Wishlist     │ │
     │  │             - CourseReview              │ │
     │  └──────────────────┬──────────────────────┘ │
     └─────────────────────┼────────────────────────┘
                           ▼
           ┌───────────────┴────────────────┐
           │                                │
           ▼                                ▼
 ┌───────────────────────┐      ┌───────────────────────┐
 │       PostgreSQL      │      │     Elasticsearch     │
 │ (Core Data + Metadata)│      │(Vector/Keyword Search)│
 └───────────────────────┘      └───────────────────────┘
                                            ▲
                                            │
                                ┌───────────────────────┐
                                │   GMS API (OpenAI)    │
                                │ - Embedding Generation│
                                └───────────────────────┘
```

---

<br>

## 6. 앱 구조

```
courses/
├── admin.py                  # Django Admin 설정
├── apps.py                   # 앱 설정
├── models.py                 # Course(pgvector 포함), CourseReview 등 모델
├── serializers.py            # API 응답 직렬화
├── tests.py                  # 유닛 테스트
├── urls.py                   # URL 라우팅 설정
├── views.py                  # 비즈니스 로직
│   ├── CourseListView        # 목록 및 필터링 (DB)
│   ├── CourseKeywordSearchView   # 오타 보정 검색 (ES)
│   ├── CourseSemanticSearchView  # 의미 기반 검색 (ES+Vector)
│   └── CourseRecommendationView  # 유사 강좌 추천 (ES+Vector)
│
└── management/commands/      # 데이터 파이프라인 스크립트
    ├── setup_es.py           # ES 인덱스 생성 및 설정
    ├── make_embeddings.py    # 임베딩 생성 (OpenAI)
    ├── push_to_es.py         # ES 데이터 동기화
    ├── load_courses.py       # CSV 데이터 적재 (Raw)
    └── import_courses.py     # 백업 데이터 임포트 (Embedded)
```