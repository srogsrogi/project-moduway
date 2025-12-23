from rest_framework import serializers
from django.db.models import Avg
from apps.courses.models import Course, Wishlist, CourseReview

# 개요
"""
1.1 CourseListSerializer   | 강의 목록 시리얼라이저
1.2 CourseDetailSerializer | 강의 상세 정보 시리얼라이저
1.3 CourseReviewSerializer | 강의 리뷰 목록 시리얼라이저
"""

# 1.1 CourseListSerializer | 강의 목록 시리얼라이저
class CourseListSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 목록 조회용 간단한 Serializer
    - average_rating, review_count는 annotate로 계산된 값 사용 # 최적화

    [상세 고려사항]
    - CourseDetailSerializer보다 간소화 (summary 제외)
    - average_rating: View에서 annotate(Avg('reviews__rating'))
    - review_count: View에서 annotate(Count('reviews'))
    - SerializerMethodField 대신 annotated 필드 직접 사용 (성능 최적화)
    """

    # 1. Null 처리 및 소수점 처리를 위해 FloatField 옵션 활용
    # annotate 결과가 None일 경우를 대비해 allow_null=True 명시
      # - DB에서 집계 함수는 리뷰가 하나도 없을 때 0이 아니라 NULL 반환 -> 오류 방지
    average_rating = serializers.FloatField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',                    # 강좌 ID
            'name',                  # 강좌명
            'professor',             # 교수명
            'org_name',              # 운영 기관
            'classfy_name',          # 대분류
            'middle_classfy_name',   # 중분류
            'course_image',          # 썸네일 이미지
            'url',                   # 강좌 URL
            'week',                  # 총 주차
            'course_playtime',       # 총 학습 시간
            'average_rating',        # 평균 평점 (annotated)
            'review_count',          # 리뷰 개수 (annotated)
            'enrollment_start',      # 수강 신청 시작일
            'enrollment_end',        # 수강 신청 종료일
            'study_start',           # 학습 시작일
            'study_end'              # 학습 종료일
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        """
        [설계 의도]
        - 소수점 1자리까지 반올림하여 응답 데이터 깔끔하게 제공
        """
        data = super().to_representation(instance)
        if data['average_rating'] is not None:
            data['average_rating'] = round(data['average_rating'], 1)
        return data


# 1.2 CourseDetailSerializer | 강의 상세 정보 시리얼라이저
class CourseDetailSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 상세 페이지에서 필요한 모든 정보를 통합하여 제공
    - courses 앱의 데이터와 mypage 앱의 활동 데이터를 결합
    
    [가상 필드 설명]
    1. is_wished: 현재 로그인한 유저의 찜 여부 (True/False)
    2. rating: 해당 강좌의 평균 별점 (리뷰 기반)
    3. review_count: 해당 강좌에 달린 전체 수강평 개수
    """
    
    is_wished = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'kmooc_id', 'name', 'org_name', 'professor',
            'classfy_name', 'middle_classfy_name', 'summary',
            'course_image', 'url', 'week', 'course_playtime',
            'certificate_yn', 'is_wished', 'rating', 'review_count',
            'enrollment_start', 'enrollment_end', 'study_start', 'study_end'
        ]

    def get_is_wished(self, obj):
        """
        [로직] 
        - 요청자(request.user)가 로그인 상태라면 Wishlist 모델에서 해당 강좌 존재 여부 확인
        - 비로그인 상태이거나 찜하지 않았다면 False 반환
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(user=request.user, course=obj).exists()
        return False

    def get_rating(self, obj):
        """
        [로직] 
        - CourseReview 모델에서 해당 강좌의 rating 평균값 계산
        - 리뷰가 없을 경우 기본값 0.0 반환
        """
        avg_rating = CourseReview.objects.filter(course=obj).aggregate(Avg('rating'))['rating__avg']
        return round(avg_rating, 1) if avg_rating else 0.0

    def get_review_count(self, obj):
        """
        [로직] 
        - 해당 강좌에 달린 수강평의 총 개수 반환
        """
        return CourseReview.objects.filter(course=obj).count()

# 1.3 CourseReviewSerializer | 강의 리뷰 시리얼라이저
class CourseReviewSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 상세 페이지에서 보여줄 리뷰 목록용 시리얼라이저
    - 작성자 이름(user_name)을 포함하여 UI에 표시
    """
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = CourseReview
        fields = ['id', 'user_name', 'rating', 'review_text', 'created_at']
