# 마이페이지 아키텍쳐

<br>

## 1. 개요

```
마이페이지는 여러 도메인에 흩어진 사용자 데이터를  
**하나의 사용자 관점으로 집계하여 제공하는 Aggregation Layer**입니다!!
```

<br>

- Mypage앱은 본 플랫폼 내에서 로그인한 사용자의 개인화된 데이터를 통합하여 제공하는 View & Serializers 전용 앱입니다.

- 사용자의 학습 현황, 커뮤니티 활동 내역, 프로필 설정 등의 데이터를 사용자 중심으로 집계하여 제공합니다.

- 전역이 is_authenticated이지만, 보안을 신경쓰기 위해 방어적 설계를 적용하였습니다.

- 집계의 경우 python 보다는 DB 레이어에서 진행하여 N+1 문제를 방지하고자 하였습니다. 



---

<br>

## 2. 특이사항

<br>

본 mypage 앱은 독자적인 모델(DB Table)을 정의하지 않습니다.

1. 모델 배치 전략 (Domain-Driven):
   - 데이터의 주체가 되는 도메인별로 모델을 분리하여 배치하였습니다.
   - User 관련: accounts | `User`, `EmailVerfication`, `UserConsent`
   - 게시글/커뮤니티: community | `Board`, `Post`, `Comment`, `PostLikes`, `Scrap`
   - 강의/수강신청: courses | `Course`, `Enrollment`, `WishList`, `CourseReview`

2. mypage 앱의 역할:
   - View & Serializer 전용 앱 (Aggregation Layer)
   - 타 앱(accounts, community, courses)의 모델을 Import하여,
     사용자 중심의 데이터를 조회(Query)하고 가공하여 응답하는 역할을 수행합니다.

3. 기대 효과:
   - 앱 간의 불필요한 순환 참조(Circular Dependency) 방지
   - 데이터 소유권과 참조 로직의 명확한 분리


---

## 3. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Client (Web/Mobile)                        │
│                 - Authorization: Bearer <access_token>               │
└─────────────────────────────────────────────────────────────────────┘
                               │  HTTP
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Django DRF  (/api/v1)                          │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                 mypage app (Aggregation Layer)              │   │
│   │   - View & Serializer 전용                                   │   │
│   │   - "사용자 관점"으로 여러 도메인 데이터를 집계/가공                   │   │
│   │   - DB 레벨 집계(aggregate/annotate)로 N+1 방지                 │   │
│   │                                                             │   │
│   │   Endpoints                                                 │   │
│   │   ├─ GET  /mypage/dashboard/stats/        → 학습 현황 통계     │   │
│   │   ├─ GET  /mypage/courses/recent/         → 최근 학습 강좌     │   │
│   │   ├─ GET  /mypage/courses/?status=...     → 수강 목록         │   │
│   │   ├─ GET  /mypage/courses/{id}/status/    → 수강 상세         │   │
│   │   ├─ POST /mypage/courses/{id}/rating/    → 수강평 upsert     │   │
│   │   ├─ DEL  /mypage/courses/{id}/rating/    → 수강평 삭제        │   │
│   │   ├─ GET  /mypage/wishlist/               → 찜 목록           │   │
│   │   ├─ POST /mypage/wishlist/{id}/          → 찜 추가           │   │
│   │   ├─ DEL  /mypage/wishlist/{id}/          → 찜 삭제           │   │
│   │   ├─ GET  /mypage/community/stats/        → 커뮤니티 통계       │   │
│   │   ├─ GET  /mypage/community/posts/        → 내가 쓴 글         │   │
│   │   ├─ GET  /mypage/community/comments/     → 내가 쓴 댓글       │   │
│   │   ├─ GET  /mypage/scraps/                 → 스크랩 목록        │   │
│   │   └─ GET/PUT /mypage/profile/             → 프로필 조회/수정    │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                               │ ORM Query (join/aggregate/annotate) │
└───────────────────────────────┼─────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Domain Apps (Data Owner)                    │
│                                                                     │
│   accounts  ── User, EmailVerification, UserConsent                 │
│      ▲              │ (marketing_opt_in 등)                         │
│      │              │                                               │
│   community ─ Board, Post, Comment, PostLikes, Scrap                │
│      ▲              │ (내 글/댓글/스크랩/받은 좋아요 집계)                  │
│      │              │                                               │
│   courses   ─ Course, Enrollment, Wishlist, CourseReview            │
│                     (수강/진도/리뷰/찜/최근 학습 강좌)                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                               Database                              │
│                - mypage는 "독자 테이블 없음" (조회/집계만 수행)             │
└─────────────────────────────────────────────────────────────────────┘


```

<br>

------

## 4. API 구성

### 4.1 Endpoints

| **Method** | **Endpoint**                          | **Description**                                    |
| ---------- | ------------------------------------- | -------------------------------------------------- |
| **GET**    | `/api/v1/mypage/dashboard/stats/`     | 학습 현황 요약 (수강/완료/찜/리뷰 수 집계)         |
| **GET**    | `/api/v1/mypage/courses/recent/`      | 최근 학습 강좌 조회 (이어듣기)                     |
| **GET**    | `/api/v1/mypage/courses/`             | 수강 강좌 목록 조회 (`?status=enrolled|completed`) |
| **GET**    | `/api/v1/mypage/courses/{id}/status/` | 특정 강좌 수강 상세 정보 조회                      |
| **POST**   | `/api/v1/mypage/courses/{id}/rating/` | 수강평 등록/수정                                   |
| **DEL**    | `/api/v1/mypage/courses/{id}/rating/` | 수강평 삭제                                        |
| **GET**    | `/api/v1/mypage/wishlist/`            | 관심 강좌(위시리스트) 목록 조회                    |
| **POST**   | `/api/v1/mypage/wishlist/{id}/`       | 관심 강좌 추가                                     |
| **DEL**    | `/api/v1/mypage/wishlist/{id}/`       | 관심 강좌 삭제                                     |
| **GET**    | `/api/v1/mypage/community/stats/`     | 커뮤니티 활동 통계 (작성 글/댓글/스크랩 등)        |
| **GET**    | `/api/v1/mypage/community/posts/`     | 내가 쓴 글 목록 조회                               |
| **GET**    | `/api/v1/mypage/community/comments/`  | 내가 쓴 댓글 목록 조회                             |
| **GET**    | `/api/v1/mypage/scraps/`              | 스크랩한 게시글 목록 조회                          |
| **GET**    | `/api/v1/mypage/profile/`             | 내 프로필 정보 조회                                |
| **PUT**    | `/api/v1/mypage/profile/`             | 내 프로필 정보 수정                                |

<br>

### 4.2 URL 구조

```
/api/v1/mypage/
├── dashboard/
│   └── stats/                          # GET: 학습 현황 요약
├── courses/
│   ├── recent/                         # GET: 최근 학습 강좌
│   ├── /                               # GET: 수강 강좌 목록 (?status=enrolled|completed)
│   └── {course_id}/
│       ├── status/                     # GET: 강좌 수강 상세 정보
│       └── rating/                     # POST: 수강평 등록/수정
│                                       # DELETE: 수강평 삭제
├── wishlist/
│   ├── /                               # GET: 관심 강좌 목록
│   └── {course_id}/                    # POST: 관심 강좌 추가
│                                       # DELETE: 관심 강좌 삭제
├── community/
│   ├── stats/                          # GET: 커뮤니티 활동 통계
│   ├── posts/                          # GET: 내가 쓴 글 목록
│   └── comments/                       # GET: 내가 쓴 댓글 목록
├── scraps/                             # GET: 스크랩한 게시글 목록
└── profile/
    ├── /                               # GET: 내 정보 조회
    │                                   # PUT: 내 정보 수정
    └── password/change/                # POST: 비밀번호 변경 (이미 구현됨)
```

<br>

## 5. Serializers 구성

```
1. 대시보드
  - 1. DashboardStatsSerializer | 학습 현황 요약

2. 학습현황
  - 1. SimpleCourseSerializer           | 간단한 강좌 정보
  - 2. EnrollmentListSerializer          | 수강 목록
  - 3. EnrollmentDetailSerializer       | 수강 상세 정보
  - 4. CourseReviewSerializer           | 수강평
  - 5. WishlistSerializer               | 위시리스트

3. 커뮤니티
  - 1. CommunityStatsSerializer | 커뮤니티 활동 통계
  - 2. MyPostSerializer         | 내가 쓴 글 목록
  - 3. MyCommentSerializer      | 내가 쓴 댓글 목록
  - 4. MyScrapSerializer        | 내가 스크랩한 게시글 목록

4. 내 계정
 - 1. ProfileSerializer        | 내 정보 조회/수정

참고:
- 관심분야 설정 탭은 MVP 범위 제외로 이번 구현에 포함하지 않음 (추후 구현 예정)
"""

```

------

<br>

## 6. Views 구성

```
  1. 대시보드
  - 1. DashboardStatsView       | 학습 현황 요약 (수강/완료/찜/리뷰 수 집계)

  2. 학습 현황
  - 1. RecentCourseView         | 최근 학습 강좌 조회 (이어듣기 기능까지)
  - 2. EnrollmentListView       | 수강 목록 조회 (수강중, 수강완료 필터링)
  - 3. EnrollmentStatusView     | 특정 강좌의 수강 상세 정보 조회
  - 4. CourseReviewView         | 수강평 등록/수정/삭제
  - 5.1. WishlistListView       | 위시리스트 목록 조회
  - 5.2. WishlistToggleView     | 위시리스트 추가/삭제

  3. 커뮤니티
  - 1. CommunityStatsView       | 커뮤니티 활동 통계 (작성 글/댓글/스크랩/받은 좋아요)
  - 2. MyPostListView           | 내가 쓴 글 목록
  - 3. MyCommentListView        | 내가 쓴 댓글 목록
  - 4. MyScrapListView          | 내가 스크랩한 게시글 목록

  4. 내 계정
  - 1. ProfileView             | 내 정보 조회/수정 (마케팅 동의 포함)
  """
```



---

<br>

---

## 7. 설계 원칙 (Design Principles)

### 7.1 Aggregation Layer 분리
- mypage 앱은 도메인 로직을 소유하지 않으며,  
  accounts / courses / community 앱의 데이터를 사용자 관점으로 집계하는 역할만 담당한다.
- 비즈니스 규칙은 각 도메인 앱에 유지하고,  
  mypage는 조회(Query)와 응답(Response) 책임만 가진다.

### 7.2 DB 중심 집계 전략
- Python 루프 기반 집계 대신 `aggregate`, `annotate`, `Count`, `Q`를 적극 활용
- 모든 통계성 API는 DB 레벨에서 1~2개의 쿼리로 종료되도록 설계
- N+1 문제 방지를 위해 `select_related`, `prefetch_related`를 명시적으로 사용

### 7.3 방어적 인증 설계
- 전역 permission 정책과 무관하게,
  모든 View에서 IsAuthenticated를 명시적으로 선언
- 개인정보/개인화 데이터 영역임을 코드 레벨에서 명확히 드러냄

---

## 8. 성능 최적화 포인트

| 구분           | 적용 방식                    |
| -------------- | ---------------------------- |
| 통계 집계      | `aggregate()` 단일 쿼리      |
| 리스트 조회    | `select_related`, `annotate` |
| 좋아요/댓글 수 | DB 사전 계산 후 응답         |
| Payload 최적화 | 중첩 Serializer 최소화       |
| 정렬 기준      | 인덱스 활용 가능한 컬럼 우선 |

---

## 9. API 응답 일관성 규칙

- 모든 목록 API는 **ListAPIView** 기반
- 단일 조회는 **RetrieveAPIView**
- 생성/수정/삭제는 **APIView**로 명시적 제어
- 상태 코드 규칙:
  - `200 OK` : 조회/수정 성공
  - `201 Created` : 신규 생성
  - `204 No Content` : 삭제 성공
  - `404 Not Found` : 권한 없음 또는 리소스 없음
  - `400 Bad Request` : 입력 검증 실패

---

## 10. 확장 고려 사항

- 마이페이지 캐싱 (Redis) 적용
- 통계 API 비동기 집계 (Celery)
- 관리자용 사용자 활동 대시보드
- 마이페이지 전용 검색/필터링 기능