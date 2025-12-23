import csv
import os
import sys
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.courses.models import Course

# CSV 필드 크기 제한 해제 (raw_summary 등 긴 텍스트 처리용)
csv.field_size_limit(sys.maxsize)

class Command(BaseCommand):
    help = 'Import KMOOC courses from CSV file'

    def handle(self, *args, **kwargs):
        # CSV 파일 경로 (프로젝트 루트 기준 data/backups/kmooc_processed_data.csv)
        base_dir = settings.BASE_DIR  # backend/
        project_root = base_dir.parent # project-moduway/
        csv_path = os.path.join(project_root, 'data', 'backups', 'kmooc_processed_data.csv')

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at: {csv_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading CSV from: {csv_path}'))

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            created_count = 0
            updated_count = 0
            
            for row in reader:
                try:
                    # 날짜 파싱 헬퍼 함수
                    def parse_date(date_str):
                        if not date_str or date_str.strip() == '':
                            return None
                        try:
                            # 다양한 날짜 형식 대응 가능하도록 수정 가능 (현재 YYYY-MM-DD 가정)
                            return datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            return None

                    # 숫자 파싱 헬퍼 함수
                    def parse_float(num_str):
                        if not num_str or num_str.strip() == '':
                            return None
                        try:
                            return float(num_str)
                        except ValueError:
                            return None

                    course_data = {
                        'name': row['name'],
                        'content_key': row.get('content_key'),
                        'professor': row.get('professor'),
                        'org_name': row.get('org_name'),
                        'classfy_name': row.get('classfy_name'),
                        'middle_classfy_name': row.get('middle_classfy_name'),
                        'summary': row.get('summary'),
                        'raw_summary': row.get('raw_summary'), # 추가됨
                        'url': row.get('url'),
                        'course_image': row.get('course_image'),
                        'enrollment_start': parse_date(row.get('enrollment_start')),
                        'enrollment_end': parse_date(row.get('enrollment_end')),
                        'study_start': parse_date(row.get('study_start')),
                        'study_end': parse_date(row.get('study_end')),
                        'week': parse_float(row.get('week')),
                        'course_playtime': parse_float(row.get('course_playtime')),
                    }

                    # kmooc_id로 기존 객체 확인
                    kmooc_id = row['id']
                    course = Course.objects.filter(kmooc_id=kmooc_id).first()

                    if course:
                        # 이미 존재하면 raw_summary가 비어있는 경우에만 업데이트
                        if not course.raw_summary:
                            course.raw_summary = row.get('raw_summary')
                            course.save(update_fields=['raw_summary'])
                            updated_count += 1
                    else:
                        # 없으면 새로 생성
                        Course.objects.create(kmooc_id=kmooc_id, **course_data)
                        created_count += 1
                    
                    count += 1
                    if count % 100 == 0:
                        self.stdout.write(f'Processed {count} courses...')

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row ID {row.get('id')}: {str(e)}"))

            self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} courses.'))
            self.stdout.write(self.style.SUCCESS(f'Created: {created_count}, Updated: {updated_count}'))
