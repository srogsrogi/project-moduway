# backend/apps/comparisons/services/llm_service.py


# 개요
"""
Comparisons 앱에서 LLM(현재는 GMS API)을 호출하여 "맞춤 코멘트"와 "리뷰 요약"을 생성하는 서비스 모듈
- __init__()                                                     | GMS API 키 검증.
- generate_personalized_comment(course, ai_review, user_goal)    | 개인화 코멘트 생성
- generate_review_summary(course_id)                             | 리뷰 요약 생성 # courses 앱에서 재사용 가능하도록 설계함'!!
- _call_gms_api(messages, temperature, max_tokens)               | 공통 LLM 호출 로직
"""

"""
[설계 의도]
- LLM을 활용한 즉시 생성 기능 제공
  1. AI 맞춤 코멘트: 사용자 학습 목적에 맞춘 개인화 추천 이유
  2. 리뷰 요약: 실제 수강생 리뷰 기반 강좌 핵심 정보 요약
- View/Serializer에서 LLM 호출 로직을 분리하여 재사용성 및 테스트 용이성 확보

[상세 고려 사항]
- GMS API를 통한 OpenAI GPT-4o-mini 모델 사용
- JSON 모드 활성화로 구조화된 응답 보장
- timeout, 재시도, 에러 처리로 외부 API 호출 안정성 확보
- 리뷰 요약은 courses 앱에서도 재사용 가능하도록 독립적으로 설계

[의사결정 배경]
- #TODO generate_review_summary의 경우, MVP에서는 comparisons/services/에 구현하고 추후 공통 모듈로 리팩토링하고자 함.
- 재사용성을 고려하여 각 메서드는 최소한의 인자만 받도록 설계
"""

import os
import json
import requests
from typing import Dict, List
from django.db.models import Q # Q가 있어야 복잡한 쿼리 연산이 가능해짐!
from apps.courses.models import CourseReview
from apps.comparisons.models import CourseAIReview
from apps.courses.models import Course

# =========================
# LLM 설정 상수
# -하드코딩은 지양함.
# =========================

LLM_MODEL_NAME = 'gpt-4o-mini'  # 사용할 LLM 모델 버전
LLM_TEMPERATURE_CREATIVE = 0.6  # 코멘트 생성용 (창의성 조금 필요)
LLM_TEMPERATURE_FACTUAL = 0.3   # 요약용 (일관성 조금 더 중요)
LLM_MAX_TOKENS = 500            # 최대 토큰 수
LLM_TIMEOUT = 30                # API 호출 타임아웃 (초)

# =========================
# 리뷰 요약 정책 상수
# =========================
REVIEW_SUMMARY_MIN_REVIEWS_FOR_HIGH_RELIABILITY = 5  # 높은 신뢰도 기준 최소 리뷰 수 | 5개 미만이면, 신뢰도가 낮다고 UI에 알려줌.
REVIEW_SUMMARY_MAX_REVIEWS_TO_PROCESS = 30           # 요약할 최대 리뷰 수 (#NOTE 비용 절감)
REVIEW_MIN_LENGTH = 10                               # 유효한 리뷰로 인정할 최소 길이

# =========================
# 코멘트 생성 정책 상수
# =========================
COMMENT_MIN_KEY_POINTS = 2  # 최소 핵심 포인트 개수
COMMENT_MAX_KEY_POINTS = 5  # 최대 핵심 포인트 개수


class LLMService:
    """
    LLM 기반 즉시 생성 기능을 담당하는 서비스 레이어

    [설계 의도]
    - 외부 LLM API 호출 로직을 캡슐화
    - View에서는 간단한 메서드 호출만으로 LLM 기능 사용
    - 프롬프트 엔지니어링, 에러 처리, 응답 파싱을 서비스 내부에서 완결

    [상세 고려 사항]
    - 싱글톤 패턴으로 관리 (불필요한 인스턴스 생성 방지)
    - 메서드별 책임 명확히 분리 (SRP 원칙)
    - 외부 API 실패 시 graceful degradation 전략 적용
    """

    def __init__(self):
        """
        [설계 의도]
        - GMS API 설정을 초기화 시점에 검증
        - 환경변수 누락 시 명확한 에러 메시지 제공

        [상세 고려 사항]
        - GMS_KEY는 환경변수에서 주입 (보안)
        - API URL은 상수로 정의 (향후 변경 가능성 고려)
        """
        self.gms_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
        self.gms_key = os.environ.get("GMS_KEY")

        # 키 없으면 미리 시패 처리함.
        if not self.gms_key:
            raise ValueError(
                "GMS_KEY 환경변수가 설정되지 않았습니다. "
                "LLM 기능을 사용하려면 환경변수를 설정해주세요."
            )

    # =========================
    # 기능 1: AI 맞춤 코멘트 생성
    # 사용자의 목표 + 강좌 정보 + 사전 AI 평가를 이용하여 개인화된 추천 코멘트 생성
    # =========================

    def generate_personalized_comment(
        self,
        course: Course,
        ai_review: CourseAIReview,
        user_goal: str
    ) -> Dict:
        """
        사용자 학습 목적에 맞춘 개인화된 강좌 추천 코멘트 생성

        [설계 의도]
        - 사용자의 학습 목적과 강좌 특성을 매칭하여 설득력 있는 추천 이유 제공
        - 강좌명, 추천 이유, 핵심 포인트를 구조화하여 프론트엔드에서 활용 용이

        [상세 고려 사항]
        - user_goal: 사용자가 입력한 학습 목적 (예: "비전공자이지만 데이터 분석가로 이직하고 싶습니다")
        - ai_review: DB에 미리 저장된 강좌 AI 평가 (이론/실무/난이도/기간 점수)
        - course: 강좌 기본 정보 (이름, 교수자, 분류 등)

        Args:
            course: Course 인스턴스
            ai_review: CourseAIReview 인스턴스
            user_goal: 사용자 학습 목적 텍스트

        Returns:
            dict: {
                'course_name': str,           # 강좌명
                'recommendation_reason': str,  # 추천 이유 (3-4문장)
                'key_points': List[str]        # 핵심 포인트 (2-4개)
            }

        Raises:
            Exception: LLM API 호출 실패 시
        """
        # 1. 프롬프트 생성
        system_prompt = f"""
당신은 온라인 강좌 추천 전문가입니다.
사용자의 학습 목적과 강좌의 특성을 분석하여, 해당 강좌를 추천하는 개인화된 코멘트를 작성해야 합니다.

**작성 규칙**:
1. 사용자의 학습 목적을 면밀히 분석하여 그에 맞는 추천 이유를 제시
2. 강좌의 이론적 깊이, 실무 활용도, 난이도, 학습 기간 등을 고려
3. 추천 이유는 3-4문장으로 구체적이고 설득력 있게 작성
4. 핵심 포인트는 {COMMENT_MIN_KEY_POINTS}~{COMMENT_MAX_KEY_POINTS}개로 간결하게 정리
5. 반드시 JSON 형식으로만 응답

**응답 형식**:
{{
  "course_id": {course.id},
  "course_name": "강좌명",
  "recommendation_reason": "이 강좌는... (3-4문장)",
  "key_points": ["포인트1", "포인트2", "포인트3"]
}}
"""

        user_prompt = f"""
**사용자의 학습 목적**:
{user_goal}

**강좌 정보**:
- 강좌 ID: {course.id}
- 강좌명: {course.name}
- 교수자: {course.professor or 'N/A'}
- 운영기관: {course.org_name or 'N/A'}
- 분류: {course.classfy_name} > {course.middle_classfy_name}
- 총 주차: {course.week or 'N/A'}주

**AI 평가**:
- 이론적 깊이: {ai_review.theory_rating}/5.0
- 실무 활용도: {ai_review.practical_rating}/5.0
- 학습 난이도: {ai_review.difficulty_rating}/5.0
- 학습 기간: {ai_review.duration_rating}/5.0
- 강좌 요약: {ai_review.course_summary}

위 정보를 바탕으로 사용자의 학습 목적에 맞춘 추천 코멘트를 JSON 형식으로 작성해주세요.
"""

        # 2. LLM API 호출
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response_text = self._call_gms_api(
            messages=messages,
            temperature=LLM_TEMPERATURE_CREATIVE,
            max_tokens=LLM_MAX_TOKENS
        )

        # 3. 응답 파싱 및 검증
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise Exception(f"LLM 응답 JSON 파싱 실패: {response_text}")

        # 필수 필드 검증
        required_fields = ['course_name', 'recommendation_reason', 'key_points']
        for field in required_fields:
            if field not in result:
                raise Exception(f"LLM 응답에 필수 필드 누락: {field}")

        # key_points 개수 검증
        if not isinstance(result['key_points'], list):
            raise Exception("key_points는 리스트 타입이어야 합니다")

        # 최소 개수 검증 
        if len(result['key_points']) < COMMENT_MIN_KEY_POINTS:
            raise Exception(f"key_points는 최소 {COMMENT_MIN_KEY_POINTS}개 이상이어야 합니다")

        # NOTE 최대 개수 검증은 굳이 에러까지는 안내하지 않음. 그대신 개수는 자르기. 
        if len(result['key_points']) > COMMENT_MAX_KEY_POINTS:
            result['key_points'] = result['key_points'][:COMMENT_MAX_KEY_POINTS]
        
        return result

    # =========================
    # 기능 2: 리뷰 요약 생성
    # =========================

    def generate_review_summary(self, course_id: int) -> Dict:
        """
        실제 수강생 리뷰를 기반으로 강좌 핵심 정보 요약 생성

        [설계 의도]
        - CourseReview 테이블의 review_text를 LLM으로 요약하여 핵심 피드백 추출
        - 리뷰가 없거나 적은 경우 명확한 안내 메시지 제공 (NULL 에러 방지)
        - courses 앱에서도 재사용 가능하도록 course_id만으로 독립적으로 동작

        [상세 고려 사항]
        - 리뷰 없음: "리뷰가 없어서 요약을 제공할 수 없습니다" 메시지
        - 리뷰 적음 (5개 미만): "리뷰가 적어 신뢰도가 낮을 수 있습니다" 경고 + 요약 제공
        - 리뷰 많음: 최대 30개만 선택하여 LLM 호출 비용 절감

        [의사결정 배경]
        - 옵션 A 선택: CourseReview의 review_text만 사용
        - 실제 사용자 피드백 기반으로 최신성과 신뢰성 확보

        Args:
            course_id: 강좌 ID

        Returns:
            dict: {
                'review_summary': dict,      # {summary, pros, cons} (없으면 기본 메시지 객체)
                'review_count': int,         # 전체 리뷰 개수
                'reliability': str,          # 'high' | 'low'
                'warning_message': str|None  # 경고 메시지 (있는 경우)
            }

        Raises:
            Exception: Course가 존재하지 않거나 LLM API 호출 실패 시
        """
        # 1. 강좌 존재 여부 확인
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise Exception(f"ID {course_id}에 해당하는 강좌를 찾을 수 없습니다")

        # 2. 리뷰 조회 (유효한 리뷰만)
        # - review_text가 NULL이 아니고, 최소 길이 이상인 리뷰만 선택
        # 최신순!! -> 추후 30개 선택할 때 필요함.
        reviews = CourseReview.objects.filter(
            course_id=course_id
        ).exclude(
            Q(review_text__isnull=True) | Q(review_text='')
        ).filter(
            # 최소 길이 검증 (의미 있는 리뷰만)
            review_text__regex=r'.{' + str(REVIEW_MIN_LENGTH) + ',}'
        ).values_list('review_text', flat=True
        ).order_by('-created_at')

        review_count = reviews.count()

        # 3. 리뷰 없는 경우 처리
        if review_count == 0:
            return {
                'review_summary': {
                    'summary': "리뷰가 없어서 요약을 제공할 수 없습니다",
                    'pros': [],
                    'cons': []
                },
                'review_count': 0,
                'reliability': 'low',
                'warning_message': "아직 수강생 리뷰가 등록되지 않았습니다"
            }

        # 4. 신뢰도 판정
        reliability = (
            'high' if review_count >= REVIEW_SUMMARY_MIN_REVIEWS_FOR_HIGH_RELIABILITY
            else 'low'
        )

        warning_message = None
        if review_count < REVIEW_SUMMARY_MIN_REVIEWS_FOR_HIGH_RELIABILITY:
            warning_message = f"리뷰가 {review_count}개로 적어 신뢰도가 낮을 수 있습니다"

        # 5. 리뷰 샘플링 (비용 절감)
        # - 최신 리뷰 우선 (created_at 역순 정렬)
        # - 최대 30개만 선택
        review_texts = list(reviews[:REVIEW_SUMMARY_MAX_REVIEWS_TO_PROCESS])

        # 6. 프롬프트 생성
        system_prompt = system_prompt = """
당신은 온라인 강좌 리뷰 분석 전문가입니다.
여러 수강생의 리뷰를 종합하여 강좌의 핵심 정보를 요약하십시오.

[작성 규칙]
1. 리뷰에서 공통적으로 언급되는 장점과 단점을 중심으로 분석합니다.
2. 강좌의 전반적인 만족도와 주요 특징을 객관적으로 정리합니다.
3. summary는 반드시 3~4문장으로 작성합니다.
4. pros와 cons는 각각 2~3개 항목으로 작성합니다.
5. 추측이나 과장된 표현은 사용하지 않습니다.
6. 출력은 반드시 **순수 JSON**만 반환해야 합니다.
7. JSON 외의 설명, 문장, 코드블록(```)은 절대 출력하지 마십시오.

**[응답 JSON 형식]**
{
  "review_summary": {
    "summary": "3~4문장 요약 텍스트",
    "pros": ["장점 1", "장점 2"],
    "cons": ["단점 1", "단점 2"]
  }
}
"""


        # 리뷰 텍스트를 줄바꿈으로 구분하여 하나의 문자열로 결합
        combined_reviews = "\n---\n".join(review_texts)

        user_prompt = f"""
**강좌명**: {course.name}

**수강생 리뷰** (총 {review_count}개 중 {len(review_texts)}개):
{combined_reviews}

위 리뷰들을 종합하여 강좌의 핵심 정보를 요약해주세요.
"""

        # 7. LLM API 호출
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response_text = self._call_gms_api(
            messages=messages,
            temperature=LLM_TEMPERATURE_FACTUAL,
            max_tokens=LLM_MAX_TOKENS
        )

        # 8. 응답 파싱 및 검증
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            raise Exception(f"LLM 응답 JSON 파싱 실패: {response_text}")

        # 데이터 존재 여부 및 형식 검증 # 모델에 유연하게 대응하기 위해 약간 느슨하게 검증함.
        if 'review_summary' not in result:
            raise Exception("LLM 응답에 'review_summary' 필드 누락")
        
        review_data = result.get('review_summary') or result # 최상위 키가 없을 경우도 대비
        final_summary = {
            'summary': review_data.get('summary', '리뷰 요약을 생성할 수 없습니다.'),
            'pros': review_data.get('pros', []),
            'cons': review_data.get('cons', [])
        }

        # 9. 최종 결과 구성
        return {
            'course_id': course_id,
            'review_summary': final_summary, 
            'review_count': review_count,
            'reliability': reliability,
            'warning_message': warning_message
        }

    # =========================
    # 공통 내부 메서드: GMS API 호출
    # =========================

    def _call_gms_api(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        GMS API를 통한 LLM 호출 공통 로직

        [설계 의도]
        - 중복 코드 제거 (DRY 원칙)
        - API 호출 에러 처리를 한 곳에서 관리
        - timeout, 재시도 정책 등 향후 확장 용이

        [상세 고려 사항]
        - JSON 모드 활성화로 구조화된 응답 보장
        - timeout 30초로 설정하여 무한 대기 방지 -> 수정하고 싶으면 LLM_TIMEOUT 바꾸면 됨. 
        - HTTP 상태 코드별 명확한 에러 메시지 제공

        Args:
            messages: ChatCompletion API 메시지 리스트
            temperature: 0.0-1.0 (창의성 조절)
            max_tokens: 최대 생성 토큰 수

        Returns:
            str: LLM이 생성한 텍스트 (JSON 문자열)

        Raises:
            Exception: API 호출 실패, timeout, 응답 파싱 실패 시
        """
        # 1. 요청 헤더
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.gms_key}"
        }

        # 2. 요청 바디
        data = {
            "model": LLM_MODEL_NAME,
            "messages": messages,
            "response_format": {"type": "json_object"},  # JSON 모드 활성화 # 중요!!
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 3. API 호출
        try:
            response = requests.post(
                self.gms_url,
                headers=headers,
                data=json.dumps(data),
                timeout=LLM_TIMEOUT
            )
        except requests.Timeout:
            raise Exception(
                f"GMS API 호출 시간 초과 (timeout: {LLM_TIMEOUT}초). "
                "잠시 후 다시 시도해주세요."
            )
        except requests.RequestException as e:
            raise Exception(f"GMS API 호출 중 네트워크 에러 발생: {str(e)}")

        # 4. HTTP 상태 코드 검증
        if response.status_code != 200:
            error_detail = response.text[:200]  # 에러 내용 일부만 로깅
            raise Exception(
                f"GMS API 호출 실패 (Status: {response.status_code}): {error_detail}"
            )

        # 5. 응답 파싱
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            raise Exception(f"GMS API 응답 JSON 파싱 실패: {response.text[:200]}")

        # 6. OpenAI API 응답 구조 검증
        if 'choices' not in result or len(result['choices']) == 0:
            raise Exception("GMS API 응답에 'choices' 필드가 없거나 비어있습니다")

        if 'message' not in result['choices'][0]:
            raise Exception("GMS API 응답에 'message' 필드가 없습니다")

        # 7. 생성된 텍스트 추출
        content = result['choices'][0]['message'].get('content', '')

        if not content:
            raise Exception("GMS API가 빈 응답을 반환했습니다")

        return content


# =========================
# 싱글톤 인스턴스 관리
# =========================

_llm_service_instance = None

def get_llm_service() -> LLMService:
    """
    LLMService 싱글톤 인스턴스 반환

    [설계 의도]
    - 애플리케이션 전역에서 하나의 LLMService 인스턴스 재사용
    - 불필요한 객체 생성 및 초기화 방지

    [상세 고려 사항]
    - LLMService는 상태를 가지지 않으므로 싱글톤 패턴 적합
    - 환경변수 검증은 최초 1회만 수행

    Returns:
        LLMService: 싱글톤 인스턴스
    """
    global _llm_service_instance

    if _llm_service_instance is None:
        _llm_service_instance = LLMService()

    return _llm_service_instance

