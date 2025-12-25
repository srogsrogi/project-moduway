# 커뮤니티 (Community)

<br>

## 1. 개요
Community 앱은 사용자 간의 자유로운 소통과 정보 공유를 위한 **게시판 서비스**입니다. 
주제별 게시판, 계층형 댓글, 그리고 좋아요/스크랩 같은 반응형 기능을 통해 활발한 커뮤니티 활동을 지원합니다.

---

<br>

## 2. 주요 기능

### 2.1 게시판 및 게시글
- **주제별 분류:** 여러 개의 게시판(`Board`)을 운영하여 성격에 맞는 글을 작성/조회할 수 있습니다.
- **게시글 관리:** 마크다운이나 텍스트 기반의 게시글을 작성, 수정, 삭제할 수 있습니다.
- **검색 및 필터:** 키워드 검색과 게시판별 필터링을 통해 원하는 정보를 빠르게 찾습니다.

### 2.2 소통 및 상호작용
- **계층형 댓글(Reply):** 댓글에 대댓글을 달 수 있는 구조로, 특정 주제에 대한 심도 있는 토론을 지원합니다.
- **좋아요(Like):** 유용한 정보나 공감되는 글에 좋아요를 표시합니다.
- **스크랩(Scrap):** 다시 보고 싶은 중요한 글을 보관함에 저장합니다.

---

<br>

## 3. 기술 상세

### 3.1 모델 설계
- **Post & Board:** 게시글은 반드시 하나의 게시판에 속하며, 효율적인 조회를 위해 인덱싱됩니다.
- **Comment (Self-referencing):** `parent` 필드를 통해 무제한 깊이의 대댓글 확장이 가능하지만, UI 효율성을 위해 주로 2단계(댓글-대댓글) 구조를 사용합니다.
- **Interaction (M:N with Through):** 좋아요(`PostLike`)와 스크랩(`Scrap`)은 생성 시점 기록을 위해 중개 모델을 사용합니다.

### 3.2 성능 최적화 (Query Optimization)
Django ORM의 기능을 적극 활용하여 데이터 조회 성능을 극대화했습니다.

- **N+1 문제 해결:**
  - `select_related`: 작성자(`author`), 게시판(`board`) 등 1:1 관계 데이터 사전 로드.
  - `prefetch_related`: 댓글(`comments`) 및 대댓글 트리(`replies`) 일괄 로드.
- **집계 최적화:**
  - `annotate`: 게시글 목록 조회 시 좋아요 수, 댓글 수를 DB 레벨에서 미리 계산.
  - `Subquery & Exists`: 현재 접속한 사용자의 **좋아요/스크랩 여부**를 메인 쿼리에 포함시켜 별도 조회 없이 상태 확인 가능.

---

<br>

## 4. API 구성

### 4.1 게시판 및 게시글
| Method | Endpoint | 설명 |
| :--- | :--- | :--- |
| GET | `/api/v1/community/boards/` | 전체 게시판 목록 조회 (게시글 수 포함) |
| GET | `/api/v1/community/<board_id>/posts/` | 특정 게시판 게시글 목록 조회 |
| POST | `/api/v1/community/<board_id>/posts/` | 게시글 작성 |
| GET | `/api/v1/community/posts/<post_id>/` | 게시글 상세 조회 |
| GET | `/api/v1/community/posts/search/` | 게시글 검색 (`?q=키워드`) |

### 4.2 댓글 (Comment)
| Method | Endpoint | 설명 |
| :--- | :--- | :--- |
| GET | `/api/v1/community/posts/<post_id>/comments/` | 댓글 목록 조회 (대댓글 포함) |
| POST | `/api/v1/community/posts/<post_id>/comments/` | 댓글 작성 (대댓글 포함) |

### 4.3 반응 (Interaction)
| Method | Endpoint | 설명 |
| :--- | :--- | :--- |
| POST | `/api/v1/community/posts/<post_id>/likes/` | 좋아요 토글 |
| POST | `/api/v1/community/posts/<post_id>/scrap/` | 스크랩 토글 |

---

<br>

## 5. 시스템 아키텍처 (Architecture)

```text
                 ┌─────────────────────┐
                 │    Frontend (Vue)   │
                 │   - 게시판/게시글 UI   │
                 │   - 댓글/대댓글 기능   │
                 └──────────┬──────────┘
                            │ RESTful API
                            ▼
     ┌──────────────────────────────────────────────┐
     │           Django REST Framework              │
     │                                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │     API Layer (Views + Serializers)     │ │
     │  │       - PostList / DetailView           │ │
     │  │       - CommentList / DetailView        │ │
     │  │       - Like / Scrap Toggle             │ │
     │  └────────────┬────────────────────────────┘ │
     │               ▼                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │   Business Logic (Views & Models)       │ │
     │  │     - Permission (IsOwnerOrReadOnly)    │ │
     │  │     - Aggregation (Count Annotations)   │ │
     │  │     - Optimization (Prefetch Related)   │ │
     │  └────────────┬────────────────────────────┘ │
     │               ▼                              │
     │  ┌─────────────────────────────────────────┐ │
     │  │     Data Access Layer (ORM Models)      │ │
     │  │             - Board / Post              │ │
     │  │             - Comment (Reply Structure) │ │
     │  │             - PostLike / Scrap          │ │
     │  └──────────────────┬──────────────────────┘ │
     └─────────────────────┼────────────────────────┘
                           ▼
                 ┌───────────────────────┐
                 │       PostgreSQL      │
                 └───────────────────────┘
```

---

<br>

## 6. 앱 구조

```
community/
├── admin.py            # 관리자 페이지 설정
├── models.py           # Board, Post, Comment, PostLike, Scrap 모델
├── serializers.py      # API 데이터 직렬화 및 유효성 검증
├── urls.py             # URL 라우팅
├── views.py            # 비즈니스 로직 (ListView, DetailView 등)
└── permissions.py      # 권한 관리 (작성자 본인만 수정/삭제)
```
