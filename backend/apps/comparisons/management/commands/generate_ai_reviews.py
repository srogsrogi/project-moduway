# apps/comparisons/management/commands/generate_ai_reviews.py

import os
import json
import time
import requests
import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from apps.courses.models import Course
from apps.comparisons.models import CourseAIReview

"""
[설계의도]
- 모든 강좌(Course)에 대해 LLM 기반의 'AI 평가(CourseAIReview)'를 생성/저장하는 Django management command
- 테스트/운영 상황에 맞게 처리 범위를 제어(--limit, --course-id)하고,
  재생성 정책을 선택(--force)하며,
  호출 속도 제한(--delay)으로 API Rate Limit을 피하도록 설계

[상세 고려사항]
- API 키는 코드에 하드코딩하지 않고 환경변수(GMS_KEY)로 주입하여 보안/운영 편의성을 확보
- 이미 평가가 존재하는 강좌는 기본적으로 스킵(ai_review__isnull=True)하여 비용/시간을 절감
  (단, --force 옵션이면 update_or_create로 덮어쓰기)
- 각 강좌별 DB 저장은 transaction.atomic()으로 감싸
  부분 저장/불완전 저장을 방지하고 원자성을 확보
- 실패한 강좌는 전체 작업을 중단하지 않고 continue로 넘어가
  "대량 처리 배치 작업"에서 흔한 부분 실패 허용 전략 적용
- LLM 응답은 JSON 모드(response_format=json_object)를 사용하고,
  추가로 json.loads + 필수 필드/점수 범위 검증을 통해 데이터 품질을 방어
- 생성된 결과를 CSV 파일로 내보낼 수 있는 기능 추가 (--output)
"""

MODEL_VERSION = 'gpt-4o-mini'
PROMPT_VERSION = 'v2.1'

class Command(BaseCommand):
    help = 'LLM을 사용하여 모든 강좌에 대한 AI 평가 생성'

    # 클래스 상수 - 중복 제거 및 유지보수성 향상
    # LLM이 평가하는 필드 (duration은 코드로 직접 계산)
    LLM_RATING_FIELDS = [
        'theory_rating',
        'practical_rating',
        'difficulty_rating',
    ]

    # 전체 rating 필드 (평균 계산에 사용)
    RATING_FIELDS = LLM_RATING_FIELDS + ['duration_rating']

    REQUIRED_FIELDS = ['course_summary'] + LLM_RATING_FIELDS

    # CourseAIReview 모델의 course_summary 필드 max_length 기준
    SUMMARY_MAX_LENGTH = 999

    # 배치 설정
    CSV_BATCH_SIZE = 50  # CSV 중간 저장 간격

    # LLM 설정
    LLM_TEMPERATURE = 0.3  # 일관된 평가를 위해 낮은 temperature
    LLM_MAX_TOKENS = 800   # 충분한 응답 생성을 위한 토큰 수

    # CSV 필드 순서 고정 (헤더 일관성 보장)
    CSV_FIELDNAMES = [
        'course_id',
        'course_name',
        'course_summary',
        'average_rating',
        'theory_rating',
        'practical_rating',
        'difficulty_rating',
        'duration_rating',
        'reason_theory',
        'reason_practical',
        'reason_difficulty',
        'reason_duration',
    ]

    def add_arguments(self, parser):
        """
        [설계의도]
        - 배치 작업에서 흔히 필요한 "범위 제어/재실행 정책/속도 제한"을 CLI 옵션으로 제공

        [상세 고려사항]
        - --limit: 개발/테스트 시 일부만 돌려 빠르게 검증할 수 있도록 함
        - --force: 이미 평가가 있어도 다시 생성(업데이트)할 수 있도록 함
        - --course-id: 특정 강좌 1개만 대상으로 디버깅/테스트 가능
        - --delay: API rate limit 및 서버 부하 완화를 위해 호출 간 sleep 제어
        - --output: 결과를 CSV 파일로 저장할 파일명 (data/backups/ 하위에 생성)
        """
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 강좌 수 제한 (테스트용)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 평가가 있는 강좌도 재생성'
        )
        parser.add_argument(
            '--course-id',
            type=int,
            default=None,
            help='특정 강좌만 평가 (테스트용)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='API 호출 간 대기 시간 (초)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='결과를 저장할 CSV 파일명 (예: ai_reviews_backup.csv)'
        )

    def handle(self, *args, **options):
        """
        [설계의도]
        - 커맨드 실행 시 전체 제어 흐름(설정 → 대상 추출 → 반복 처리 → 결과 요약)을 담당하는 엔트리포인트

        [상세 고려사항]
        - stdout에 진행률/성공/실패를 출력해 배치 실행 로그로 활용 가능
        - 강좌 단위로 try/except 처리하여 일부 실패가 전체를 중단시키지 않도록 함
        """
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('강좌 AI 평가 생성 시작'))
        self.stdout.write(self.style.SUCCESS('=' * 70))

        # =============================================
        # 1. GMS API 설정
        # =============================================
        gms_url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
        gms_key = os.environ.get("GMS_KEY")

        if not gms_key:
            raise CommandError('GMS_KEY 환경변수가 설정되지 않았습니다.')

        # =============================================
        # 2. 처리할 강좌 필터링
        # =============================================
        if options['course_id']:
            courses = Course.objects.filter(id=options['course_id'])
            if not courses.exists():
                raise CommandError(f"ID {options['course_id']} 강좌를 찾을 수 없습니다.")
        elif options['force']:
            courses = Course.objects.all()
        else:
            courses = Course.objects.filter(ai_review__isnull=True)

        if options['limit']:
            courses = courses[:options['limit']]

        total_count = courses.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('처리할 강좌가 없습니다.'))
            return

        self.stdout.write(f'\n총 {total_count}개 강좌 처리 시작\n')

        # =============================================
        # 3. 통계 및 파일 설정 변수
        # =============================================
        success_count = 0
        error_count = 0
        batch_results = []

        output_path = None
        if options['output']:
            project_root = settings.BASE_DIR.parent
            backup_dir = os.path.join(project_root, 'data', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            output_path = os.path.join(backup_dir, options['output'])

        # =============================================
        # 4. 각 강좌 처리
        # =============================================
        for idx, course in enumerate(courses, 1):
            self.stdout.write(f'\n[{idx}/{total_count}] 처리 중: {course.name} (ID: {course.id})')

            try:
                # LLM 호출하여 AI 평가 생성
                ai_review_data = self._generate_ai_review(course, gms_url, gms_key)

                # DB 저장
                with transaction.atomic():
                    review_data = self._prepare_review_data(ai_review_data)
                    review_data.update({
                        'model_version': MODEL_VERSION,
                        'prompt_version': PROMPT_VERSION
                    })

                    ai_review, created = CourseAIReview.objects.update_or_create(
                        course=course,
                        defaults=review_data
                    )

                # CSV용 데이터 수집
                if output_path:
                    csv_data = self._prepare_csv_data(course, ai_review_data)
                    batch_results.append(csv_data)

                action = '생성' if created else '업데이트'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {action} 완료 - 종합: {ai_review_data["average_rating"]}/5'
                    )
                )

                success_count += 1

                # 중간 저장
                if output_path and len(batch_results) >= self.CSV_BATCH_SIZE:
                    self._save_to_csv(output_path, batch_results)
                    self.stdout.write(self.style.WARNING(f'  💾 중간 저장 완료 ({success_count}개)'))
                    batch_results = []

                # Rate Limiting
                if idx < total_count:
                    time.sleep(options['delay'])

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ 에러 발생: {str(e)}'))
                continue

        # =============================================
        # 5. 남은 잔여 데이터 저장
        # =============================================
        if output_path and batch_results:
            self._save_to_csv(output_path, batch_results)
            self.stdout.write(self.style.SUCCESS(f'\n✓ 최종 CSV 저장 완료: {output_path}'))

        # 6. 결과 요약
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('작업 완료'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'✓ 성공: {success_count}개')
        self.stdout.write(f'✗ 실패: {error_count}개')
        if options['output']:
            self.stdout.write(f'📁 파일: {options["output"]}')
        self.stdout.write(f'총 처리: {success_count + error_count}개\n')

    def _calculate_duration_rating(self, week):
        """
        주차 수를 기반으로 학습 기간 평점 계산

        Args:
            week: 강좌 주차 수

        Returns:
            int: 1-5 범위의 학습 기간 평점
        """
        if not week:
            return 3  # 기본값: 중간

        if week <= 4:
            return 1
        elif week <= 8:
            return 2
        elif week <= 12:
            return 3
        elif week <= 16:
            return 4
        else:
            return 5

    def _prepare_review_data(self, ai_review_data):
        """
        AI 리뷰 데이터를 DB 저장 형식으로 변환

        Args:
            ai_review_data: LLM으로부터 받은 평가 데이터

        Returns:
            dict: DB 저장용 데이터
        """
        data = {
            'course_summary': ai_review_data['course_summary'][:self.SUMMARY_MAX_LENGTH],
            'average_rating': ai_review_data['average_rating'],
        }

        # Rating 필드 추가
        for field in self.RATING_FIELDS:
            data[field] = ai_review_data[field]

        return data

    def _prepare_csv_data(self, course, ai_review_data):
        """
        AI 리뷰 데이터를 CSV 저장 형식으로 변환

        Args:
            course: Course 인스턴스
            ai_review_data: LLM으로부터 받은 평가 데이터

        Returns:
            dict: CSV 저장용 데이터
        """
        csv_data = {
            'course_id': course.id,
            'course_name': course.name,
            'course_summary': ai_review_data['course_summary'],
            'average_rating': ai_review_data['average_rating'],
        }

        # Rating 필드 추가
        for field in self.RATING_FIELDS:
            csv_data[field] = ai_review_data[field]

        # Reasoning 필드 추가 (선택사항)
        reasoning = ai_review_data.get('reasoning', {})
        csv_data.update({
            'reason_theory': reasoning.get('theory', ''),
            'reason_practical': reasoning.get('practical', ''),
            'reason_difficulty': reasoning.get('difficulty', ''),
            'reason_duration': '',  # Duration은 코드로 계산하므로 reasoning 없음
        })

        return csv_data

    def _save_to_csv(self, file_path, data_list):
        """
        데이터 리스트를 CSV 파일에 추가 저장

        Args:
            file_path: 저장할 파일 경로
            data_list: 저장할 데이터 리스트
        """
        if not data_list:
            return

        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerows(data_list)

    def _generate_ai_review(self, course, gms_url, gms_key):
        """
        LLM을 호출하여 강좌 평가 생성 (메인 로직)

        Args:
            course: Course 인스턴스
            gms_url: GMS API URL
            gms_key: GMS API 키

        Returns:
            dict: AI 평가 데이터
        """
        system_prompt, user_prompt = self._build_prompts(course)
        response_data = self._call_gms_api(gms_url, gms_key, system_prompt, user_prompt)
        ai_review = self._parse_and_validate_response(response_data)

        # Duration rating을 코드로 직접 계산하여 추가
        ai_review['duration_rating'] = self._calculate_duration_rating(course.week)

        # Duration 포함하여 평균 재계산
        total_rating = sum(ai_review[field] for field in self.RATING_FIELDS)
        ai_review['average_rating'] = round(total_rating / len(self.RATING_FIELDS), 2)

        return ai_review

    def _build_prompts(self, course):
        """
        강좌 정보를 기반으로 System/User 프롬프트 생성

        Args:
            course: Course 인스턴스

        Returns:
            tuple: (system_prompt, user_prompt)
        """
        # 데이터 전처리: 초 단위를 시간 단위로 변환
        total_playtime_hours = round(course.course_playtime / 3600.0, 1) if course.course_playtime else 0

        system_prompt = """당신은 K-MOOC 온라인 강좌 평가 전문가입니다.
주어진 강좌 정보를 분석하여 객관적이고 일관된 평가를 제공해야 합니다.

평가 기준 (모든 항목은 1-5 범위의 정수):
1. 이론적 깊이 (theory_rating): 개념과 원리의 깊이
   - 1-2: 매우 기초적, 개념 소개 수준
   - 3: 중급, 원리와 개념 설명
   - 4-5: 고급, 심화 이론 및 수학적 증명 포함

2. 실무적 활용도 (practical_rating): 실무 적용 가능성
   - 1-2: 이론 중심, 실습 거의 없음
   - 3: 기본 실습 포함
   - 4-5: 프로젝트 중심, 포트폴리오 제작 가능

3. 학습 난이도 (difficulty_rating): 학습자 요구 수준
   - 1-2: 입문자용, 비전공자 가능
   - 3: 중급, 기본 지식 필요
   - 4-5: 고급, 전문 지식 필수"""

        user_prompt = f"""다음 K-MOOC 강좌를 분석하여 평가해주세요:

**강좌 기본 정보**
- 강좌명: {course.name}
- 운영 기관: {course.org_name or 'N/A'}
- 교수자: {course.professor or 'N/A'}
- 분류: {course.classfy_name} > {course.middle_classfy_name}

**강좌 규모**
- 주차 수: {course.week or 'N/A'}주
- 총 영상 시간: {total_playtime_hours}시간

**강좌 설명**
{course.summary or '설명 없음'}

위 정보를 바탕으로 다음 JSON 형식으로 평가를 제공하세요:
{{
  "course_summary": "강좌의 핵심 내용과 학습 목표를 2-3문장으로 요약",
  "theory_rating": 3,
  "practical_rating": 2,
  "difficulty_rating": 3,
  "reasoning": {{
    "theory": "이론 점수 근거 (1문장)",
    "practical": "실무 점수 근거 (1문장)",
    "difficulty": "난이도 점수 근거 (1문장)"
  }}
}}

참고: 모든 rating 값은 1-5 범위의 정수여야 합니다."""

        return system_prompt, user_prompt

    def _call_gms_api(self, gms_url, gms_key, system_prompt, user_prompt):
        """
        GMS API를 호출하여 LLM 응답 받기

        Args:
            gms_url: GMS API URL
            gms_key: GMS API 키
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트

        Returns:
            dict: API 응답 데이터

        Raises:
            Exception: API 호출 실패 시
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gms_key}"
        }

        data = {
            "model": MODEL_VERSION,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": self.LLM_TEMPERATURE,
            "max_tokens": self.LLM_MAX_TOKENS
        }

        response = requests.post(
            gms_url,
            headers=headers,
            data=json.dumps(data),
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(
                f"GMS API 호출 실패 (Status: {response.status_code}): {response.text[:200]}"
            )

        return response.json()

    def _parse_and_validate_response(self, response_data):
        """
        LLM 응답을 파싱하고 검증

        Args:
            response_data: API 응답 데이터

        Returns:
            dict: 검증된 AI 평가 데이터

        Raises:
            Exception: 파싱 실패 또는 검증 실패 시
        """
        content = response_data['choices'][0]['message']['content']

        # JSON 파싱
        try:
            ai_review = json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 실패: {content[:200]}...")

        # 필수 필드 검증
        for field in self.REQUIRED_FIELDS:
            if field not in ai_review:
                raise Exception(f"필수 필드 누락: {field}")

        # LLM이 생성한 점수 범위 검증
        for field in self.LLM_RATING_FIELDS:
            value = ai_review[field]
            if not isinstance(value, int) or value < 1 or value > 5:
                raise Exception(
                    f"{field} 값이 유효하지 않음: {value} (1-5 사이의 정수여야 함)"
                )

        return ai_review
