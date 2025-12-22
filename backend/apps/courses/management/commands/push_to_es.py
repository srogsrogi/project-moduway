import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.courses.models import Course

class Command(BaseCommand):
    help = 'DB의 데이터를 Elasticsearch로 벌크 전송합니다.'

    def handle(self, *args, **options):
        base_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200')
        # 벌크 전송 엔드포인트는 /_bulk 입니다.
        es_bulk_url = f"{base_url}/_bulk"

        # 임베딩이 있는 코스만 전송 (추천 기능을 위해 필수)
        courses = Course.objects.exclude(embedding__isnull=True)
        total_courses = Course.objects.count()
        skipped = total_courses - courses.count()

        bulk_data = ""

        self.stdout.write("ES 데이터 전송 시작...")
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"임베딩 없는 코스 {skipped}개는 제외됩니다."))

        for i, course in enumerate(courses):
            # 1. 메타데이터 줄
            action = {"index": {"_index": "kmooc_courses", "_id": str(course.id)}}
            bulk_data += json.dumps(action) + "\n"
            
            # 2. 데이터 임베딩 형변환 (numpy float32 해결 핵심)
            safe_embedding = None
            if course.embedding is not None:
                # list()로 감싸는 것만으로는 내부 요소가 numpy 타입일 경우 해결되지 않으므로 
                # 리스트 컴프리헨션으로 요소를 float으로 강제 변환합니다.
                safe_embedding = [float(v) for v in course.embedding]
            
            # 3. 문서 데이터 구성
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
                "content_key": course.content_key,
                "embedding": safe_embedding
            }
            bulk_data += json.dumps(doc) + "\n"
            
            # 500개마다 전송
            if (i + 1) % 500 == 0:
                response = requests.post(
                    es_bulk_url, 
                    data=bulk_data, 
                    headers={"Content-Type": "application/x-ndjson"}
                )
                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"에러 발생: {response.text}"))
                
                bulk_data = ""
                self.stdout.write(f"{i+1}개 전송 완료...")

        # 남은 데이터 전송
        if bulk_data:
            requests.post(
                es_bulk_url, 
                data=bulk_data, 
                headers={"Content-Type": "application/x-ndjson"}
            )
        
        self.stdout.write(self.style.SUCCESS(f'총 {courses.count()}개 데이터 ES 전송 완료!'))
