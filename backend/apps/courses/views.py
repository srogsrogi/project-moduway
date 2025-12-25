from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, Count, Avg, Window, F
from django.db.models.functions import Coalesce, RowNumber
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import OrderingFilter
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from elasticsearch import Elasticsearch
import requests
import json
import os

from .models import Course, CourseReview
from .serializers import CourseDetailSerializer, CourseReviewSerializer, CourseListSerializer
from apps.mypage.serializers import SimpleCourseSerializer

# 개요
"""
1.1 CourseListPagination | 강의 목록 조회 시 페이지네이션
1.2 CourseListView       | 강의 목록 조회
1.3 

2.1 CourseDetailView         | 강의 상세 정보 조회
2.2 CourseReviewListView     | 강의 리뷰 목록 조회
2.3 CourseRecommendationView | 추천 강의 조회
"""


PAGE_SIZE = 10          # 기본 페이지 크기
MAX_PAGE_SIZE = 100     # 최대 페이지 크기

# ========================
# 1. 강의 목록 API
# ========================

# 1.1 CourseListPagination | 강의 목록 조회 시 페이지네이션 
class CourseListPagination(PageNumberPagination):
    """
    [설계 의도]
    - 강좌 목록 조회 시 페이지네이션 설정

    [상세 고려사항]
    - page_size: 기본 {PAGE_SIZE}개
    - page_size_query_param: 클라이언트가 페이지 크기 조정 가능
    - max_page_size: 최대 {MAX_PAGE_SIZE}개까지 허용
    """
    page_size = PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE

# 1.2 CourseListView | 강의 목록 조회
class CourseListView(generics.ListAPIView):
    """
    [API]
    - GET: /api/v1/courses/

    [설계 의도]
    - 강좌 목록 조회/검색/필터링/정렬 제공
    - average_rating 기준 정렬 지원 (DB 레벨 계산)
    - 페이지네이션으로 성능 최적화

    [처리 흐름]
    1. QuerySet에 average_rating, review_count annotate
    2. 검색 조건 적용 (search 파라미터)
    3. 필터링 적용 (classfy_name, org_name 등)
    4. 정렬 적용 (ordering 파라미터, 기본값: -average_rating)
    5. 페이지네이션 적용
    6. 응답 반환

    [상세 고려사항]
    - permission_classes = [AllowAny]: 비로그인 사용자도 조회 가능
    - annotate 활용: N+1 쿼리 방지
    - Q 객체: 복합 검색 조건 (name OR summary)
    - Coalesce: average_rating이 NULL이면 0.0으로 처리
        - COALESCE(값, 대체값) := 값이 NULL이 아니면 그대로, 값이 NULL이면 대체값 반환
    - default ordering: -average_rating (평점 높은순)
    """

    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    pagination_class = CourseListPagination

    def get_queryset(self):
        """
        [설계 의도]
        - QuerySet 구성: annotate → filter → search → order_by

        [처리 흐름]
        1. annotate (평점, 리뷰수, Window Function으로 중복 제거용 row_num)
        2. 중복 제거 (row_num=1 필터링: 이름+교수자가 같으면 study_start 최신순만 선택)
        3. 검색 (search)
        4. 필터 (category, org 등)
        5. 정렬 (ordering)
        6. Distinct (JOIN으로 인한 추가 중복 방지)
        """
        # DRF ListAPIView는 요청마다 get_queryset()을 호출해서 최종 queryset을 만든다.
        # 따라서 이 함수는 "목록 쿼리 1방"으로 끝나도록 DB 레벨 계산/필터/정렬을 조합한다.

        # 1. Base QuerySet with annotate

        # - 목록 화면에서 필요한 집계 값(평균 평점, 리뷰 수)을 미리 계산하여 N+1을 방지한다.
        # - Window Function으로 중복 제거 처리
        queryset = Course.objects.annotate(
            # 평균 평점 계산 (NULL이면 0.0)
            # - 리뷰가 없는 강좌는 Avg 결과가 NULL이 되므로 Coalesce로 0.0으로 대체
            # - 이렇게 하면 Serializer/프론트에서 None 처리 분기를 줄일 수 있음
            average_rating=Coalesce(
                Avg('reviews__rating'),
                0.0 # 대체값
            ),
            # 리뷰 개수
            review_count=Count('reviews', distinct=True), # distinct=True: 중복 리뷰 방지

            # 2. 중복 제거를 위한 Window Function
            # [설계 의도]
            # - 강좌명(name)과 교수자(professor)가 같다면,
            #   수강 시작일(study_start)이 가장 최신인(Null 포함 정렬 주의) 강좌 1개만 남김
            row_num=Window(
                expression=RowNumber(),
                partition_by=[F('name'), F('professor')],  # 그룹핑 기준
                order_by=F('study_start').desc(nulls_last=True)  # 정렬 기준 (NULL은 마지막)
            )
        ).filter(
            row_num=1  # 각 그룹에서 첫 번째(최신) 강좌만 선택
        )
        
        # 3. Search (강좌명만 검색)
        # ?search=" 파이썬  웹 " -> ['파이썬', '웹']
        search_query = self.request.query_params.get('search', '').strip()  # 공백 제거

        if search_query: # 빈 문자열이면 건너뜀
            keywords = search_query.split() # 공백을 기준으로 토큰화
            search_filter = Q()  # 복합 조건을 처리하기 위한 Q 객체

            for keyword in keywords:
                # 각 키워드가 강좌명에 포함되어야 함 (AND 조건)
                search_filter &= Q(name__icontains=keyword)  # 강좌명이 키워드를 포함(대소문자 무시)

            queryset = queryset.filter(search_filter)

        # 4. Filter
        # - 특정 필드 기반 필터링(카테고리/기관/교수 등)을 파라미터로 받아 적용한다.

        filters = Q()

        # 대분류 필터 (단일 값)
        classfy_name = self.request.query_params.get('classfy_name')
        if classfy_name:
            filters &= Q(classfy_name=classfy_name)

        # 중분류 필터 (다중 값 지원)
        # ?middle_classfy_name=컴퓨터·통신&middle_classfy_name=전기·전자 형태로 받음
        middle_classfy_names = self.request.query_params.getlist('middle_classfy_name')
        if middle_classfy_names:
            # OR 조건으로 처리 (하나라도 일치하면 포함)
            middle_filter = Q()
            for name in middle_classfy_names:
                middle_filter |= Q(middle_classfy_name=name)
            filters &= middle_filter

        # 운영기관 필터 (부분 일치)
        org_name = self.request.query_params.get('org_name')
        if org_name:
            filters &= Q(org_name__icontains=org_name)

        # 교수명 필터 (부분 일치)
        professor = self.request.query_params.get('professor')
        if professor:
            filters &= Q(professor__icontains=professor)

        queryset = queryset.filter(filters) # 누적된 필터는 한 번에 적용

        # 5. Ordering
        # - 정렬 파라미터를 받아 허용된 값만 적용한다, 화이트리스트!!
        ordering = self.request.query_params.get('ordering', '-average_rating') # 기본값: -average_rating

        # ordering 옵션 검증
        allowed_ordering = [
            'average_rating', '-average_rating',  # 평균 평점 오름/내림
            'review_count', '-review_count',      # 리뷰 수 오름/내림
            'created_at', '-created_at',          # 생성일 오름/내림(모델에 created_at이 있다고 가정)
            'name', '-name',                       # 강좌명 오름/내림
            'study_start', '-study_start' # 수강일
        ]

        if ordering not in allowed_ordering:  # 허용되지 않은 정렬 키가 들어오면
            ordering = '-average_rating'       # 안전한 기본 정렬로 강제 fallback

        # 6. Distinct (추가 중복 제거)
        # - Window Function으로 이미 주요 중복은 제거했지만,
        #   annotate/filter 과정에서 JOIN이 생기면 동일 Course가 중복 row로 나올 수 있음
        # - distinct()는 최종 결과에서 중복 Course 제거(단, DB에 따라 성능 영향이 있으니 최소화가 이상적)
        return queryset.order_by(ordering).distinct()  # 정렬 적용 후 중복 제거한 최종 QuerySet 반환

    def list(self, request, *args, **kwargs):
        """
        [설계 의도]
        - 캐싱을 적용하여 동일한 쿼리 파라미터 요청 시 DB 조회 없이 캐시에서 응답
        - 캐시 키: 쿼리 파라미터를 기반으로 생성
        - 캐시 TTL: 5분 (300초)

        [처리 흐름]
        1. 쿼리 파라미터로 캐시 키 생성
        2. 캐시에서 데이터 확인
        3. 캐시 히트 시 캐시 데이터 반환
        4. 캐시 미스 시 DB 조회 후 캐시 저장 및 반환
        """
        # 1. 캐시 키 생성 (쿼리 파라미터 기반)
        query_params = request.GET.urlencode()
        cache_key = f"course_list:{query_params}"

        # 2. 캐시에서 데이터 확인
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)

        # 3. 캐시 미스 - DB 조회
        response = super().list(request, *args, **kwargs)

        # 4. 캐시에 저장 (5분 TTL)
        cache.set(cache_key, response.data, 300)

        return response




# ========================
# 2. 강의 상세, 리뷰, 추천 강의 API
# ========================


# 2.1 CourseDetailView | 강의 상세 정보 조회
class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# 2.2 CourseReviewListView | 강의 리뷰 목록 조회
class CourseReviewListView(generics.ListAPIView):
    serializer_class = CourseReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return CourseReview.objects.filter(course_id=course_id).select_related('user').order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

# ES 클라이언트 설정
ES_CLIENT = Elasticsearch(getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200'))

# 2.3 CourseRecommendationView | 추천 강의 조회
class CourseRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        target_course = get_object_or_404(Course, id=course_id)
        query_vector = target_course.embedding

        if query_vector is None:
            return Response([])

        try:
            # 중복 필터링을 위해 넉넉히 30개 가져옴, 출력은 4개
            res = ES_CLIENT.search(
                index="kmooc_courses",
                knn={
                    "field": "embedding",
                    "query_vector": list(query_vector),
                    "k": 30,
                    "num_candidates": 200
                },
                source=["id"]
            )
            
            hits = res.get("hits", {}).get("hits", [])
            candidate_ids = [int(h["_source"]["id"]) for h in hits]

            # 후보군 정보 한꺼번에 조회
            courses_queryset = Course.objects.filter(id__in=candidate_ids)
            course_data_map = {c.id: c for c in courses_queryset}

            final_courses = []
            seen_identity = set()

            # 현재 강의 정보(이름, 교수)를 중복 기준에 추가
            target_name = target_course.name.strip()
            target_professor = target_course.professor.strip()
            seen_identity.add((target_name, target_professor))

            for c_id in candidate_ids:
                course = course_data_map.get(c_id)
                if not course or course.id == target_course.id:
                    continue

                curr_name = course.name.strip()
                curr_professor = course.professor.strip()

                # 이름과 교수가 모두 같으면 같은 강의의 다른 기수로 판단하여 제외
                identity = (curr_name, curr_professor)
                if identity not in seen_identity:
                    final_courses.append(course)
                    seen_identity.add(identity)

                if len(final_courses) >= 4:
                    break

            serializer = SimpleCourseSerializer(final_courses, many=True)
            return Response(serializer.data)

        except Exception as e:
            import traceback
            print(f"❌ ES 추천 로직 에러: {e}")
            print(traceback.format_exc())
            # 에러 발생 시 500 대신 빈 리스트 반환하여 프론트엔드 에러 방지
            return Response([], status=status.HTTP_200_OK)


class CourseKeywordSearchView(APIView):
    """
    Elasticsearch를 활용한 키워드 검색 (Fuzzy Search 지원)

    [설계 의도]
    - ES의 multi_match + fuzziness로 오타 보정 기능 제공
    - 제목(name) 필드만 검색
    - 필터링 및 페이지네이션 지원
    - 중복 제거 (같은 이름+교수 조합)
    """
    permission_classes = [AllowAny]

    def _build_es_filters(self):
        """ES query용 필터 조건 생성"""
        filters = []

        # 대분류 필터 (정확히 일치)
        classfy_name = self.request.query_params.get('classfy_name')
        if classfy_name:
            filters.append({"term": {"classfy_name.keyword": classfy_name}})

        # 중분류 필터 (다중 값 지원)
        middle_classfy_names = self.request.query_params.getlist('middle_classfy_name')
        if middle_classfy_names:
            filters.append({"terms": {"middle_classfy_name.keyword": middle_classfy_names}})

        # 운영기관 필터 (부분 일치)
        org_name = self.request.query_params.get('org_name')
        if org_name:
            filters.append({"match": {"org_name": org_name}})

        # 교수명 필터 (부분 일치)
        professor = self.request.query_params.get('professor')
        if professor:
            filters.append({"match": {"professor": professor}})

        return filters

    def get(self, request):
        search_query = request.query_params.get('search', '').strip()
        if not search_query:
            return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)

        # 페이지네이션 파라미터
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 3))
        from_index = (page - 1) * page_size

        try:
            # ES 필터 조건 생성
            es_filters = self._build_es_filters()

            # ES 검색 쿼리 구성
            es_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": search_query,
                                "fields": ["name^2"],  # name 필드만, 가중치 2배
                                "fuzziness": 1,        # 1글자 차이까지 허용
                                "operator": "and",     # 모든 키워드 포함
                                "prefix_length": 1     # 첫 글자는 정확히 일치해야 함
                            }
                        }
                    ]
                }
            }

            # 필터 추가
            if es_filters:
                es_query["bool"]["filter"] = es_filters

            # ES 검색 실행 (넉넉하게 가져와서 중복 제거 후 페이지네이션)
            res = ES_CLIENT.search(
                index="kmooc_courses",
                query=es_query,
                size=200,  # 중복 제거를 위해 넉넉히 가져옴
                source=["id"]
            )

            hits = res.get("hits", {}).get("hits", [])
            candidate_ids = [int(h["_source"]["id"]) for h in hits]

            # DB 조회
            courses_queryset = Course.objects.filter(id__in=candidate_ids).annotate(
                average_rating=Coalesce(Avg('reviews__rating'), 0.0),
                review_count=Count('reviews', distinct=True)
            )
            course_data_map = {c.id: c for c in courses_queryset}

            # 중복 제거 (ES 순서 유지)
            final_courses = []
            seen_identity = set()

            for c_id in candidate_ids:
                course = course_data_map.get(c_id)
                if not course:
                    continue

                curr_name = course.name.strip()
                curr_professor = course.professor.strip()
                identity = (curr_name, curr_professor)

                if identity not in seen_identity:
                    final_courses.append(course)
                    seen_identity.add(identity)

            # 전체 개수
            total_count = len(final_courses)

            # 페이지네이션 적용
            start = from_index
            end = from_index + page_size
            paginated_courses = final_courses[start:end]

            serializer = CourseListSerializer(paginated_courses, many=True)

            return Response({
                "results": serializer.data,
                "count": total_count
            })

        except Exception as e:
            import traceback
            print(f"❌ ES 키워드 검색 에러: {e}")
            print(traceback.format_exc())
            return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)


class CourseSemanticSearchView(APIView):
    """
    사용자 입력 쿼리를 임베딩하여 유사한 강좌를 검색하는 뷰
    CourseRecommendationView와 로직이 유사하나 변경 가능성이 있어 완전 분리하여 설계함
    """
    permission_classes = [AllowAny]

    def _get_embedding(self, text):
        """내부용 임베딩 생성 메서드"""
        GMS_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
        GMS_KEY = os.environ.get("GMS_KEY")

        if not GMS_KEY:
            print("❌ GMS_KEY가 설정되지 않았습니다.")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GMS_KEY}"
        }

        clean_text = text.replace('\n', ' ').replace('\r', ' ').strip()
        if not clean_text:
            return None

        data = {
            "model": "text-embedding-3-small",
            "input": clean_text
        }

        try:
            response = requests.post(GMS_URL, headers=headers, data=json.dumps(data), timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result['data'][0]['embedding']
            else:
                print(f"❌ 임베딩 API 호출 실패: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ 임베딩 생성 중 에러 발생: {e}")
            return None

    def _apply_filters(self, queryset):
        """필터링 로직 (CourseListView와 동일)"""
        filters = Q()

        # 대분류 필터 (단일 값)
        classfy_name = self.request.query_params.get('classfy_name')
        if classfy_name:
            filters &= Q(classfy_name=classfy_name)

        # 중분류 필터 (다중 값 지원)
        middle_classfy_names = self.request.query_params.getlist('middle_classfy_name')
        if middle_classfy_names:
            middle_filter = Q()
            for name in middle_classfy_names:
                middle_filter |= Q(middle_classfy_name=name)
            filters &= middle_filter

        # 운영기관 필터 (부분 일치)
        org_name = self.request.query_params.get('org_name')
        if org_name:
            filters &= Q(org_name__icontains=org_name)

        # 교수명 필터 (부분 일치)
        professor = self.request.query_params.get('professor')
        if professor:
            filters &= Q(professor__icontains=professor)

        return queryset.filter(filters)

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response([], status=status.HTTP_400_BAD_REQUEST)

        # 1. 검색어 임베딩 생성
        query_vector = self._get_embedding(query)
        if not query_vector:
            # 임베딩 실패 시 빈 결과 반환
            return Response([], status=status.HTTP_200_OK)

        try:
            # 2. ES 벡터 검색
            res = ES_CLIENT.search(
                index="kmooc_courses",
                knn={
                    "field": "embedding",
                    "query_vector": query_vector,
                    "k": 50,
                    "num_candidates": 500
                },
                source=["id"]
            )

            hits = res.get("hits", {}).get("hits", [])
            candidate_ids = [int(h["_source"]["id"]) for h in hits]

            # 3. DB 조회 및 필터 적용
            courses_queryset = Course.objects.filter(id__in=candidate_ids)
            courses_queryset = self._apply_filters(courses_queryset)  # 필터 적용
            course_data_map = {c.id: c for c in courses_queryset}

            # 4. 중복 필터링 (ES 순서 유지)
            final_courses = []
            seen_identity = set()

            for c_id in candidate_ids:
                course = course_data_map.get(c_id)
                if not course:
                    continue

                curr_name = course.name.strip()
                curr_professor = course.professor.strip()
                identity = (curr_name, curr_professor)

                if identity not in seen_identity:
                    final_courses.append(course)
                    seen_identity.add(identity)

                # 검색 결과는 조금 더 많이 보여줘도 됨 (예: 20개)
                if len(final_courses) >= 20:
                    break

            serializer = SimpleCourseSerializer(final_courses, many=True)
            return Response(serializer.data)

        except Exception as e:
            import traceback
            print(f"❌ ES 검색 로직 에러: {e}")
            print(traceback.format_exc())
            return Response([], status=status.HTTP_200_OK)
