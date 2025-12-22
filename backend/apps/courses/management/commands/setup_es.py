from django.core.management.base import BaseCommand
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Elasticsearch 인덱스 및 Nori 분석기 설정을 생성합니다.'

    def handle(self, *args, **options):
        base_url = getattr(settings, 'ELASTICSEARCH_URL', 'http://elasticsearch:9200')
        es_url = f"{base_url}/kmooc_courses"
        config = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "nori_analyzer": {
                            "type": "custom",
                            "tokenizer": "nori_tokenizer"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "kmooc_id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "nori_analyzer"},
                    "summary": {"type": "text", "analyzer": "nori_analyzer"},
                    "professor": {"type": "keyword"},
                    "org_name": {"type": "keyword"},
                    "classfy_name": {"type": "keyword"},
                    "middle_classfy_name": {"type": "keyword"},
                    "course_image": {"type": "keyword", "index": False},
                    "url": {"type": "keyword", "index": False},
                    "content_key": {"type": "keyword"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        requests.delete(es_url) # 초기화 코드이므로 운영시 주의
        response = requests.put(es_url, json=config)
        self.stdout.write(self.style.SUCCESS(f'Successfully created index: {response.text}'))