from django.db import models

class Course(models.Model):
    # K-MOOC 원본 데이터의 식별자 (CSV의 id 컬럼)
    kmooc_id = models.CharField(max_length=50, unique=True)
    
    # 강좌 기본 정보
    name = models.CharField(max_length=500)  # 강좌명
    content_key = models.CharField(max_length=500, blank=True, null=True)
    professor = models.CharField(max_length=500, blank=True, null=True)  # 교수자
    org_name = models.CharField(max_length=100, blank=True, null=True)   # 운영기관(대학 등)
    
    # 분류
    classfy_name = models.CharField(max_length=100, blank=True, null=True)        # 대분류
    middle_classfy_name = models.CharField(max_length=100, blank=True, null=True) # 중분류
    
    # 상세 정보
    summary = models.TextField(blank=True, null=True)  # 강좌 요약/소개
    url = models.URLField(max_length=500, blank=True, null=True)  # 강좌 바로가기 URL
    course_image = models.URLField(max_length=500, blank=True, null=True)  # 강좌 썸네일/이미지 URL
    
    # 일정 정보 (NULL 허용)
    enrollment_start = models.DateField(blank=True, null=True) # 수강신청 시작일
    enrollment_end = models.DateField(blank=True, null=True)   # 수강신청 종료일
    study_start = models.DateField(blank=True, null=True)      # 수강 시작일
    study_end = models.DateField(blank=True, null=True)        # 수강 종료일
    
    # 기타 메타데이터
    week = models.FloatField(blank=True, null=True)            # 주차 수
    course_playtime = models.FloatField(blank=True, null=True) # 총 재생 시간 (분 단위 등)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
