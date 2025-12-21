from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
# Django ORM 집계/조건 필터링 도구 import
# - Count: 개수 집계
# - Q: 복합 조건(AND/OR/NOT, 필터 조건 분기)에 사용
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from apps.courses.models import Course, Enrollment, Wishlist, CourseReview
from apps.community.models import Post, Comment, Scrap
from apps.accounts.models import UserConsent

from .serializers import WishlistSerializer, CourseReviewSerializer, DashboardStatsSerializer, EnrollmentDetailSerializer, EnrollmentListSerializer, CommunityStatsSerializer, MyPostSerializer, MyCommentSerializer, MyScrapSerializer, ProfileSerializer

User = get_user_model()

# 개요
"""
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

# =========================
# 1) 대시보드: 학습 현황 요약
# =========================

# 1.1 DashboardStatsView | 학습 현황 요약
class DashboardStatsView(APIView):
    """
    [API]
    - GET: /api/v1/mypage/dashboard/stats/

    [설계 의도]
    - 마이페이지 최상단 대시보드에서 보여줄 "요약 통계" 제공
    - 다음 4가지 지표를 한 번에 집계하여 반환
      1) 수강 중 강좌 수
      2) 수강 완료 강좌 수
      3) 찜한 강좌 수
      4) 내가 작성한 수강평 수

    [상세 고려 사항]
    - aggregate()를 활용하여 단일 쿼리로 집계
    => Python 루프 대신 DB 레벨 집계로 성능 최적화

    # NOTE:
    # - 전역 permission 정책으로 IsAuthenticated가 설정되어 있으나,
    #   마이페이지 핵심 API임을 명확히 하기 위해
    #   View 레벨에서도 permission을 다시 명시함
    """

    # 로그인한 사용자만 접근 가능
    # - 비로그인 사용자가 접근하면 DRF가 401 Unauthorized 응답을 반환
    permission_classes = [IsAuthenticated]

    # GET 요청 처리 메서드
    # - /mypage/dashboard/stats/ 로 GET 요청이 들어오면 이 메서드가 실행됨
    def get(self, request):
        # 현재 사용자 객체
        user = request.user

        # Enrollment 집계

        # Enrollment.objects.filter(user=user):
        # - 현재 사용자에 해당하는 수강 기록만 대상으로 제한
        #
        # aggregate(...):
        # - queryset 결과를 "한 번에" 집계해서 dict로 반환
        # - 여기서는 '수강중 개수', '수강완료 개수'를 동시에 구함
        enrollment_stats = Enrollment.objects.filter(user=user).aggregate(
            # Count('id', filter=Q(...)):
            # - 특정 조건을 만족하는 레코드만 Count 하는 방식
            # - Django가 지원하는 조건부 집계 패턴 (DB가 조건에 맞는 행만 카운트)

            # enrolled_count:
            # - status가 ENROLLED(수강중)인 Enrollment 레코드 개수
            enrolled_count=Count('id', filter=Q(status=Enrollment.Status.ENROLLED)),
            # completed_count:
            # - status가 COMPLETED(수강완료)인 Enrollment 레코드 개수
            completed_count=Count('id', filter=Q(status=Enrollment.Status.COMPLETED))
        )

        # Wishlist(찜한 강좌), CourseReview(내가 작성한 수강평) 집계
        # 찜한 강좌 수
        # - user 필터링 후 count()로 개수만 반환
        # - 단순 count라 aggregate 없이도 충분히 빠르고 명확하다고 생각.
            # - 단일 지표(개수 1개) 집계이므로
            #   aggregate 대신 count()를 사용
            # - DB 레벨에서 SELECT COUNT(*)만 수행하므로
            #   성능상 차이 없고, 코드 가독성이 더 좋음
        # ++ 추가 설명 : count()는 내부적으로 SQL의 COUNT(*)로 변환되어 DB 레벨에서 효율적으로 처리됨
            # SELECT COUNT(*) 
            # FROM wishlist 
            # WHERE user_id = ?
        wishlist_count = Wishlist.objects.filter(user=user).count()
        my_review_count = CourseReview.objects.filter(user=user).count()

        # 응답 데이터 구성
        data = {
            'enrolled_count': enrollment_stats['enrolled_count'],
            'completed_count': enrollment_stats['completed_count'],
            'wishlist_count': wishlist_count,
            'my_review_count': my_review_count
        }
        # 직렬화
        # NOTE:
        # DashboardStatsSerializer는
        # dict 데이터를 인스턴스로 전달하여, JSON 응답으로 변환하는 역할만 수행
        # ModelSerializer가 아니며, DB 저장/검증의 목적이 아님
        serializer = DashboardStatsSerializer(data)
        # JSON 응답 반환
        # - serializer.data는 최종적으로 클라이언트에게 내려갈 dict
        return Response(serializer.data)


# =========================
# 2) 학습 현황
#   - 1. RecentCourseView         | 최근 학습 강좌 1건 조회 (이어듣기 기능까지)
#   - 2. EnrollmentListView       | 수강 목록 조회 (수강중, 수강완료 필터링)
#   - 3. EnrollmentStatusView     | 특정 강좌의 수강 상세 정보 조회
#   - 4. CourseReviewView         | 수강평 등록/수정/삭제
#   - 5.1. WishlistListView       | 위시리스트 목록 조회
#   - 5.2. WishlistToggleView     | 위시리스트 추가/삭제
# =========================

# 2.1 RecentCourseView | 최근 학습 강좌 조회
class RecentCourseView(APIView):
    """
    [API]
    - GET: /api/v1/mypage/courses/recent/

    [설계 의도]
    - 사용자가 가장 최근에 학습한 강좌 1건을 조회하여
      "이어듣기" UX(최근 학습 강좌 바로가기)를 제공

    [상세 고려 사항]
    - last_studied_at이 존재하면 이를 최우선 기준으로 최신 1건 선택
    - last_studied_at이 NULL인 경우를 대비해 created_at을 보조 정렬 기준으로 사용
      (예: 아직 학습 기록이 없는 '막 수강 등록한 강좌'도 최근 강좌로 잡히게)
    - select_related('course')로 Enrollment → Course 접근 시 N+1 쿼리 방지 (미리 조인)
    - 전역 DEFAULT_PERMISSION이 있어도,
      마이페이지 핵심 API임을 명확히 하고 전역 정책 변경에도 흔들리지 않게
      View 레벨에서 IsAuthenticated를 명시적으로 재선언(방어적 설계)
    """
    # 인증된 사용자만 접근 가능 (마이페이지 전용)
    # - 전역 설정으로도 인증이 걸려있지만,
    #   본 API가 개인정보/개인화 데이터 영역임을 명확히 드러내기 위해
    #   View 레벨에서도 permission을 다시 명시함
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 최근 학습 강좌 조회 (last_studied_at 우선, null이면 created_at)
        recent_enrollment = Enrollment.objects.filter(
            user=user # 현재 사용자 수강 기록 필터링
        # select_related('course'):
        # - Enrollment가 참조하는 course(FK)를 JOIN으로 미리 가져옴
        # - Serializer에서 enrollment.course 접근 시 추가 쿼리(N+1) 발생 방지
        ).select_related('course').order_by(  
            '-last_studied_at', '-created_at' # 내림차순
        ).first() # 가장 최근 1건

        # 학습 기록도 없고 수강 등록도 없고 그냥 아예 없으면 recent_enrollment가 None
        if not recent_enrollment:
            # 404 응답 반환으로 처리하겠음.
            return Response(
                {"detail": "최근 학습한 강좌가 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        # 직렬화
        serializer = EnrollmentDetailSerializer(recent_enrollment)
        return Response(serializer.data)
    

# 2.2 EnrollmentListView | 수강 목록 조회
    # generics.ListAPIView를 사용하는 이유:
    # - 이 View는 "데이터 목록을 조회하는(GET)" 역할만 한다.
    #
    # - ListAPIView는
    #   · GET 요청을 자동으로 처리해 주고
    #   · 여러 개의 데이터를 리스트 형태로 반환하며
    #   · Serializer를 이용해 데이터를 JSON으로 바꾸고
    #   · 페이지네이션(한 페이지에 몇 개 보여줄지)까지
    #   DRF가 미리 만들어 둔 방식대로 자동 처리해 준다.
    #
    # - 그래서 APIView를 써서 get()을 직접 만드는 것보다
    #   코드가 훨씬 짧아지고, 실수할 가능성도 줄어든다.
    #
    # - 이 View에서 우리가 직접 작성해야 할 부분은
    #   "이번 요청에서 어떤 데이터들을 가져올지"를 정하는 부분뿐이라,
    #   get_queryset() 메서드만 구현하면 된다.
class EnrollmentListView(generics.ListAPIView):
    """
    [API]
    #   backend/apps/courses/models.py의
    #   class Status(models.TextChoices)와 동일하게 처리함! (enrolled, completed, dropped)
    - GET: /api/v1/mypage/courses/?status=enrolled
    - GET: /api/v1/mypage/courses/?status=completed

    [설계 의도]
    - 마이페이지에서 사용자의 수강 강좌 목록을 조회 (수강중/완료 필터링)
    - status 쿼리 파라미터를 통해 수강중, 수강완료 필터링을 지원.
    - #TODO? 향후 수강취소(dropped) 필터링도 지원 가능

    [상세 고려 사항]
    - status 쿼리 파라미터로 필터링
    - select_related('course')로 미리 조인해서 N+1 방지
    - 정렬은 "최근 학습한 강좌가 위로" 오도록
      last_studied_at 내림차순을 우선 적용하고,
      last_studied_at이 NULL이거나 동일한 경우 created_at으로 보조 정렬
    - 전역 DEFAULT_PERMISSION이 있어도,
      마이페이지 핵심 API임을 명확히 하고 전역 정책 변경에도 흔들리지 않게
      View 레벨에서 IsAuthenticated를 명시적으로 재선언(방어적 설계)
    """
     # 이 View가 사용할 Serializer 지정
    # - ListAPIView는 queryset의 각 객체를 serializer_class로 직렬화하여 리스트 응답 생성
    serializer_class = EnrollmentListSerializer

    permission_classes = [IsAuthenticated]

    # ListAPIView는 GET 요청이 들어오면,
    # 먼저 get_queryset()을 호출해서
    # "이번 요청에서 어떤 데이터를 조회할지"를 정한다.
    #
    # queryset 속성은 항상 같은 데이터만 조회하는 고정 값이기 때문에,
    # 로그인한 사용자(request.user)나
    # URL 쿼리 파라미터(query_param)에 따라
    # 데이터를 다르게 조회하기 어렵다.
    #
    # 그래서 요청마다 조회 대상이 달라지는 경우에는
    # get_queryset() 메서드를 직접 구현해서 사용한다.
    def get_queryset(self):
        # 현재 로그인한 사용자
        user = self.request.user
        # url 쿼리 파라미터에서 status 값 추출
        status_param = self.request.query_params.get('status', None)

        # 기본 QuerySet: 현재 사용자 수강 기록 전체
        # - 내 수강 기록만 필터링
        # - course를 미리 조인으로 가져와서 추가 쿼리 발생 방지(N+1 문제 해결)
        queryset = Enrollment.objects.filter(
            user=user
        ).select_related('course')

        # status 필터링
        if status_param == 'enrolled': # 수강 중 
            queryset = queryset.filter(status=Enrollment.Status.ENROLLED)
        elif status_param == 'completed': # 수강 완료
            queryset = queryset.filter(status=Enrollment.Status.COMPLETED)

        # status 파라미터가 없거나 예상 값이 아니면
        # 필터링 없이 전체 수강 목록을 반환

        # 정렬 기준 적용 후 반환하기
        # last_studied_at 내림차순:
        # - "최근 학습한 강좌"가 먼저 오도록
        #
        # created_at 내림차순:
        # - last_studied_at이 NULL이거나 동일한 경우 보조 정렬
        #
        # NOTE:
        # - DB에 따라 NULL 정렬 위치가 다를 수 있어,
        #   "NULL이면 created_at 기준"을 엄밀하게 보장하려면
        #   Coalesce 등을 이용한 정렬이 더 확실함
        return queryset.order_by('-last_studied_at', '-created_at')



# 2.3 EnrollmentStatusView | 특정 강좌 수강 상세 정보 조회
    # DRF의 generic class-based view import
    # - RetrieveAPIView: "단일 객체 조회(GET 1건)"에 특화된 제네릭 View
class EnrollmentStatusView(generics.RetrieveAPIView):
    """
    [API]
    - GET: /api/v1/mypage/courses/{course_id}/status/

    [설계 의도]
    - 특정 강좌의 수강 상세 정보 조회

    [상세 고려 사항]
    - URL에서 course_id를 받아 해당 강좌의 Enrollment를 조회
    - 현재 사용자의 수강 정보만 반환
    - select_related('course')를 사용해
      Enrollment → Course 접근 시 추가 쿼리(N+1) 발생 방지
    """
    # 이 View에서 사용할 Serializer
    # - RetrieveAPIView는 단일 객체 1개를 가져와
    #   serializer_class로 직렬화해 응답한다.
    serializer_class = EnrollmentDetailSerializer
    # 인증된 사용자만 접근 가능
    # - 전역 설정이 있더라도,
    #   마이페이지 핵심 API임을 명확히 하기 위해 View 레벨에서 재선언(방어적 설계)
    permission_classes = [IsAuthenticated]

    # URL 경로에서 객체를 식별할 때 사용할 키 이름
    # 기본값은 'pk'지만,
    # 여기서는 course_id를 사용하므로 lookup_url_kwarg를 명시적으로 지정
    lookup_url_kwarg = 'course_id'

    # 단일 객체 조회 로직
    # RetrieveAPIView는 내부적으로 get_object()를 호출하여
    # "이번 요청에서 조회할 단일 객체 1개"를 결정한다.
    #
    # 기본 구현은 pk 기반 조회이지만,
    # 여기서는 (user + course_id) 조건으로 조회해야 하므로
    # get_object()를 직접 재정의한다.
    def get_object(self):
        # URL에서 course_id 추출
        course_id = self.kwargs.get('course_id')
        # 현재 로그인한 사용자
        user = self.request.user

        # get_object_or_404:
        # - 조건에 맞는 객체가 없으면
        #   자동으로 404 Not Found 응답 반환
        enrollment = get_object_or_404(
            # Enrollment.objects.select_related('course'):
            # - course(ForeignKey)를 JOIN으로 미리 가져옴
            Enrollment.objects.select_related('course'),
            user=user,
            course_id=course_id
        )
        return enrollment


# 2.4 CourseReviewView | 수강평 등록/수정/삭제
    # 검증 로직을 수행하지 않는 이유는,
    # 검증 규칙을 Serializer에 이미 추가했기 때문에!
    # view는 저장 로직에만 집중하도록 설계함.
class CourseReviewView(APIView):
    """
    [API]
    - POST: /api/v1/mypage/courses/{course_id}/rating/
    - DELETE: /api/v1/mypage/courses/{course_id}/rating/

    [설계 의도]
    - 사용자가 특정 강좌에 대해 수강평을 남기는 기능 제공
    - "등록"과 "수정"을 POST 하나로 통합하고, 삭제는 DELETE로 분리

    [상세 고려 사항]
    - POST:
      - Serializer에서 입력 검증을 전담
        · review_text 필수
        · review_text 최소 100자
        · rating 범위(1~5)
      - update_or_create()로 등록/수정 로직 통합
      - UniqueConstraint(user, course)를 전제로
        사용자당 강좌별 수강평 1개 보장
    - DELETE:
      - 현재 로그인한 사용자가 작성한 리뷰만 삭제 가능
      - 리뷰가 없으면 404 반환
    - 전역 permission이 있어도,
      마이페이지 핵심 API임을 명확히 하기 위해
      View 레벨에서 IsAuthenticated를 명시적으로 재선언
    """

    # 인증된 사용자만 접근 가능
    # - 전역 설정에도 IsAuthenticated가 있지만,
    #   본 API가 개인 데이터(리뷰 작성/삭제) 영역임을 명확히 하기 위해 재선언
    permission_classes = [IsAuthenticated]

    # POST: 수강평 등록/수정
    def post(self, request, course_id):
        # 현재 로그인한 사용자
        user = request.user
        # URL로 전달받은 course_id에 해당하는 강좌가 존재하는지 확인
        # - 존재하지 않으면 404 반환
        course = get_object_or_404(Course, pk=course_id)

        # 클라이언트가 보낸 요청 body(JSON)를 Serializer로 검증.
        # DRF의 Serializer는 두 가지 역할이 있다고 생각하면 편함
            # 1. 입력 검증: 클라이언트가 보낸 데이터를 검증하고 정제 (주로 post/put/patch요청)
            # 2. 출력 직렬화: 파이썬 객체를 JSON 등으로 변환 (예쁘게) (주로 get요청)
        # 여기서는 1번의 쓰임새. 입력 검증용.
            # 보통 1번 역할을 할 때는 data=... 인자를 사용하고,
            # 2번 역할을 할 때는 instance=... 인자를 사용함.
        # 그래서 여기서는 data=request.data 로 쓰는 것 !!!!
        serializer = CourseReviewSerializer(data=request.data)

        # 유효성 검사
        # - 실패 시 ValidationError 발생
        # - DRF가 자동으로 400 Bad Request 응답 생성
        serializer.is_valid(raise_exception=True)

        # 검증 통과 시, 리뷰 등록/수정
        # - update_or_create():
        #   - (user, course) 조합으로 기존 리뷰가 있으면 수정
        #   - 없으면 새로 생성
        review, created = CourseReview.objects.update_or_create(
            user=user,
            course=course,
            defaults={
                'rating': serializer.validated_data['rating'],
                'review_text': serializer.validated_data['review_text']
            }
        )
        # 저장된 결과를 serializer로 다시 직렬화해서 응답
            # -created_at, updated_at 같은 "서버가 저장하는" 필드도 응답에 포함시키기 위함
        result_serializer = CourseReviewSerializer(review)

        # 생성이면 201, 수정이면 200
        if created:
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(result_serializer.data, status=status.HTTP_200_OK)


    # DELETE: 수강평 삭제
    def delete(self, request, course_id):
        # 현재 로그인한 사용자
        user = request.user

        # 강좌 존재 여부 확인
        course = get_object_or_404(Course, pk=course_id)

        # user + course 조합으로 해당 사용자가 작성한 특정 강좌의 리뷰만 삭제 가능
        #  - 리뷰가 없으면 404 반환
        #  - 있으면 삭제
        try:
            # user + course 조합
            review = CourseReview.objects.get(user=user, course=course)
            review.delete()

            return Response(
                {"detail": "수강평이 삭제되었습니다."},
                status=status.HTTP_204_NO_CONTENT # 삭제 성공
            )
        
        except CourseReview.DoesNotExist:
            # 리뷰가 없으면 404 응답
            return Response(
                {"detail": "작성한 수강평이 없습니다."},
                status=status.HTTP_404_NOT_FOUND # 삭제 실패
            )

# 2.5.1 WishlistListView | 위시리스트 목록 조회
class WishlistListView(generics.ListAPIView):
    """
    [API]
    - GET: /api/v1/mypage/wishlist/

    [설계 의도]
    - 사용자가 찜한 강좌 목록을 조회하기 위한 API
    - 마이페이지에서 "내가 찜한 강좌" 리스트 화면에 사용

    [상세 고려 사항]
    - ListAPIView를 사용하는 이유:
      - 이 API는 "목록 조회(GET)"만 필요함
      - GET 처리/Serializer 적용/페이지네이션 등은 DRF가 기본 제공하므로
        우리는 "어떤 데이터를 가져올지(get_queryset)"만 정의하면 됨
    - IsAuthenticated를 명시적으로 재선언(방어적 설계)
    - select_related('course')로 Wishlist → Course 접근 시 N+1 쿼리 방지
    - 최신순 정렬.
    """
    # 이 뷰가 사용한 Serializer 지정
    serializer_class = WishlistSerializer

    # 인증된 사용자만 접근 가능 # 방어적 설계
    permission_classes = [IsAuthenticated]

    # ListAPIView는 GET 요청이 들어오면 get_queryset()을 먼저 호출하여
    # "이번 요청에서 실제로 조회할 데이터 범위(QuerySet)"를 결정한다.
    #
    # queryset 속성(고정 QuerySet) 대신 get_queryset()을 사용하는 이유:
    # - request.user(로그인 사용자) 같은 요청 맥락에 따라
    #   조회 대상이 매번 달라져야 하기 때문
    def get_queryset(self):
        # 현재 로그인한 사용자
        user = self.request.user
        return Wishlist.objects.filter(
            user=user
        # select_related('course'):
        # - FK인 course를 JOIN으로 미리 로드
        # - Serializer에서 wishlist.course 접근 시 추가 쿼리 발생 방지(N+1 방지)
        ).select_related('course').order_by('-created_at') # 최신 순
    

# 2.5.2 WishlistToggleView | 위시리스트 추가/삭제
class WishlistToggleView(APIView):
    """
    [API]
    - POST: /api/v1/mypage/wishlist/{course_id}/
    - DELETE: /api/v1/mypage/wishlist/{course_id}/

    [설계 의도]
    - 위시리스트 추가/삭제

    [상세 고려 사항]
    - POST: get_or_create()로 중복 방지
      - 이미 찜한 강좌라면, 중복 생성하지 말고 200 응답 반환
      - 새로 찜한 강좌라면, 201 Created 응답 반환
    - DELETE: 위시리스트에서 제거
        - 존재하지 않는 찜 항목이면 404 반환
    - UniqueConstraint(user, course)로 중복 방지
    """
    # view 레벨에서 인증된 사용자만 접근 가능 # 방어적 설계
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        # 현재 로그인한 사용자
        user = request.user

        # URL로 전달받은 course_id에 해당하는 강좌가 존재하는지 확인
        # - 존재하지 않으면 404 반환
        course = get_object_or_404(Course, pk=course_id)

        # 위시리스트 생성 시도
        # - 이미 존재하면 생성하지 않고 기존 객체 반환
        # - created: 새로 생성되었는지 여부
        wishlist, created = Wishlist.objects.get_or_create(
            user=user,
            course=course
        )

        if created:
            # 새로 추가되었다면, 201 Created 응답
            return Response(
                {"detail": "위시리스트에 추가되었습니다.", "is_wished": True},
                status=status.HTTP_201_CREATED
            )
        else:
            # 이미 존재하는 항목이라면, 200 OK 응답
            return Response(
                {"detail": "이미 위시리스트에 추가된 강좌입니다.", "is_wished": True},
                status=status.HTTP_200_OK
            )

    def delete(self, request, course_id):
        # 현재 로그인한 사용자
        user = request.user

        # 강좌 존재 여부 확인
        course = get_object_or_404(Course, pk=course_id)

        # 위시리스트에서 제거
        try:
            # user + course 조합으로 위시리스트 조회
            wishlist = Wishlist.objects.get(user=user, course=course)
            wishlist.delete()

            # 삭제 성공, 204
            return Response(
                {"detail": "위시리스트에서 삭제되었습니다.", "is_wished": False},
                status=status.HTTP_204_NO_CONTENT
            )
        
        # 위시리스트에 없는 강좌, 404
        except Wishlist.DoesNotExist:
            return Response(
                {"detail": "위시리스트에 없는 강좌입니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        

# =========================
# 3. 커뮤니티
#   - 1. CommunityStatsView       | 커뮤니티 활동 통계
#   - 2. MyPostListView           | 내가 쓴 글 목록
#   - 3. MyCommentListView        | 내가 쓴 댓글 목록
#   - 4. MyScrapListView          | 내가 스크랩한 게시

# ========================

# 1. CommunityStatsView | 커뮤니티 활동 통계
class CommunityStatsView(APIView):
    """
    [API]
    - GET: /api/v1/mypage/community/stats/

    [설계 의도]
    - 마이페이지에서 커뮤니티 활동 통계를 제공하기 위함.
    - 내가 쓴 글, 댓글, 스크랩 수와, 내 글이 받은 좋아요 수를 한 번에 집계

    [상세 고려 사항]
    - aggregate()로 단일 쿼리 최적화
    - received_likes_count는 내 글이 받은 좋아요 수
    - 집계 데이터는 DB모델 필드가 아니므로 Serializer에서 직접 정의
    - IsAuthenticated를 명시적으로 재선언(방어적 설계))
    """
    # 인증된 사용자만 접근 가능
    # - 전역 설정에도 IsAuthenticated가 있지만,
    #   본 API가 개인 데이터(활동 통계) 영역임을 명확히 하기 위해 재선언(방어적 설계))
    permission_classes = [IsAuthenticated]


    def get(self, request):
        user = request.user

        # 내가 쓴 글/댓글/스크랩 수 집계
        post_count = Post.objects.filter(author=user).count() # 내가 쓴 글 수
        comment_count = Comment.objects.filter(author=user).count() # 내가 쓴 댓글 수
        scrap_count = Scrap.objects.filter(user=user).count() # 내가 쓴 스크랩 수

        # 내 글이 받은 좋아요 수 (aggregate 활용)
        # Post.likes는 ManyToMany 관계이므로 Count 사용
        # 주의:
        # - Count('likes')는 "내가 쓴 게시글들의 좋아요 개수 합"을 의미
        # - 댓글 좋아요는 여기서 포함하지 않음
        post_likes_stats = Post.objects.filter(author=user).aggregate(
            total_likes=Count('likes')
        )

        # 받은 좋아요 수가 None일 수 있으므로 0으로 대체
        received_likes_count = post_likes_stats['total_likes'] or 0

        # 응답 데이터 구성
        data = {
            'post_count': post_count,
            'comment_count': comment_count,
            'scrap_count': scrap_count,
            'received_likes_count': received_likes_count
        }

        # 직렬화
            # NOTE:
            # - data를 인스턴스처럼 직접 전달하여 직렬화
            # - CommunityStatsSerializer는 모델이 아닌 데이터 직렬화용!
        serializer = CommunityStatsSerializer(data)
        return Response(serializer.data)
    
# 2. MyPostListView | 내가 쓴 글 목록
class MyPostListView(generics.ListAPIView):
    """
    [API]
    - GET: /api/v1/mypage/community/posts/

    [설계 의도]
    - 마이페이지에서 내가 작성한 게시글 목록을 조회하기 위함
    - 커뮤니티 활동 내역 확인 화면에 사용

    [상세 고려 사항]
    - ListAPIView 사용 이유:
      - "목록 조회(GET)"만 필요하므로
      - DRF가 기본 제공하는 기능 활용 (GET 처리/Serializer 적용/페이지네이션 등)
      - 우리는 "어떤 데이터를 가져올지(get_queryset)"만 정의하면 됨
    - select_related('author', 'board')로 N+1 방지
    - annotate로 likes_count, comments_count 사전 집계
    - 최신 작성순 정렬
    """

    # 이 뷰가 사용할 Serializer 지정
    # - 게시글 기본 정보 + likes_count, comments_count 포함
    serializer_class = MyPostSerializer

    # 인증된 사용자만 접근 가능 # 방어적 설계
    permission_classes = [IsAuthenticated]

    # get_queryset 메서드 재정의
        # ListAPIView는 GET 요청이 들어오면
        # 가장 먼저 get_queryset()을 호출하여
        # "이번 요청에서 조회할 데이터 범위"를 결정한다.
    def get_queryset(self):
        # 현재 로그인한 사용자
        user = self.request.user


        return Post.objects.filter(
            author=user # 내가 쓴 글만 필터링
        # annotate
        # - 각 게시글(Post) 객체에 "계산된 컬럼"을 추가하는 역할
        # - DB에서 미리 집계하여 성능 최적화
        ).select_related('author', 'board').annotate(
            likes_count=Count('likes'),
            # comments_count는 부모 댓글만 집계하여 대댓글 제외
            comments_count=Count('comments', filter=Q(comments__parent=None)) # 가장 최상위인 것만 !
        ).order_by('-created_at') # 최신 순
    
# 3.3 MyCommentListView | 내가 쓴 댓글 목록
class MyCommentListView(generics.ListAPIView):
    """
    [API]
    - GET: /api/v1/mypage/community/comments/

    [설계 의도]
    - 마이페이지에서 "내가 쓴 댓글" 목록을 조회하기 위한 API
    - 댓글만 보여주면 맥락이 부족하므로,
      원문 게시글 정보(제목/게시판 등)를 함께 제공하여
      사용자가 어디에 쓴 댓글인지 바로 알 수 있게 한다.

    [상세 고려 사항]
    - ListAPIView 사용
    - select_related('author', 'post', 'post__board')로 미리 조인해놔서 N+1 방지
    - 최신 작성순으로 정렬
    """
    # 이 뷰가 사용할 Serializer 지정)
    serializer_class = MyCommentSerializer

    # 인증된 사용자만 접근 가능 # 방어적 설계
    permission_classes = [IsAuthenticated]

    # get_queryset 메서드 재정의
    def get_queryset(self):
        # 현재 로그인한 사용자
        user = self.request.user

        return Comment.objects.filter(
            author=user # 내가 쓴 댓글만 필터링
        ).select_related('author', 'post', 'post__board').order_by('-created_at') # 미리 조인하고, 최신 순 정렬
    

# 3.4 MyScrapListView | 내가 스크랩한 게시글 목록
class MyScrapListView(generics.ListAPIView):
    """
    [API]
    - GET: /api/v1/mypage/scraps/

    [설계 의도]
    - 마이페이지에서 "내가 스크랩한 게시글" 목록을 조회하기 위한 API
    - 스크랩 자체 정보만 주면 맥락이 부족하므로,
      스크랩한 게시글(Post)의 핵심 정보까지 함께 제공한다.

    [상세 고려 사항]
    - ListAPIView 사용
    - select_related('post', 'post__author', 'post__board')로 N+1 방지
    - post의 likes/comments는 ManyToMany/역참조 관계이므로
        prefetch_related로 미리 로드하여 N+1 방지
    - 최신 스크랩순 정렬

    # NOTE
    selected_related:
    - 정참조만 처리  (FK, OneToOne)
    - 역참조, ManyToMany는 처리 불가
    - SQL JOIN 으로 처리

    prefetch_related:
    - 역참조, ManyToMany 모두 처리 가능
    - JOIN이 아닌 별도 쿼리로 관련 객체들을 한 번에 가져옴
    - 메모리에서 Django가 알아서 매칭해 줌

    # NOTE
    JOIN
    ```sql
    SELECT *
    FROM scrap
    JOIN post ON scrap.post_id = post.id
    WHERE scrap.user_id = ?
    ```
    MANY-TO-MANY
    ```sql
    SELECT *
    FROM post_likes
    WHERE post_id IN (1, 2, 3, 4 ...)
    ```
    REVERSE FOREIGN KEY
    ```sql
    SELECT *
    FROM comment
    WHERE post_id IN (1, 2, 3, 4 ...)
    ```
    """
    # 이 뷰가 사용할 Serializer 지정
    serializer_class = MyScrapSerializer
    permission_classes = [IsAuthenticated]

    # 내부 작동 로직
    """
    # 1. 스크랩 + 게시글 -> selected_related (JOIN)
    SELECT *
    FROM scrap
    JOIN post ON scrap.post_id = post.id
    WHERE scrap.user_id = ?

    # 2. 스크랩된 게시글들의 좋아요를 한 번에 가져오기
    SELECT *
    FROM post_likes
    WHERE post_id IN (1, 2, 3, 4 ...)

    3. 스크랩된 게시글들의 댓글을 한 번에 가져오기
    SELECT *
    FROM comment
    WHERE post_id IN (1, 2, 3, 4 ...)

    4. Django가 메모리에서 post별로 likes, comments 매칭
    post._prefetched_objects_cache = {
    "likes": <QuerySet[...]>,
    "comments": <QuerySet[...]>
}
        
    """
    def get_queryset(self):

        user = self.request.user

        return Scrap.objects.filter(
            user=user
        ).select_related(
            'post', 'post__author', 'post__board'

        ).prefetch_related(
            'post__likes', 'post__comments'
        ).order_by('-created_at') # 최신순
    


# =========================
# 4. 내 계정
# -1. ProfileView             | 내 정보 조회/수정 (마케팅 동의 포함)
# =========================

# 4.1 ProfileView | 내 정보 조회/수정
# - RetrieveUpdateAPIView 사용 이유:
# RetrieveUpdateAPIView는 "단일 객체 조회/수정"에 특화되게끔 DRF가 미리 만들어 둔 제네릭 View이다.
# 즉, 우리가 매번 get()과 put() 메서드를 직접 작성하지 않아도 DRF가 알아서 처리해 준다.
"""
<예시>
GET 요청
 → get_object()
 → serializer = get_serializer(instance)
 → Response(serializer.data)
PUT/PATCH 요청
 → get_object()
 → serializer = get_serializer(instance, data=request.data)
 → serializer.is_valid()
 → serializer.save()
 → perform_update(serializer)
 → Response(serializer.data)
"""
class ProfileView(generics.RetrieveUpdateAPIView):
    """
    [API]
    - GET: /api/v1/mypage/profile/
    - PUT: /api/v1/mypage/profile/

    [설계 의도]
    - 로그인한 사용자의 프로필 정보를 조회하고 수정하기 위한 API
    - 내 정보만 다루니까, 별도의 user_id 없이도 가능

    [상세 고려 사항]
    - 현재 로그인한 사용자 정보만 조회/수정
    - marketing_opt_in은 UserConsent에서 가져와야 함 → SerializerMethodField 활용
    - email 수정 시 중복 검증은 Serializer에서 처리 (검증은 serializer, 저장은 view로 역할 분담!!!)
    - 전역 permission이 있어도, 인증된 사용자만 접근 가능하도록 재선언(방어적 설계)
    """
    # 이 뷰에서 사용할 serializer 지정
    serializer_class = ProfileSerializer
    
    # 인증된 사용자만 접근 가능 # 방어적 설계
    permission_classes = [IsAuthenticated]

    # 조회/수정 대상 객체를 지정.
    def get_object(self):
        """
        [설계 의도]
        - 조회/수정 대상은 항상 "현재 로그인한 사용자"

        [설명]
        - RetrieveUpdateAPIView는 내부적으로
          get_object()를 호출해 대상 객체를 가져온다.
        - 일반적인 경우 pk를 URL에서 받아 조회하지만,
          이 API는 "내 프로필" 전용이므로
          request.user를 그대로 반환한다.
        """
        return self.request.user

    # 프로필 수정 후 추가 처리를 위함.
    def perform_update(self, serializer):
        """
        [설계 의도]
        - User 모델 수정 이후,
          UserConsent(marketing_opt_in)도 함께 갱신

        [상세 고려 사항]
        - serializer.save()는 User 모델의 필드만 저장
          (email, name 등)
        - marketing_opt_in은 User 모델 필드가 아니므로
          request.data에서 직접 추출해 별도로 저장
        """
        # 1) User 모델 필드 저장
        # 이메일, name 등 profileserializer에 정의된 필드 저장은 여기서
        user = serializer.save()

        # 2) marketing_opt_in 업데이트
        # request.data에서 marketing_opt_in 값 추출
        # - 값이 전달된 경우에만 UserConsent 업데이트
        marketing_opt_in = self.request.data.get('marketing_opt_in', None)

        if marketing_opt_in is not None:
            # UserConsent : User - OneToOne 관계
            UserConsent.objects.update_or_create(
                user=user,
                defaults={'marketing_opt_in': marketing_opt_in}
            )


