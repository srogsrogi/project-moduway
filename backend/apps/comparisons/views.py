# apps/comparisons/views.py

"""
# 개요
1. 강좌 비교 분석
1.1 ComparisonAnalyzeView      | 강좌 비교 분석 API

2. 강좌 AI 평가 조회
2.1 CourseAIReviewDetailView   | 강좌 AI 평가 조회 API

3. 리뷰 요약 생성
3.1 CourseReviewSummaryView    | 강좌 리뷰 요약 생성 API

4. 감성분석 API
4.1 CourseSentimentView        | 강좌 감성분석 조회 API

[구조]
1.1 ComparisonAnalyzeView
  1) 요청 검증 `ComparisonAnalyzeRequestSerializer` 사용
    1) `SimpleCourseSerializer` 사용 | 강좌 기본 정보(이름, 교수, 이미지)
    2) `CourseAIReviewSerializer` 사용 | LLM이 생성하고 DB에 저장된 강좌 요약 및 항목별 평점 정보
    3) `SentimentResultSerializer` 사용 | 리뷰 감성 분석 결과 (리뷰 수, 긍정 비율 등)
    4) `TimelineResultSerializer` 사용 | 예상 수강 일정 고려 (주당 필요 학습시간, 상태, 비율 등)
  2) 입력내부검증 `UserPreferenceSerializer` 사용
  3) 개별결과구성 `ComparisonResultSerializer` 사용
  4) 최종응답직렬화 `ComparisonAnalyzeResponseSerializer` 사용
2.1 CourseAIReviewDetailView
  1) 강좌 ID로 `CourseAIReview` 조회
  2) `CourseAIReviewDetailSerializer` 사용 | 강좌 AI 평가 상세 정보

[설명]
- LLM이 생성한 강좌 평가 데이터를 저장하기 위한 전용 모델
- 강좌(Course) 모델과 1:1 관계로 연결
- 강좌 요약(course_summary)은 CharField로 정의하고 max_length=1000으로 제한하여
  요약 정보의 길이를 명확히 관리
- 평가 점수는 0.0 ~ 5.0 범위의 점수 체계를 사용하며 FloatField로 저장
  - 0.0 : 매우 낮음 / 쉬움 / 짧음
  - 5.0 : 매우 높음 / 어려움 / 긺
- 모델 버전, 프롬프트 버전 등 메타데이터를 함께 저장하여 평가 생성 이력 추적 가능
- related_name='ai_review'를 설정하여 Course 모델에서 직관적인 역참조 지원
- 평가 점수 필드에 validators를 적용하여 데이터 무결성 확보
- 향후 평가 항목 추가, 메타데이터 확장 등 확장성을 고려한 구조로 설계            

[설계 의도]
- 강좌 비교를 위한 Comparisons API 엔드포인트 구현
- Services 계층을 활용하여 View에서는 요청/응답 처리만 담당하고, 비즈니스 로직은 별도로 분리

[상세 고려 사항]
- # NOTE 비로그인 사용자은 접근 불가능
  # 전역 설정 IsAuthenticated 를 따름
  # TODO: 추후 비로그인 사용자 접근 허용(AllowAny) 검토 필요
- select_related 등을 활용한 쿼리 최적화
- 클라이언트가 원인을 쉽게 파악할 수 있도록 명확한 에러 메시지 제공
# TODO
- 향후 캐싱 도입 검토
- LLM 호출을 강좌별로 병렬 처리
- Celery + asyncio 조합 검토 -> 응답 시간 단축 목적
- 프롬프트 버저닝 -> 프롬프트 변경 시점 추적 및 재생산성 확보
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from apps.courses.models import Course
from apps.comparisons.models import CourseAIReview
from apps.comparisons.serializers import (
    ComparisonAnalyzeRequestSerializer,
    ComparisonAnalyzeResponseSerializer,
    ComparisonResultSerializer,
    CourseAIReviewDetailSerializer,
    ReviewSummarySerializer,
    SentimentResultSerializer

)
from apps.comparisons.services import (
    get_sentiment_service,
    get_timeline_service,
    get_score_service,
    get_llm_service
)
import logging
logger = logging.getLogger(__name__)


# =========================
# 1. 강좌 비교 분석 API
# =========================

# 1.1 ComparisonAnalyzeView | 강좌 비교 분석 API
class ComparisonAnalyzeView(APIView):
    """
    [API]
    - POST: /api/v1/comparisons/analyze/

    [설계 의도]
    - 사용자가 선택한 강좌들을 비교 분석하여
      매칭 점수 기반 순위 제공
    - MVP 범위: DB 저장 없이 실시간 계산 후 응답

    [상세 고려 사항]
    - 인증 필요 (전역 설정 IsAuthenticated)
    # NOTE 비로그인 사용자도 체험 가능하게 할지에 대해서 -> 추후 변경 검토
    - Services 계층 활용으로 View는 조율 역할만
    - 쿼리 최적화: select_related로 N+1 방지
    - 에러 처리: 강좌 없음, AI 평가 없음 등
    """

    

    def post(self, request):
        """
        강좌 비교 분석 수행

        [처리 흐름]
        1. 요청 데이터 검증
        2. 강좌 조회 (AI 평가 포함)
        3. 각 강좌별로:
           - 매칭 점수 계산
           - 감성분석 수행
           - 타임라인 시뮬레이션
           - AI 맞춤 코멘트 생성
           - 강의 리뷰 요약 생성
        4. 매칭 점수 기준 정렬
        5. 응답 반환
        """
        # 1. 요청 데이터 검증
        request_serializer = ComparisonAnalyzeRequestSerializer(
            data=request.data
        )

        # 유효성 검사 실패 시 400 Bad Request 자동 반환
        request_serializer.is_valid(raise_exception=True)

        # 검증된 데이터 추출
        course_ids = request_serializer.validated_data['course_ids']
        weekly_hours = request_serializer.validated_data['weekly_hours']
        user_preferences = request_serializer.validated_data['user_preferences']
        user_goal = request_serializer.validated_data['user_goal']

        # 2. 강좌 조회 (AI 평가 포함)
        # select_related('ai_review'):
        # - Course → CourseAIReview(OneToOne) 조인으로 미리 로드
        # - N+1 쿼리 방지
        courses = Course.objects.filter(
            id__in=course_ids
        ).select_related('ai_review')

        # 요청한 강좌 ID와 실제 조회된 강좌 개수 비교
        found_ids = set(courses.values_list('id', flat=True))
        missing_ids = set(course_ids) - found_ids

        if missing_ids:
            # 일부 강좌가 없으면 404 반환
            return Response(
                {
                    'detail': '일부 강좌를 찾을 수 없습니다.',
                    'missing_ids': list(missing_ids)
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. 서비스 인스턴스 가져오기 (싱글톤)
        sentiment_service = get_sentiment_service()
        timeline_service = get_timeline_service()
        score_service = get_score_service()
        llm_service = get_llm_service()

        # 4. 각 강좌별 분석 수행
        results = []

        for course in courses:
            # 4-1. AI 평가 확인
            try:
                ai_review = course.ai_review
            except CourseAIReview.DoesNotExist:
                # NOTE
                # AI 평가가 없는 강좌는 스킵
                # # TODO UX관점에서 (1) 전체 실패를 하거나 (2) AI 평가 부분만 NULL로 보내서 프론트엔드에서 "평가 준비중" 표시하는 방안도 고려 가능
                continue

            # 4-2. 매칭 점수 계산
            match_score = score_service.calculate_match_score(
                ai_review=ai_review,
                user_preferences=user_preferences
            )

            # 4-3. 감성분석 수행
            sentiment_result = sentiment_service.analyze_course_reviews(
                course_id=course.id
            )

            # 4-4. 타임라인 시뮬레이션
            timeline_result = timeline_service.calculate_timeline(
                course=course,
                weekly_hours=weekly_hours
            )

            # 4-5. 맞춤 코멘트 생성
            try:
                personalized_comment = llm_service.generate_personalized_comment(
                    course=course,
                    ai_review=ai_review,
                    user_goal=user_goal,
                )
            # LLM 호출 과정에서 발생할 수 있는 모든 예외를 포괄적으로 처리
            # 네트워크 오류, 타임아웃, API 제한 초과, JSON 파싱 오류 등
            except Exception as e: 
                # LLM 호출 실패 시 로그로 기록하여 추후 디버깅/모니터링 가능하게 함.
                logger.warning(
                    f'리뷰 요약 생성 실패 (Course {course.id}): {str(e)}',
                    # 어떤 강좌에서 실패했는지 + 예외 메시지를 함께 기록
                    exc_info=True # trackbqack까지 로그에 남김.
                )
                # LLM 호출 실패 시데오 API응답 구조를 깨뜨리지 않기 위한 gracefull  fallback 처리
                # 전체 요청을 실패시키지 않고 안내 메시지 제공
                personalized_comment = {
                    'course_id': course.id,
                    # 실패했더라도 UI에서 강좌 이름은 보여줄 수 있도록 함.
                    'course_name': course.name,
                    # 사용자에게 안내 메시지 제공
                    'recommendation_reason': '현재 개인화 추천을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.',
                    # 빈 리스트만 제공.
                    'key_points': []
                }

                
            # 4-6. 리뷰 요약 생성
            try:
                review_summary = llm_service.generate_review_summary(
                    course_id=course.id
                )
            except Exception as e:
                # LLM 호출 실패 시 로그로 기록
                logger.warning(
                    f'리뷰 요약 생성 실패 (Course {course.id}): {str(e)}',
                    exc_info=True
                )
                # gracefull fallback 처리
                review_summary = {
                    'course_id': course.id,
                    'course_name': course.name,
                    'review_summary': {  
                        'summary': '현재 리뷰 요약을 생성할 수 없습니다. 잠시 후 다시 시도해주세요.',
                        'pros': [],
                        'cons': []
                    },
                    'review_count': 0,
                    'reliability': 'low',
                    'warning_message': '리뷰 요약 생성에 실패했습니다.'
                }

            # 4-7. 결과 데이터 구성
            result_data = {
                'course': course,
                'ai_review': ai_review,
                'match_score': match_score,
                'sentiment': sentiment_result,
                'timeline': timeline_result,
                'personalized_comment': personalized_comment,
                'review_summary': review_summary
            }

            results.append(result_data)

        # 5. 매칭 점수 기준 내림차순 정렬
        # 점수가 높은 강좌가 먼저 오도록
        results.sort(
            key=lambda x: x['match_score'],
            reverse=True
        )

        # 6. 응답 직렬화
        response_data = {'results': results}
        response_serializer = ComparisonAnalyzeResponseSerializer(
            response_data
        )

        # 7. 응답 반환
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )


# =========================
# 2. 강좌 AI 평가 조회 API
# =========================

# 2.1 CourseAIReviewDetailView | 강좌 AI 평가 조회 API
class CourseAIReviewDetailView(APIView):
    """
    [API]
    - GET: /api/v1/comparisons/courses/{course_id}/ai-review/

    [설계 의도]
    - 특정 강좌의 LLM 생성 평가 정보 조회
    - 강좌 상세 페이지에서 재사용 가능

    [상세 고려 사항]
    - 인증 필요 (전역 설정 IsAuthenticated)
    # NOTE 비로그인 사용자도 체험 가능하게 할지에 대해서 -> 추후 변경 검토
    - AI 평가가 없으면 404 반환
    """


    def get(self, request, course_id):
        """
        강좌 AI 평가 조회

        Args:
            course_id: URL path에서 전달된 강좌 ID

        Returns:
            200: AI 평가 정보
            404: 강좌 없음 또는 AI 평가 없음
        """
        # 1. 강좌 존재 여부 확인
        course = get_object_or_404(Course, pk=course_id)

        # 2. AI 평가 조회
        try:
            ai_review = course.ai_review
        except CourseAIReview.DoesNotExist:
            # AI 평가가 없으면 404 반환
            return Response(
                {'detail': '해당 강좌의 AI 평가가 존재하지 않습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. 직렬화 및 응답
        serializer = CourseAIReviewDetailSerializer(ai_review)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
# =========================
# 3. 리뷰 요약 생성 API
# =========================

# 3.1 CourseReviewSummaryView | 강좌 리뷰 요약 생성 API
class CourseReviewSummaryView(APIView):
    """
    [API]
    - GET: /api/v1/comparisons/courses/{course_id}/review-summary/

    [설계 의도]
    - 특정 강좌의 리뷰를 실시간으로 요약하여 정보 제공
    - courses앱의 강좌 상세 페이지에서 재사용 가능
    - comparisonanalyze api와 분리하여 독립적 호출 지원

    [상세 고려 사항]
    - 인증 필요 (전역 설정 IsAuthenticated)
    # NOTE 비로그인 사용자도 체험 가능하게 할지에 대해서 -> 추후 변경 검토
    - 리뷰 요약 생성 실패 시 적절한 에러 메시지 반환
    # TODO: 향후 캐싱 도입 검토
    - LLM 호출 실패 시 graceful fallback 처리
    """


    def get(self, request, course_id):
        """
        강좌 리뷰 요약 조회

        Args:
            course_id: URL path에서 전달된 강좌 ID

        Returns:
            200: 리뷰 요약 정보
            404: 강좌 없음
            500: 리뷰 요약 생성 실패
        """
        # 1. 강좌 존재 여부 확인
        course = get_object_or_404(Course, pk=course_id)

        # 2. 서비스 인스턴스 가져오기 (싱글톤)
        llm_service = get_llm_service()

        # 3. 리뷰 요약 생성
        try:
            review_summary = llm_service.generate_review_summary(
                course_id=course.id
            )
        except Exception as e:
            # LLM 호출 실패 시 에러 로깅 후 fallback 메시지 반환
            # 전체 요청을 500으로 실패시키지 않고 안내 메시지 제공
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f'리뷰 요약 생성 실패 (Course {course_id}): {str(e)}',
                exc_info=True
            )

            review_summary = {
                'summary': '일시적으로 리뷰 요약을 제공할 수 없습니다. 잠시 후 다시 시도해주세요.',
                'review_count': 0,
                'reliability': 'low',
                'warning_message': 'LLM 서비스 일시적 오류가 발생했습니다'
            }

        # 4. 직렬화 및 응답
        serializer = ReviewSummarySerializer(review_summary)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
# =========================
# 4. 감성분석 API
# =========================

# 4.1 CourseSentimentView | 강좌 감성분석 조회 API
class CourseSentimentView(APIView):
    """
    [API]
    - GET: /api/v1/comparisons/courses/{course_id}/sentiment/

    [설계 의도]
    - 특정 강좌의 리뷰 감성분석 결과만 독립적으로 조회
    - POST /analyze/ 에서 사용하는 동일한 Service Layer 재사용
    - 프론트엔드에서 강좌 상세 페이지 등에서 개별 호출 가능

    [상세 고려사항]
    - 인증 불필요 (AllowAny) - 공개 정보
    - 강좌가 없으면 404 반환
    - 리뷰가 없어도 200 반환 (기본값)
      - positive_ratio: 0.0
      - review_count: 0
      - reliability: 'low'
    - Service Layer 호출만 담당 (비즈니스 로직 분리)
    """

    permission_classes = [AllowAny]    # courses/ 강좌 상세 페이지에서 비로그인 사용자도 접근 가능해야 함.

    def get(self, request, course_id):
        """
        강좌 리뷰 감성분석 조회

        [처리 흐름]
        1. 강좌 존재 여부 확인
        2. SentimentService 인스턴스 가져오기
        3. analyze_course_reviews(course_id) 호출
        4. 결과 직렬화 (SentimentResultSerializer)
        5. 응답 반환
        """
        # 1. 강좌 존재 여부 확인
        course = get_object_or_404(Course, pk=course_id)

        # 2. SentimentService 인스턴스 가져오기 (싱글톤)
        sentiment_service = get_sentiment_service()

        # 3. 감성분석 수행
        # 기존에 구현된 analyze_course_reviews 재사용
        # - Service가 DB 조회 + processor 호출 + 통계 가공 담당
        # - 리뷰가 없으면 _get_default_result() 반환
        try:
            sentiment_result = sentiment_service.analyze_course_reviews(course_id)
        except Exception as e:
            # Service 호출 실패 시 로깅 후 기본값 반환
            logger.error(
                f'리뷰 감성분석 실패 (Course {course_id}): {e}',
                exc_info=True
            )
            sentiment_result = {
                'positive_ratio': 0.0,
                'review_count': 0,
                'reliability': 'low'
            }

        # 4. 응답 직렬화
        # 기존 serializers.py에 있는 SentimentResultSerializer를 그대로 사용
        response_serializer = SentimentResultSerializer(sentiment_result)

        # 5. 응답 반환
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )