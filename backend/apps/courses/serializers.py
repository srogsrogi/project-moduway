from rest_framework import serializers
from django.db.models import Avg
from apps.courses.models import Course, Wishlist, CourseReview

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
            'classfy_name', 'middle_classfy_name', 'summary', 'raw_summary',
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

class CourseReviewSerializer(serializers.ModelSerializer):
    """
    [설계 의도]
    - 강좌 상세 페이지에서 보여줄 리뷰 목록용 시리얼라이저
    - 작성자 이름(user_name)을 포함하여 UI에 표시
    - is_owner 필드를 통해 현재 요청자가 리뷰의 소유주인지 여부 판별
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = CourseReview
        fields = ['id', 'user_name', 'rating', 'review_text', 'created_at', 'is_owner']

    def get_is_owner(self, obj):
        """
        [로직] 
        - Serializer가 context로부터 request를 받아, 로그인된 user와 리뷰의 user를 비교
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.user == request.user
        return False
