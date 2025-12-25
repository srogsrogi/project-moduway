# Accounts

<br>

## 1. 개요

Accounts 앱은

사용자 인증, 회원가입, 소셜 로그인, 프로필 관리 등

사용자 계정과 관련된 모든 핵심 기능을 담당하는 백엔드 로직을 포함하고 있습니다.

Django의 기본 인증 시스템을 확장하여 Custom User 모델을 사용하며,

dj-rest-auth와 django-allauth를 활용하여 REST API 기반 인증과 소셜 로그인을 지원합니다.

<br>

<br>

## 2. 특이사항

- Django REST Framework + dj-rest-auth 기반 토큰 인증
- django-allauth를 활용한 소셜 로그인 (Google OAuth 2.0)
- Custom User 모델 확장 (AbstractUser 상속)
- 회원가입 시 약관 동의 정보 분리 저장 (UserConsent)
- 트랜잭션 보장을 통한 데이터 일관성 확보
- 이메일 인증 준비 (EmailVerification 모델, 현재 로컬 환경에서는 실행하지 않음)

---

## 3. 전체 아키텍처

```
                     ┌─────────────────────┐
                     │    Frontend (Vue)   │
                     │   - 회원가입 폼      │
                     │   - 로그인 폼        │
                     │   - Google 로그인    │
                     └──────────┬──────────┘
                                │ RESTful API (JSON)
                                ▼
         ┌──────────────────────────────────────────────┐
         │         Django REST Framework                │
         │                                              │
         │  ┌─────────────────────────────────────────┐ │
         │  │     API Layer (dj-rest-auth)            │ │
         │  │          - 회원가입 (registration)        │ │
         │  │          - 로그인 (login)                │ │
         │  │          - 로그아웃 (logout)              │ │
         │  │          - 비밀번호 변경/재설정            │ │
         │  └────────────┬────────────────────────────┘ │
         │               ▼                              │
         │  ┌─────────────────────────────────────────┐ │
         │  │   Custom Serializers & Adapters         │ │
         │  │   - CustomRegisterSerializer            │ │
         │  │   - CustomSocialAccountAdapter          │ │
         │  │   - UserConsentSerializer               │ │
         │  └────────────┬────────────────────────────┘ │
         │               ▼                              │
         │  ┌─────────────────────────────────────────┐ │
         │  │      Models & Data Layer                │ │
         │  │   - User (AbstractUser 확장)            │ │
         │  │   - UserConsent (약관 동의)              │ │
         │  │   - EmailVerification (준비)            │ │
         │  │   - Token (자동 생성)                    │ │
         │  └────────────┬────────────────────────────┘ │
         └───────────────┼────────────────────────────┘
                         ▼
              ┌───────────────────────┐
              │  PostgreSQL Database  │
              └───────────────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │   Google OAuth 2.0    │
              │   (django-allauth)    │
              └───────────────────────┘


                         [Future]
              - 이메일 인증 기능 (EmailVerification)
              - 추가 소셜 로그인 (Kakao, Naver 등)
              - 2FA (Two-Factor Authentication)
```

<br>

---

## 4. Models 구성

### 4.1 User (Custom User 모델)

Django의 AbstractUser를 상속하여 확장한 사용자 모델입니다.

```python
class User(AbstractUser):
    """
    기본 AbstractUser 필드:
    - username (사용자명)
    - password (비밀번호)
    - is_active (활성 여부)
    - is_staff (스태프 여부)
    - is_superuser (슈퍼유저 여부)
    - date_joined (가입일)
    - last_login (최근 로그인)

    추가 커스텀 필드:
    - name (이름) - 필수
    - email (이메일) - 유니크, 필수
    - is_email_verified (이메일 인증 여부) - 향후 사용

    제거된 필드:
    - first_name (사용 안 함)
    - last_name (사용 안 함)
    """
```

**설계 의도**:
- `name` 필드를 추가하여 한국 사용자 환경에 맞는 이름 관리
- `email`을 unique 제약으로 설정하여 중복 가입 방지
- `is_email_verified`를 추가하여 향후 이메일 인증 기능 확장 준비

<br>

### 4.2 UserConsent (약관 동의)

서비스 이용약관, 개인정보 처리방침, 마케팅 수신 동의 등을 저장하는 모델입니다.

```python
class UserConsent(models.Model):
    """
    필드:
    - user (User와 OneToOne 관계)
    - terms_service (서비스 이용약관 동의) - 필수
    - terms_privacy (개인정보 처리방침 동의) - 필수
    - marketing_opt_in (마케팅 수신 동의) - 선택
    - agreed_at (동의 일시)
    """
```

**설계 의도**:
- User 모델과 분리하여 약관 관련 정보를 독립적으로 관리

- OneToOne 관계로 사용자당 하나의 약관 동의 레코드 보장

- 향후 약관 버전 관리, 동의 이력 추적 등 확장 가능

  

<br>

### 4.3 EmailVerification (이메일 인증 - 준비)

회원가입 전 이메일 인증 코드를 저장하는 모델입니다. (현재 구현 미완성)

```python
class EmailVerification(models.Model):
    """
    필드:
    - email (인증 대상 이메일)
    - code_hash (인증 코드 해시)
    - expires_at (만료 시간)
    - verified_at (인증 완료 시간)
    - created_at (생성 일시)

    프로퍼티:
    - is_expired (만료 여부)
    - is_verified (인증 완료 여부)
    """
```

**설계 의도**:
- 평문 코드 대신 해시를 저장하여 보안 강화
- 만료 시간 설정으로 무한 유효한 인증 코드 방지
- 향후 이메일 인증 기능 구현 시 바로 사용 가능

<br>

<br>



## 5. API 구성

### 5.1 Endpoints

```
# 기본 인증 (dj-rest-auth 제공)
- POST  /api/v1/accounts/registration/                       - 회원가입
- POST  /api/v1/accounts/login/                             - 로그인
- POST  /api/v1/accounts/logout/                            - 로그아웃
- GET   /api/v1/accounts/user/                              - 사용자 정보 조회

# 비밀번호 관리
- POST  /api/v1/accounts/password/reset/                    - 비밀번호 재설정 요청
- POST  /api/v1/accounts/password/reset/confirm/            - 비밀번호 재설정 확인
- POST  /api/v1/accounts/mypage/profile/password/change/    - 비밀번호 변경

# 소셜 로그인
- POST  /api/v1/accounts/google/                            - Google 소셜 로그인
```

<br>

### 5.2 URL 구조

```
/api/v1/accounts/
├── registration/                  # 회원가입
├── login/                        # 로그인
├── logout/                       # 로그아웃
├── user/                         # 사용자 정보
├── password/
│   ├── reset/                   # 비밀번호 재설정 요청
│   └── reset/confirm/           # 비밀번호 재설정 확인
├── mypage/profile/password/change/  # 비밀번호 변경
└── google/                       # Google 소셜 로그인
```

<br>

<br>

## 6. Serializers 구성

```
1. 회원가입
1.1  CustomRegisterSerializer           | 회원가입 요청 검증 및 처리
1.2  UserConsentSerializer              | 약관 동의 정보 검증

2. 사용자 정보
2.1  CustomUserDetailsSerializer        | 로그인 사용자 정보 반환
```

<br>

### 6.1 CustomRegisterSerializer

**설계 의도**:
- dj-rest-auth의 기본 RegisterSerializer를 확장
- 사용자 추가 정보(name)와 약관 동의 정보를 함께 처리
- 트랜잭션으로 User 생성과 Consent 생성을 원자적으로 처리

**주요 검증 로직**:
1. username 중복 검증 (validate_username)
2. email 중복 검증 (validate_email)
3. 필수 약관 동의 검증 (validate)
   - terms_service: True 필수
   - terms_privacy: True 필수
   - marketing_opt_in: 선택

**저장 로직**:

```python
@transaction.atomic
def save(self, request):
    # 1. allauth 기본 User 생성
    user = super().save(request)

    # 2. 추가 정보 저장
    user.username = self.validated_data.get('username')
    user.name = self.validated_data.get('name')
    user.save()

    # 3. 약관 동의 저장
    consent_data = self.validated_data.get('consent')
    UserConsent.objects.update_or_create(
        user=user,
        defaults={**consent_data}
    )

    return user
```

<br>

### 6.2 UserConsentSerializer

**설계 의도**:
- 약관 동의 정보를 중첩 객체로 받아 처리
- ModelSerializer로 자동 검증 활용
- 필수/선택 필드 명확히 구분

<br>

<br>

## 7. Views 구성

```
1. Google 소셜 로그인
1.1 GoogleLogin                   | Google OAuth 2.0 로그인 처리
```

### 7.1 GoogleLogin (views.py)

**설계 의도**:
- dj-rest-auth의 SocialLoginView를 상속
- GoogleOAuth2Adapter와 OAuth2Client 사용
- 프론트엔드에서 받은 access_token으로 Google 인증 처리

**구현 방식**:
```python
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "http://localhost/api/v1/accounts/google/login/callback/"
```

**처리 흐름**:
1. 프론트엔드에서 Google 인증 후 access_token 받기
2. access_token을 POST /api/v1/accounts/google/에 전송
3. GoogleOAuth2Adapter가 토큰 검증 및 사용자 정보 가져오기
4. 기존 사용자면 로그인, 신규면 회원가입 (CustomSocialAccountAdapter 호출)
5. DRF Token 반환

<br>

<br>

## 8. Adapter 구성

### 8.1 CustomSocialAccountAdapter (adapter.py)

**설계 의도**:
- django-allauth의 DefaultSocialAccountAdapter를 확장
- Google 소셜 로그인 시 Custom User 모델의 name 필드 자동 채우기
- 소셜 계정 정보(extra_data)에서 name 정보 추출

**주요 로직**:
```python
@transaction.atomic
def save_user(self, request, sociallogin, form=None):
    # 1. allauth 기본 User 생성
    user = super().save_user(request, sociallogin, form)

    # 2. name 필드가 비어있으면 extra_data에서 채우기
    if not user.name:
        extra = sociallogin.account.extra_data or {}

        # 우선순위 1: 전체 이름
        name = (extra.get("name") or "").strip()

        # 우선순위 2: given_name + family_name
        if not name:
            given = (extra.get("given_name") or "").strip()
            family = (extra.get("family_name") or "").strip()
            name = f"{given} {family}".strip()

        user.name = name
        user.save(update_fields=["name"])

    return user
```

<br>

**Google extra_data 구조**:

```json
{
  "name": "홍길동",
  "given_name": "길동",
  "family_name": "홍",
  "email": "hong@gmail.com",
  "picture": "https://..."
}
```

<br>

<br>

## 9. Signals 구성

### 9.1 create_auth_token (signals.py)

**설계 의도**:
- User 생성 시 자동으로 DRF Token 생성
- 회원가입 즉시 API 인증 가능하도록 준비

**구현 방식**:
```python
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
```

**처리 흐름**:
1. User 모델의 post_save 시그널 수신
2. created=True (신규 생성)인 경우에만 실행
3. Token.objects.create(user=instance)로 토큰 생성

<br>

<br>

## 10. 설계 의도 및 상세 고려사항

### 10.1 트랜잭션 보장

**문제 상황**:
- User 생성은 성공했으나 UserConsent 생성 실패 시, 약관 동의 없는 사용자 생성
- 소셜 로그인 시 name 필드 보완 실패 시, DB 무결성 오류

**해결 방법**:
- `@transaction.atomic` 데코레이터 사용
- User 생성과 관련 데이터 생성을 하나의 트랜잭션으로 묶음
- 중간 실패 시 전체 롤백으로 데이터 일관성 보장

### 10.2 중복 검증 전략

**Serializer 레벨 검증 (validate_username, validate_email)**:
- DB 제약 위반 전에 선제적 검증
- 500 Internal Server Error 대신 400 Bad Request 반환
- 사용자 친화적인 에러 메시지 제공

**DB 레벨 제약 (unique=True)**:
- 동시성 상황에서 최종 방어선
- Race Condition 방지

### 10.3 소셜 로그인 name 필드 처리

**문제 상황**:
- Custom User 모델에서 name 필드가 필수 (blank=False)
- Google OAuth에서 name 정보는 제공되지만 자동 매핑되지 않음
- allauth 기본 동작만으로는 name=None으로 User 생성 시도 → 무결성 오류

**해결 방법**:
- CustomSocialAccountAdapter의 save_user 메서드 오버라이드
- extra_data에서 name 정보 추출 및 자동 설정
- 트랜잭션으로 안전성 보장

### 10.4 약관 동의 분리 저장

**설계 이유**:
- User 모델은 인증 관련 정보만 보유
- 약관 동의는 비즈니스 로직 영역으로 분리
- 향후 약관 버전 관리, 동의 이력 추적 등 확장 용이

**구현 방식**:
- UserConsent 모델 (OneToOne 관계)
- update_or_create로 멱등성 보장
- Nested Serializer로 일괄 검증

<br>

<br>

## 11. 기술적 난관 및 해결 방법

### 11.1 소셜 로그인 시 name 필드 누락 문제

**문제**:
- Google 소셜 로그인 시 name 필드가 자동으로 채워지지 않아 User 생성 실패

**시도한 방법**:
1. allauth settings에서 ACCOUNT_USER_MODEL_USERNAME_FIELD 설정 → 실패
2. Serializer에서 처리 → SocialLogin은 Serializer를 거치지 않음

**최종 해결**:
- CustomSocialAccountAdapter의 save_user 메서드 오버라이드
- extra_data에서 name 추출 및 설정
- 트랜잭션으로 안전성 보장

<br>

### 11.2 회원가입 시 약관 동의 검증

**문제**:
- dj-rest-auth의 기본 RegisterSerializer는 추가 필드 지원 안 함
- 약관 동의 정보를 별도 모델로 관리하면서 원자적 처리 필요

**시도한 방법**:
1. View에서 처리 → 비즈니스 로직과 API 로직 혼재
2. 별도 Signal로 처리 → 검증 시점 제어 어려움

**최종 해결**:
- CustomRegisterSerializer 확장
- validate 메서드에서 약관 동의 검증
- save 메서드에서 트랜잭션으로 User + Consent 생성

<br>

### 11.3 토큰 자동 생성

**문제**:
- 회원가입 후 바로 로그인 가능하려면 Token 필요
- 매번 수동으로 Token 생성하면 휴먼 에러 가능성

**해결**:
- post_save 시그널 활용
- User 생성 즉시 Token 자동 생성
- created=True 조건으로 신규 가입만 처리

<br>

<br>

## 12. 의사 결정 기록

### 12.1 dj-rest-auth vs Custom 구현

**선택**: dj-rest-auth 사용

**이유**:
- 검증된 라이브러리로 보안 취약점 최소화
- 소셜 로그인 (django-allauth) 통합 용이
- 비밀번호 재설정, 이메일 인증 등 기본 제공
- 커스터마이징 포인트 명확 (Serializer, Adapter)

**트레이드오프**:
- 학습 곡선 존재 (allauth 동작 방식 이해 필요)
- 일부 커스터마이징은 복잡할 수 있음

<br>

### 12.2 약관 동의 별도 모델 vs User 모델 내 필드

**선택**: UserConsent 별도 모델 (OneToOne)

**이유**:
- User 모델은 인증 관련 정보만 집중
- 약관 동의는 비즈니스 로직 영역
- 향후 약관 버전 관리, 동의 이력 추적 등 확장 용이
- 마이그레이션 및 스키마 변경 최소화

**트레이드오프**:
- JOIN 필요 시 쿼리 복잡도 증가 (select_related로 해결)
- OneToOne 관계 관리 필요

<br>

### 12.3 이메일 인증 즉시 구현 vs 준비만

**선택**: 모델만 준비, 기능은 향후 구현

**이유**:
- MVP 단계에서는 이메일 인증 없이도 서비스 이용 가능
- 소셜 로그인이 주요 가입 경로
- 모델 구조는 미리 준비하여 향후 마이그레이션 최소화

<br>

<br>

---

## 13. 향후 개선 방향

### 13.1 이메일 인증 기능 구현

- EmailVerification 모델 활용
- 회원가입 시 인증 이메일 발송
- 인증 코드 검증 API 추가
- is_email_verified 플래그 업데이트

### 13.2 추가 소셜 로그인

- Kakao, Naver 등 국내 주요 플랫폼 지원
- 각 플랫폼별 Adapter 구현
- extra_data 필드 매핑 정의

### 13.3 보안 강화

- 2FA (Two-Factor Authentication) 추가
- 비밀번호 복잡도 정책 강화
- 로그인 실패 횟수 제한
- IP 기반 접근 제어

### 13.4 사용자 경험 개선

- 비밀번호 찾기 플로우 개선 (이메일 인증)
- 회원가입 시 중복 확인 API 추가 (실시간 검증)
- 소셜 로그인 후 추가 정보 입력 단계 추가

### 13.5 관리자 기능

- Django Admin 커스터마이징
- 사용자 관리 대시보드
- 약관 동의 이력 조회
- 일괄 처리 기능 (탈퇴, 정지 등)

<br>

<br>

# TODO
가장 최근 커밋된 장고 커맨드 내용은 반영하지 못했습니다.