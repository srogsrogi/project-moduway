from django.shortcuts import render, get_object_or_404
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from elasticsearch import Elasticsearch

from .models import Course, CourseReview
from .serializers import CourseDetailSerializer, CourseReviewSerializer
from apps.mypage.serializers import SimpleCourseSerializer

class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class CourseReviewListView(generics.ListAPIView):
    serializer_class = CourseReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return CourseReview.objects.filter(course_id=course_id).select_related('user').order_by('-created_at')

# ES 클라이언트 설정
ES_CLIENT = Elasticsearch(getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200'))

class CourseRecommendationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        target_course = get_object_or_404(Course, id=course_id)
        query_vector = target_course.embedding

        if query_vector is None:
            return Response([])

        try:
            # 중복 필터링을 위해 넉넉히 20개 가져옴, 출력은 4개
            res = ES_CLIENT.search(
                index="kmooc_courses",
                knn={
                    "field": "embedding",
                    "query_vector": list(query_vector),
                    "k": 20,
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
