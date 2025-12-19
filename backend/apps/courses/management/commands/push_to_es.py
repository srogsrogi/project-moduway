from django.core.management.base import BaseCommand
from apps.courses.models import Course
import requests
import json
from django.conf import settings


class Command(BaseCommand):
    help = 'DB의 데이터를 Elasticsearch로 벌크 전송합니다.'

    def handle(self, *args, **options):
        base_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200')
        es_url = f"{base_url}/kmooc_courses"
        courses = Course.objects.all() # 데이터가 많아지면 배치 처리 필요
        bulk_data = ""
        
        for i, course in enumerate(courses):
            action = {"index": {"_index": "kmooc_courses", "_id": course.id}}
            bulk_data += json.dumps(action) + "\n"
            
            doc = {
                "id": course.id,
                "kmooc_id": course.kmooc_id,
                "name": course.name,
                "summary": course.summary,
                "professor": course.professor,
                "org_name": course.org_name,
                "classfy_name": course.classfy_name,
                "middle_classfy_name": course.middle_classfy_name,
                "course_image": course.course_image,
                "url": course.url,
                "content_key": course.content_key
            }
            bulk_data += json.dumps(doc) + "\n"
            
            if (i + 1) % 500 == 0:
                requests.post(es_url, data=bulk_data, headers={"Content-Type": "application/x-ndjson"})
                bulk_data = ""
                self.stdout.write(f"{i+1}개 전송 중...")

        if bulk_data:
            requests.post(es_url, data=bulk_data, headers={"Content-Type": "application/x-ndjson"})
        
        self.stdout.write(self.style.SUCCESS('전체 데이터 ES 전송 완료!'))