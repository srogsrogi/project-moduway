# apps/comparisons/management/commands/load_ai_reviews.py

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from apps.courses.models import Course
from apps.comparisons.models import CourseAIReview

"""
[설계의도]
- CSV 백업 파일에서 CourseAIReview 데이터를 DB로 로드하는 Django management command
- 대량 데이터 복원 시 트랜잭션 처리와 에러 핸들링을 통해 안전성 확보

[상세 고려사항]
- CSV 파일은 data/backups/ 디렉토리에 위치
- 이미 존재하는 AI 리뷰는 update_or_create로 덮어쓰기 (--force 옵션 없이도 항상 upsert)
- course_id로 Course를 조회하고 존재하지 않으면 스킵
- 배치 처리 시 부분 실패를 허용하여 전체 작업 중단 방지
- 진행 상황을 stdout으로 출력하여 모니터링 가능
"""

class Command(BaseCommand):
    help = 'CSV 백업 파일에서 CourseAIReview 데이터를 DB로 로드'

    def add_arguments(self, parser):
        """
        [설계의도]
        - CSV 파일명을 인자로 받아 유연하게 사용
        - 기본값으로 ai_reviews.csv 지정
        """
        parser.add_argument(
            '--file',
            type=str,
            default='ai_reviews.csv',
            help='로드할 CSV 파일명 (data/backups/ 하위)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='트랜잭션 배치 크기 (기본: 100)'
        )

    def handle(self, *args, **options):
        """
        CSV 파일을 읽어서 CourseAIReview 데이터를 DB에 로드
        """
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CourseAIReview 데이터 로드 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # 1. CSV 파일 경로 설정
        project_root = settings.BASE_DIR.parent
        backup_dir = os.path.join(project_root, 'data', 'backups')
        csv_path = os.path.join(backup_dir, options['file'])

        if not os.path.exists(csv_path):
            raise CommandError(f'CSV 파일을 찾을 수 없습니다: {csv_path}')

        self.stdout.write(f'\n파일: {csv_path}')

        # 2. CSV 파일 읽기 및 처리
        success_count = 0
        error_count = 0
        skip_count = 0
        batch_size = options['batch_size']

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                total_count = sum(1 for _ in open(csv_path, encoding='utf-8-sig')) - 1  # 헤더 제외

                self.stdout.write(f'총 {total_count}개 레코드 처리 시작\n')

                # 파일 포인터 리셋
                f.seek(0)
                reader = csv.DictReader(f)

                batch = []
                for idx, row in enumerate(reader, 1):
                    try:
                        # course_id로 Course 조회
                        course_id = int(row['course_id'])

                        try:
                            course = Course.objects.get(id=course_id)
                        except Course.DoesNotExist:
                            skip_count += 1
                            if idx % 100 == 0:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'[{idx}/{total_count}] Course {course_id} 없음 - 스킵'
                                    )
                                )
                            continue

                        # CourseAIReview 데이터 준비
                        ai_review_data = {
                            'course_summary': row['course_summary'][:1000],  # max_length 제한
                            'average_rating': float(row['average_rating']),
                            'theory_rating': int(row['theory_rating']),
                            'practical_rating': int(row['practical_rating']),
                            'difficulty_rating': int(row['difficulty_rating']),
                            'duration_rating': int(row['duration_rating']),
                            'model_version': 'gpt-4o-mini',
                            'prompt_version': 'v2.1'
                        }

                        batch.append((course, ai_review_data))

                        # 배치 처리
                        if len(batch) >= batch_size:
                            created, updated = self._process_batch(batch)
                            success_count += created + updated
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'[{idx}/{total_count}] 배치 처리 완료 '
                                    f'(생성: {created}, 업데이트: {updated})'
                                )
                            )
                            batch = []

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'[{idx}/{total_count}] 에러 발생 (Course {row.get("course_id")}): {str(e)}'
                            )
                        )
                        continue

                # 남은 배치 처리
                if batch:
                    created, updated = self._process_batch(batch)
                    success_count += created + updated
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{total_count}/{total_count}] 최종 배치 처리 완료 '
                            f'(생성: {created}, 업데이트: {updated})'
                        )
                    )

        except Exception as e:
            raise CommandError(f'CSV 파일 읽기 실패: {str(e)}')

        # 3. 결과 요약
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('작업 완료'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'✓ 성공: {success_count}개')
        self.stdout.write(f'⊘ 스킵: {skip_count}개 (Course 없음)')
        self.stdout.write(f'✗ 실패: {error_count}개')
        self.stdout.write(f'총 처리: {success_count + skip_count + error_count}개\n')

    def _process_batch(self, batch):
        """
        배치 단위로 DB 저장 처리 (트랜잭션)

        Args:
            batch: [(course, ai_review_data), ...] 리스트

        Returns:
            tuple: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for course, ai_review_data in batch:
                _, created = CourseAIReview.objects.update_or_create(
                    course=course,
                    defaults=ai_review_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        return created_count, updated_count
