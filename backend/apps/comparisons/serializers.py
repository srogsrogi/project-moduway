# apps/comparisons/serializers.py

"""
# 개요

0. 사용자 입력 검증
0.1  UserPreferencesSerializer             | 사용자 선호도 입력 검증

1. 실시간 AI 코멘트
1.1  PersonalizedCommentSerializer        | AI 맞춤 코멘트 응답 직렬화
1.2.1  ReviewContentSerializer            | 리뷰 요약 응답 직렬화 (1.2 간단)
1.2.2  ReviewSummarySerializer            | 리뷰 요약 응답 직렬화 (1.2 상세)

2. 강좌 관련
2.1  SimpleCourseSerializer                |  강좌 비교 분석 결과에서 강좌 기본 정보 제공

3. AI 평가 관련
3.1 CourseAIReviewSerializer               | LLM이 기생성한 강좌 평가 정보 제공
3.2 CourseAIReviewDetailSerializer         | 특정 강좌의 AI 평가 상세 조회용

4. 부가 Serializer
4.1  SentimentResultSerializer             | 감성분석 결과 직렬화
4.2  TimelineResultSerializer              | 타임라인 시뮬레이션 결과 직렬화

5. 강좌 비교 분석 Request/Response
5.1  ComparisonAnalyzeRequestSerializer    | 강좌 비교 분석 요청 검증
5.2  ComparisonResultSerializer            | 강좌별 비교 분석 결과 직렬화
5.3  ComparisonAnalyzeResponseSerializer   | 강좌 비교 분석 최종 응답 직렬화


[참고사항]
- 서비스는 4개가 있음.
  - SentimentService | CourseReview 텍스트를 긍정 비율 /리뷰 수/신뢰도로 분석
  - TimelineService | course_playtime, week, study_end + weekly_hours(input)으로 "적정 / 널널 / 빠듯 / 종료 / 판정불가" 산출
  - ScoreService | theory/pracical/difficulty/duration 점수와 user_preferences(input)로 매칭 점수 산출 (유클리드 거리 기반)
  - LLMService | LLM 프롬프트 호출 담당
  - 서비스 패키지는 get_xxx_service() 함수로 인스턴스화하여 사용(싱글톤 진입점으로 export)
- 서비스는 비즈니스 로직만 담당, 입출력 데이터 직렬화는 serializers에서 담당
- API 초안은 POST /api/v1/comparisons/analyze/에 course_ids, weekly_hours, user_preferences(theory, practical, difficulty, duration)을 받아와서
  각 강좌별로 id, name, org_name, professor, course_image, url, study_end + ai_review + match_score + sentiment +timeline을 응답하는 형태

[설계 의도]
- Comparisons API의 요청/응답 데이터 직렬화
- 입력 검증 및 안전한 데이터 변환 담당

[상세 고려 사항]
- mypage 앱의 스타일과 호환 (상세 주석, 검증 로직)
- 중첩 Serializer 활용하여 관련 데이터 함께 제공
- read_only 필드와 입력 필드 명확히 구분
"""

from rest_framework import serializers
from apps.courses.models import Course
from apps.comparisons.models import CourseAIReview

MIN_COURSE_COMPARISON_COUNT = 1  # 최소 비교 강좌 수
MAX_COURSE_COMPARISON_COUNT = 3  # 최대 비교 강좌 수

MIN_WEEKLY_HOURS = 1    # 최소 주당 학습 시간
MAX_WEEKLY_HOURS = 168  # 최대 주당 학습 시간 (24*7)

MIN_VALUE = 0 # 평가 결정 요인 -> 사용자가 평가한 중요도 최소값
MAX_VALUE = 5 # 평가 결정 요인 -> 사용자가 평가한 중요도 최대값

USER_GOAL_MIN_LENGTH = 10   # 사용자 학습 목표 최소 길이
USER_GOAL_MAX_LENGTH = 1000  # 사용자 학습 목표 최대 길이

# =========================
# 0. 사용자 입력 검증
# =========================

# 0.1 UserPreferencesSerializer | 사용자 선호도 입력 검증
class UserPreferencesSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 사용자 선호도 입력 검증
    - 각 항목은 0~5 범위로 제한

    [상세 고려 사항]
    - 모든 필드 필수 입력
    - 범위 검증 (0-5)
    - #NOTE 정수로 설계 (IntegerField)
    """
    # 사용자가 원하는 이론적 깊이, 실무 활용도, 학습 난이도, 학습 기간 선호도
    theory = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        help_text="이론적 깊이 선호도 (0: 얕음, 5: 깊음)"
    )
    practical = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        help_text="실무 활용도 선호도 (0: 낮음, 5: 높음)"
    )
    difficulty = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        help_text="학습 난이도 선호도 (0: 쉬움, 5: 어려움)"
    )
    duration = serializers.IntegerField(
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        help_text="학습 기간 선호도 (0: 짧음, 5: 김)"
    )


# =========================
# 1. 실시간 AI 코멘트
# =========================

# 1.1 PersonalizedCommentSerializer | AI 맞춤 코멘트 응답 직렬화
class PersonalizedCommentSerializer(serializers.Serializer):
    """
    [설계 의도]
    - LLM이 생성한 개인화 추천 코멘트 응답 구조화
    - 강좌명, 추천 이유, 핵심 포인트를 명확히 구분하여 UI 렌더링 용이

    [상세 고려 사항]
    - LLM 생성 데이터이므로 모든 필드 read_only
    - 프론트엔드에서 추가 가공 없이 바로 표시 가능
    """
    course_id = serializers.IntegerField( # 어떤 강좌에 대한 코멘트인가 확인하기 위함.
        read_only=True, 
        help_text="강좌 ID")

    course_name = serializers.CharField(
        read_only=True,
        help_text="강좌명"
    )

    recommendation_reason = serializers.CharField(
        read_only=True,
        help_text="개인화된 추천 이유 (3-4문장)"
    )

    key_points = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="핵심 포인트 리스트 (2-4개)"
    )
    # 혹시나 LLM이 INT로 안 줄까봐 예외처리
    def to_representation(self, instance):  # serializer가 응답을 dict로 변환할 때 호출되는 훅
        """출력 시점에 course_id를 안전하게 int로 변환""" 
        ret = super().to_representation(instance)  # 기본 직렬화 결과(dict)를 먼저 만든다
        if 'course_id' in ret and ret['course_id'] is not None:  # course_id가 있고 None이 아니면 변환 시도
            try:
                ret['course_id'] = int(ret['course_id'])  # 문자열 숫자("12") 같은 값도 int로 강제 변환
            except (ValueError, TypeError):  # 숫자 변환이 안 되는 값/타입이면
                ret['course_id'] = None  # 안전하게 None 처리(프론트에서 예외 덜 나게)
        return ret  # 최종 응답 dict 반환

# 1.2.1 ReviewContentSerializer | 리뷰 요약 응답 직렬화
class ReviewContentSerializer(serializers.Serializer): 
    """
    [설계 의도]
    #NOTE 리뷰 요약 본문" 만 담당하는 0.4 Serializer의 하위 구조!!

    [상세 고려 사항]
    - summary: 리뷰가 없으면 "리뷰가 없어서 요약을 제공할 수 없습니다" 메시지
    - pros and cons : 장점과 단점 제공.
    """
    summary = serializers.CharField(
        read_only=True,
        help_text="리뷰 요약 (3-4문장) 또는 안내 메시지"
    )
    pros = serializers.ListField(
        child=serializers.CharField(), # 각 장점은 문자열.
        read_only=True,
        help_text="리뷰 장점 리스트 (2-4개)"
    )
    cons = serializers.ListField(
        child=serializers.CharField(), # 각 단점은 문자열.
        read_only=True,
        help_text="리뷰 단점 리스트 (2-4개)"
    )

    
# 1.2.2 ReviewSummarySerializer | 리뷰 요약 응답 직렬화
class ReviewSummarySerializer(serializers.Serializer):
    """
    [설계 의도]
    #NOTE 리뷰 요약 전체 구조 담당!!
    - 리뷰 요약 + 메타정보(리뷰 개수 + 신뢰도 + 경고 메시지) 포함하는 0.3 Serializer의 상위 구조!!

    [상세 고려 사항]
    - review_summary: ReviewContentSerializer로 계층 구조 반영
    - warning_message: 리뷰가 적으면 "리뷰가 적어 신뢰도가 낮을 수 있습니다" 경고
    - 리뷰 개수, 신뢰도, 경고 메시지를 함께 제공하여 사용자가 정보 신뢰성 판단 가능
    """
    course_id = serializers.IntegerField(read_only=True) # 어떤 강좌에 대핞 리뷰 요약인지 확인하기 위함. 

    review_summary = ReviewContentSerializer(read_only=True) # 계층 구조로 제공!!

    review_count = serializers.IntegerField(
        read_only=True,
        help_text="전체 리뷰 개수"
    )

    reliability = serializers.CharField(
        read_only=True,
        help_text="신뢰도 (high | low)"
    )

    warning_message = serializers.CharField(
        read_only=True,
        allow_null=True,
        help_text="경고 메시지 (리뷰가 적거나 없는 경우)"
    )


# =========================
# 2. 강좌 관련 Serializer
# =========================

# 2.1 SimpleCourseSerializer | 강좌 비교 분석 결과에서 강좌 기본 정보 제공
class SimpleCourseSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 비교 분석 결과에서 강좌 기본 정보 제공
    - mypage.serializers.SimpleCourseSerializer와 동일한 구조
    - 강좌 카드 렌더링에 필요한 최소 정보만 포함 
    #NOTE 우선은 apps 간 의존성 최소화 차원에서 별도 정의

    [상세 고려 사항]
    - Payload 최소화 (필요한 필드만)
    - 모든 필드 read_only (조회 전용)
    """

    class Meta:
        model = Course
        fields = (
            'id',                  # 강좌 ID
            'name',                # 강좌명
            'professor',           # 교수자
            'org_name',            # 운영 기관
            'course_image',        # 썸네일 이미지
            'url',                 # 강좌 URL
            'study_end',           # 수강 종료일
            'week',                # 총 주차
            'course_playtime'      # 총 학습 시간
        )
        read_only_fields = fields


# =========================
# 3. AI 평가 관련 Serializer
# =========================

# 3.1 CourseAIReviewSerializer | LLM이 기생성한 강좌 평가 정보 제공
class CourseAIReviewSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - LLM이 생성한 강좌 평가 정보 제공
    - #NOTE 미리 산출해낸 AI 평가 데이터를 DB에서 조회하여 직렬화
      - 강의 정보는 자주 변경되지 않으므로 별도 API 호출 없이 재사용 가능하다고 생각함.
      - 다만, 일정 기간 후 재생성 필요 시점이 올 수 있음(모델 업데이트, 프롬프트 개선 등) 
      #TODO 추후 정책 수립과 파이프라인 설계 필요
    - 강좌 비교 분석 및 강좌 상세 페이지에서 재사용

    [상세 고려 사항]
    - course 필드는 제외 (중복 방지)
    - 모든 필드 read_only (LLM 생성 데이터)
    """

    class Meta:
        model = CourseAIReview
        fields = (
            'course_summary',      # LLM 생성 요약
            'average_rating',      # 종합 평점
            'theory_rating',       # 이론적 깊이
            'practical_rating',    # 실무 활용도
            'difficulty_rating',   # 학습 난이도
            'duration_rating',     # 학습 기간
            'model_version',       # 사용된 모델
            'prompt_version',      # 프롬프트 버전
            'updated_at'           # 업데이트 시각
        )
        read_only_fields = fields

# 3.2 CourseAIReviewDetailSerializer | 특정 강좌의 AI 평가 상세 조회용 -> GET /api/v1/comparisons/courses/{course_id}/ai-review/
class CourseAIReviewDetailSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 특정 강좌의 AI 평가 상세 조회용
    - course_id 포함하여 어떤 강좌인지 명시

    [사용처]
    - GET /api/v1/comparisons/courses/{course_id}/ai-review/
    """

    course_id = serializers.IntegerField(source='course.id', read_only=True)

    class Meta:
        model = CourseAIReview
        fields = ( # 사실 model의 모든 필드 포함
            'course_id',                  # 강좌 ID
            'course_summary',             # LLM 생성 요약
            'average_rating',             # 종합 평점 # NOTE 평균 내리고 소수점 2자리까지 반올림
            'theory_rating',              # 이론적 깊이
            'practical_rating',           # 실무 활용도
            'difficulty_rating',          # 학습 난이도
            'duration_rating',            # 학습 기간    
            'model_version',              # 사용된 모델 (예시 : gpt-4o-mini)
            'prompt_version',             # 프롬프트 버전 -> 추후 개선 이력 관리용
            'created_at',                 # 생성 시각
            'updated_at'                  #  업데이트 시각
        )
        read_only_fields = fields


# =========================
# 4. 부가 Serializer
# =========================

# 4.1 SentimentResultSerializer | 감성분석 결과 직렬화
class SentimentResultSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 감성분석 결과 직렬화
    - SentimentService에서 계산한 데이터를 구조화

    [상세 고려 사항]
    - 모델에 매핑되지 않는 계산 데이터이므로 Serializer 사용
    - read_only로 출력 전용
    """

    positive_ratio = serializers.FloatField(
        read_only=True,
        help_text="긍정 리뷰 비율 (%)"
    )
    review_count = serializers.IntegerField(
        read_only=True,
        help_text="총 리뷰 개수"
    )
    # NOTE 신뢰도는 'high' | 'low' 문자열로 표현, 추후 INT 등급으로 변경 검토 가능
    reliability = serializers.CharField(
        read_only=True,
        help_text="신뢰도 (high | low)"
    )

# 4.2 TimelineResultSerializer | 타임라인 시뮬레이션 결과 직렬화
class TimelineResultSerializer(serializers.Serializer):
    """
    [설계 의도]
    - "내가 이 강의 완강할 수 있을까?" 타임라인 시뮬레이션 결과 직렬화
    - TimelineService에서 계산한 데이터를 구조화

    [상세 고려 사항]
    - 계산 데이터이므로 Serializer 사용
    - read_only로 출력 전용
    """

    min_hours_per_week = serializers.IntegerField(
        read_only=True,
        help_text="주당 필요 학습 시간"
    )
    total_weeks = serializers.IntegerField(
        read_only=True,
        help_text="총 학습 주차"
    )
    remaining_weeks = serializers.IntegerField(
        read_only=True,
        help_text="남은 주차"
    )
    status = serializers.CharField(
        read_only=True,
        help_text="학습 강도 (적정 | 널널 | 빠듯 | 종료)" # Threshold 기준은 우선 0.8, 1.2 -> TimelineService 참고
    )
    ratio = serializers.FloatField(
        read_only=True,
        help_text="필요시간/가능시간 비율"
    )
    
# =========================
# 5. 강좌 비교 분석 Request/Response
# =========================

# 5.1 ComparisonAnalyzeRequestSerializer | 강좌 비교 분석 요청 검증
class ComparisonAnalyzeRequestSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 강좌 비교 분석 요청 검증
    - POST /api/v1/comparisons/analyze/ 의 request body 처리

    [상세 고려 사항]
    - course_ids: 최소 1개, 최대 3개 제한
    - weekly_hours: 1~168 (주당 최대 시간)
    - user_preferences: 중첩 Serializer로 검증
    - user_goal: 사용자 학습목적, 길이 제한(USER_GOAL_MIN_LENGTH ~ USER_GOAL_MAX_LENGTH)
    """

    course_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=MIN_COURSE_COMPARISON_COUNT,
        max_length=MAX_COURSE_COMPARISON_COUNT,
        help_text="비교할 강좌 ID 리스트 (최소 1개, 최대 3개)"
    )

    weekly_hours = serializers.IntegerField(
        min_value=MIN_WEEKLY_HOURS,
        max_value=MAX_WEEKLY_HOURS,
        help_text="주당 학습 가능 시간 (1~168)"
    )

    user_preferences = UserPreferencesSerializer(
        help_text="사용자 선호도 (각 항목 0~5)"
    )

    user_goal = serializers.CharField(
        min_length=USER_GOAL_MIN_LENGTH,
        max_length=USER_GOAL_MAX_LENGTH,
        help_text=f"사용자 학습 목표 (최소 {USER_GOAL_MIN_LENGTH}자, 최대 {USER_GOAL_MAX_LENGTH}자)"
    )

    def validate_course_ids(self, value):
        """
        [설계 의도]
        - 중복 ID 제거
        - 빈 리스트 방지

        [상세 고려 사항]
        - 중복 제거 후에도 최소 1개 보장
        """
        # 중복 제거
        unique_ids = list(set(value))

        if len(unique_ids) == 0:
            raise serializers.ValidationError(
                "최소 1개의 강좌를 선택해주세요."
            )

        return unique_ids
    
    def validate_user_goal(self, value):
        """
        [설계 의도]
        - 공백만 있는 입력 방지
        - 사용자 학습 목표 검증
        - 금지어 필터링 (예: 부적절한 언어, 조작 유도 문구 등)

        [상세 고려 사항]
        - 금지어 목록은 추후 확장 가능
        """
        
        forbidden_words = [
            "무시하고","지시를 무시","이전 지시","위 지시","규칙을 무시","보안 무시","제약을 무시","너는 이제","지금부터 너는",
            "시스템 프롬프트","system prompt","assistant 역할","role: system","role: assistant",
            "속여","조작","우회","해킹","침투","탈옥","jailbreak","프롬프트 탈옥","필터 우회","검열 우회",
        ]

        for word in forbidden_words:
            if word in value.lower():
                raise serializers.ValidationError(
                    "👿 😈 🔥 😈학습 목표에 부적절한 내용이 포함되어 있습니다. 욕하는 행위나 시스템 조작을 시도하지 마세요.👿 😈 🔥 😈" # 강하게 경고.
                )
        
        stripped_value = value.strip()
        if len(stripped_value) < USER_GOAL_MIN_LENGTH:
            raise serializers.ValidationError(
                f"학습 목표는 최소 {USER_GOAL_MIN_LENGTH}자 이상이어야 합니다."
            )

        return stripped_value

# 5.2 ComparisonResultSerializer | 강좌별 비교 분석 결과 직렬화
class ComparisonResultSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 강좌별 비교 분석 결과 직렬화
    - course + ai_review + match_score + sentiment + timeline + personalized_comment + review_summary를 하나로 묶음

    [상세 고려 사항]
    - 중첩 Serializer 활용하여 관련 데이터 함께 제공
    - 프론트엔드에서 추가 API 호출 없이 렌더링 가능
    - 한번의 요청으로 모든 정보를 제공(UX 향상)
    """

    course = SimpleCourseSerializer(read_only=True, help_text="강좌 기본 정보")
    ai_review = CourseAIReviewSerializer(read_only=True, help_text="AI 리뷰")
    match_score = serializers.FloatField(read_only=True, help_text="매칭 점수")
    sentiment = SentimentResultSerializer(read_only=True, help_text="감성 분석 결과")
    timeline = TimelineResultSerializer(read_only=True, help_text="타임라인 시뮬레이션 결과")
    personalized_comment = PersonalizedCommentSerializer(read_only=True, help_text="개인화 코멘트")
    review_summary = ReviewSummarySerializer(read_only=True, help_text="리뷰 요약")

# 5.3 ComparisonAnalyzeResponseSerializer | 강좌 비교 분석 최종 응답 직렬화
class ComparisonAnalyzeResponseSerializer(serializers.Serializer):
    """
    [설계 의도]
    - 강좌 비교 분석 최종 응답 직렬화
    - results 리스트로 여러 강좌 결과 포함
    """

    results = ComparisonResultSerializer(
        many=True,
        read_only=True,
        help_text="비교 분석 결과 리스트 (매칭 점수 내림차순)"
    )




