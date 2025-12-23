import json
import os
import ast
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.courses.models import Course


class Command(BaseCommand):
    help = 'Import courses with embeddings from JSON backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='courses_backup.json',
            help='Input JSON filename (default: courses_backup.json)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing courses before import (WARNING: deletes all existing data)'
        )

    def handle(self, *args, **options):
        input_filename = options['input']
        clear_existing = options['clear']

        # 파일 경로: project-moduway/data/backups/
        base_dir = settings.BASE_DIR
        project_root = base_dir.parent
        backup_dir = os.path.join(project_root, 'data', 'backups')
        input_path = os.path.join(backup_dir, input_filename)

        if not os.path.exists(input_path):
            self.stdout.write(self.style.ERROR(f'Backup file not found: {input_path}'))
            return

        self.stdout.write(f'Reading backup from: {input_path}')

        # 기존 데이터 삭제 옵션
        if clear_existing:
            existing_count = Course.objects.count()
            if existing_count > 0:
                confirm = input(
                    f'This will delete {existing_count} existing courses. '
                    'Type "yes" to confirm: '
                )
                if confirm.lower() == 'yes':
                    Course.objects.all().delete()
                    self.stdout.write(self.style.WARNING(f'Deleted {existing_count} existing courses.'))
                else:
                    self.stdout.write(self.style.ERROR('Import cancelled.'))
                    return

        # JSON 파일 읽기
        with open(input_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        total_count = len(import_data)
        self.stdout.write(f'Found {total_count} courses in backup file...')

        # 날짜/시간 파싱 헬퍼 함수
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # ISO 형식(2025-12-22) 또는 상세 형식 대응
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
            except (ValueError, AttributeError):
                return None

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for idx, course_data in enumerate(import_data, 1):
            try:
                # Django dumpdata 형식은 실제 데이터가 'fields' 키 안에 있음
                fields = course_data.get('fields', {})
                
                # kmooc_id 추출
                kmooc_id = fields.get('kmooc_id')
                if not kmooc_id:
                    self.stdout.write(
                        self.style.WARNING(f'Skipped entry {idx}: missing kmooc_id in fields')
                    )
                    skipped_count += 1
                    continue

                # 임베딩 처리 (문자열 형태 "[...]"인 경우 리스트로 변환)
                embedding = fields.get('embedding')
                if isinstance(embedding, str):
                    try:
                        embedding = ast.literal_eval(embedding)
                    except (ValueError, SyntaxError):
                        self.stdout.write(self.style.ERROR(f'Failed to parse embedding for {kmooc_id}'))
                        embedding = None

                if embedding and isinstance(embedding, list) and len(embedding) != 1536:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Warning: Course {kmooc_id} has embedding with {len(embedding)} dimensions'
                        )
                    )

                # Course 데이터 매핑 (fields에서 데이터 추출)
                course_fields = {
                    'name': fields.get('name', ''),
                    'content_key': fields.get('content_key'),
                    'professor': fields.get('professor'),
                    'org_name': fields.get('org_name'),
                    'certificate_yn': fields.get('certificate_yn'),
                    'classfy_name': fields.get('classfy_name'),
                    'middle_classfy_name': fields.get('middle_classfy_name'),
                    'summary': fields.get('summary'),
                    'raw_summary': fields.get('raw_summary'), # 추가됨
                    'url': fields.get('url'),
                    'course_image': fields.get('course_image'),
                    'enrollment_start': parse_date(fields.get('enrollment_start')),
                    'enrollment_end': parse_date(fields.get('enrollment_end')),
                    'study_start': parse_date(fields.get('study_start')),
                    'study_end': parse_date(fields.get('study_end')),
                    'week': fields.get('week'),
                    'course_playtime': fields.get('course_playtime'),
                    'embedding': embedding,
                }

                # kmooc_id 기준으로 업데이트 또는 생성
                obj, created = Course.objects.update_or_create(
                    kmooc_id=kmooc_id,
                    defaults=course_fields
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

                if (created_count + updated_count) % 100 == 0:
                    self.stdout.write(
                        f'Processed {created_count + updated_count}/{total_count} courses...'
                    )

            except Exception as e:
                skipped_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing entry {idx} (kmooc_id: {course_data.get("fields", {}).get("kmooc_id")}): {e}'
                    )
                )

        self.stdout.write(self.style.SUCCESS(f'\nImport completed!'))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
