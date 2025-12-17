# backend/apps/accounts/serializers.py

from django.db import transaction
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import User, UserConsent

class UserConsentSerializer(serializers.ModelSerializer):
    """
    [ 설계 의도 ]
    - 회원가입 시점에 클라이언트로부터 약관 동의 상태를
      객체(Nested JSON) 형태로 전달받아 함께 저장하기 위함.

    [ 상세 고려 사항 ]
    - 필수 여부 명시:
      extra_kwargs를 통해 API 스펙 상 반드시 포함되어야 할 필드를 명확히 정의.
    - 데이터 일관성 확보:
      ModelSerializer를 사용하여 UserConsent 모델의 Boolean 필드 타입과
      Serializer 검증 로직을 자동으로 동기화.
    - 책임 분리:
      약관 동의 관련 검증 및 직렬화 책임을 UserSerializer로부터 분리하여
      회원가입 로직의 복잡도 감소.
    """
    class Meta:
        model = UserConsent
        fields = ['terms_service', 'terms_privacy', 'marketing_opt_in']
        extra_kwargs = {
            'terms_service': {'required': True},     # 필수: 서비스 이용약관
            'terms_privacy': {'required': True},     # 필수: 개인정보 처리방침
            'marketing_opt_in': {'required': False}, # 선택: 마케팅 정보 수신
        }

class CustomRegisterSerializer(RegisterSerializer):
    """
    [ 설계 의도 ]
    - dj-rest-auth의 기본 회원가입 플로우에
      '추가 사용자 정보 저장' 및 '약관 동의 기록' 단계를 결합한 확장 Serializer.

    [ 주요 설계 포인트 ]
    1. 원자성 보장 (Atomicity):
       - @transaction.atomic을 사용하여
         유저 생성(Auth)과 약관 동의 저장(DB)을 하나의 트랜잭션으로 묶음.
       - 약관 저장 중 오류 발생 시, 생성된 유저 계정도 함께 롤백되어
         인증 데이터와 비즈니스 데이터 간 불일치 방지.

    2. 데이터 검증 책임 명확화 (Validation Layer 강화):
       - 기본 required=True 검증은 '키 존재 여부'만 확인하므로,
         validate()를 오버라이딩하여
         실제 비즈니스 규칙(필수 약관 True 여부)을 추가 검증.
       - 필드 단위 에러 메시지를 반환하여
         프론트엔드에서 사용자 피드백 처리 용이.

    3. 확장성을 고려한 데이터 매핑:
       - consent 데이터 저장 시 defaults={**consent_data} 패턴 사용.
       - UserConsent 모델 필드가 확장되더라도
         Serializer save 로직 수정 최소화.

    4. 안전한 레코드 생성 전략:
       - update_or_create() 사용으로
         중복 요청, 재시도, 동시성 상황에서 발생할 수 있는
         IntegrityError 리스크 완화.
    """
    username = serializers.CharField(max_length=150, required=True)
    name = serializers.CharField(max_length=30, required=True)
    consent = UserConsentSerializer(write_only=True, required=True)

    def validate_username(self, value):
        """
        username 중복 검증
        - DB UNIQUE 제약조건 이전 단계에서 선제적으로 검증하여
          500 에러 대신 400 ValidationError 반환.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        """
        email 중복 검증
        - 회원가입 단계에서 이메일 유니크성 보장.
        - DB 레벨 에러 대신 사용자 친화적인 에러 메시지 제공 목적.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        """
        객체 단위 추가 검증 로직
        - 기본 회원가입 검증(password, email 형식 등)은 부모 클래스에 위임.
        - 약관 동의와 같이 여러 필드를 함께 판단해야 하는
          비즈니스 규칙은 이 단계에서 처리.
        """

        # 1. 부모 클래스의 기본 검증(ID/PW 규칙 등) 수행
        attrs = super().validate(attrs)
        consent = attrs.get('consent', {})
        
        # 2. 필수 동의 항목의 실제 논리값 검증 (True 여부)
        errors = {}
        if not consent.get('terms_service'):
            errors['terms_service'] = "서비스 이용약관 동의는 필수입니다."
        if not consent.get('terms_privacy'):
            errors['terms_privacy'] = "개인정보 처리방침 동의는 필수입니다."
        
        if errors:
            raise serializers.ValidationError({"consent": errors})
            
        return attrs

    @transaction.atomic
    def save(self, request):
        """
        회원가입 최종 처리 단계
        - allauth 기반 유저 생성 (이메일 인증, 시그널 트리거 포함)
        - 추가 사용자 정보 및 약관 동의 데이터 저장
        """

        # 1. 기본 회원가입 처리 (User 생성 및 저장)
        user = super().save(request)

        # 2. 서비스 도메인에서 사용하는 추가 사용자 정보 저장
        user.username = self.validated_data.get('username')
        user.name = self.validated_data.get('name')
        user.save()

        # 3. 검증 완료된 약관 동의 데이터 저장
        # validated_data는 Serializer 검증을 통과한 신뢰 가능한 데이터
        consent_data = self.validated_data.get('consent')

        UserConsent.objects.update_or_create(
            user=user,
            defaults={**consent_data}
        )

        return user

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    """
    [ 설계 의도 ]
    - 인증된 사용자에게 반환할 최소한의 프로필 정보 정의.

    [ 고려 사항 ]
    - 비밀번호, 권한 정보 등 보안상 민감한 필드는 노출 금지.
    - 프론트엔드 UI 및 상태 관리에 필요한 정보만 선별 제공.
    """
    class Meta:
        model = User
        fields = ('pk', 'username', 'email')