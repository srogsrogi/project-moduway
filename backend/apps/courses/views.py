from django.shortcuts import render, get_object_or_404
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from elasticsearch import Elasticsearch

from .models import Course
from .serializers import CourseDetailSerializer, CourseCardSerializer

class CourseDetailView(generics.RetrieveAPIView):
    """
    [API]
    - GET: /api/v1/courses/{course_id}/
    
    [설계 의도]
    - 강좌의 상세 정보 및 유저별 맞춤 정보(찜 여부)를 제공
    - 상세 페이지는 비로그인 유저도 접근 가능해야 하므로 AllowAny 적용
    """
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny] # 누구나 조회 가능

    def get_serializer_context(self):
        # SerializerMethodField에서 request.user를 사용하기 위해 context 전달
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
class CourseRecommendationView(APIView):
    """
    [설계 의도]
    - 현재 강좌의 embedding 벡터를 기준으로 Elasticsearch k-NN 검색 수행
    - 가장 유사한 강좌 4개를 카드 형태 데이터로 반환
    """
    def get(self, request, course_id):
        # 1. 기준 강좌 조회
        target_course = get_object_or_404(Course, id=course_id)
        query_vector = target_course.embedding

        # 임베딩 데이터가 없는 경우 빈 리스트 반환
        if not query_vector:
            return Response([])

        # 2. Elasticsearch 클라이언트 설정
        # (Docker 환경이라면 보통 http://elasticsearch:9200)
        es = Elasticsearch(getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200'))

        # 3. k-NN 쿼리 (가장 유사한 5개 추출, 본인 제외를 위해 5개)
        query = {
            "knn": {
                "field": "embedding",
                "query_vector": query_vector,
                "k": 5,
                "num_candidates": 100
            },
            "_source": ["id"]
        }

        try:
            # push_es.py에서 설정한 인덱스명(kmooc_courses) 사용
            res = es.search(index="kmooc_courses", body=query)
            
            # 4. 결과 ID 추출 (자기 자신은 제외)
            hit_ids = [
                int(hit["_source"]["id"]) 
                for hit in res["hits"]["hits"] 
                if int(hit["_source"]["id"]) != course_id
            ][:4] # 최종 4개만 선택

            # 5. DB 데이터 조회 및 직렬화
            # 정렬 순서를 유지하기 위해 ID 리스트 순서대로 가져오기
            recommended_courses = Course.objects.filter(id__in=hit_ids)
            # 추천 순서를 보장하려면 추가 정렬 로직이 필요할 수 있으나, 일단 간단히 반환
            serializer = CourseCardSerializer(recommended_courses, many=True)
            
            return Response(serializer.data)

        except Exception as e:
            # 운영 환경에서는 로깅 처리
            return Response({"detail": str(e)}, status=500)