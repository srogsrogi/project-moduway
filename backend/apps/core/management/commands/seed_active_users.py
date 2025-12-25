"""
가짜 데이터 생성 커맨드

[설계 의도]
- 강좌(Course)는 생성하지 않고 기존 DB의 강좌 참조
- User 생성 → 지정한 강좌들에 대해 왕성하게 활동
- 커뮤니티 활동 강화 (게시글/댓글/대댓글/스크랩/좋아요)

[사용 예시]
```bash
# 이동
cd /Users/najung/Desktop/git/project-moduway/backend

# 처음 10개 강좌 사용
python manage.py seed_active_users --users 50
# 특정 강좌 ID들 사용
python manage.py seed_active_users --users 100 --course-ids "1,2,3,4,5"

# 모든 강좌 사용
python manage.py seed_active_users --users 200 --all-courses

# 커뮤니티 활동 강화
python manage.py seed_active_users --users 100 --course-ids "1,2,3" --posts-per-user 10

# 기존 데이터 삭제 후 재생성
python manage.py seed_active_users --users 100 --course-ids "1,2,3,4,5" --flush
```
"""
import random
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings

# 모델 임포트
from apps.accounts.models import User, UserConsent, EmailVerification
from apps.community.models import Board, Post, Comment, PostLike, Scrap
from apps.courses.models import Course, Enrollment, Wishlist, CourseReview
from apps.comparisons.models import CourseAIReview

# 헬퍼 함수 임포트
from apps.core.utils.fake_data_helpers import (
    fake,
    BOARD_DATA,
    random_date_between,
    random_datetime_between,
    weighted_choice,
    gaussian_int,
    generate_unique_username,
    generate_unique_email,
)

BATCH_SIZE = 1000
DEFAULT_PASSWORD = 'testpass123'

# 하드코딩 방지용 상수
MAX_USERS = 1000
DEFAULT_COURSE_LIMIT = 10
USER_JOIN_LOOKBACK_DAYS = 365
POST_ACTIVITY_LOOKBACK_DAYS = 180
BOARD_SERVICE_LOOKBACK_DAYS = 730
EMAIL_VERIFY_LOOKBACK_DAYS_MAX = 7
EMAIL_VERIFY_EXPIRE_HOURS = 24

class RealisticReviewGenerator:
    """
    [개선된 버전] 문맥(Context)을 고려하여 말이 되는 조합만 생성하는 클래스
    """

    # 긍정/부정 비율 패턴 (긍정수, 부정수, 확률)
    SENTIMENT_PATTERNS = [
        (3, 0, 0.4),  # 완전 긍정 40%
        (2, 1, 0.4),  # 대체로 긍정 40%
        (1, 1, 0.15), # 중립 15%
        (1, 2, 0.05), # 부정 5%
    ]

    # =========================================================================
    # 1. 서론 & 결론 (얘네는 범용적이라 섞어도 됨)
    # =========================================================================
    intro_times = [
        "최근에", "예전부터", "이번 달에", "급하게", "여유가 생겨서",
        "주말을 이용해서", "퇴근하고 틈틈이", "방학 기간 동안", "프로젝트 시작 전에", "이직 준비 기간에"
    ]
    intro_motivations = [
        "부족한 기초를 채우고 싶어서", "실무 스킬업이 필요해서", "지인의 강력한 추천으로",
        "커리큘럼이 너무 마음에 들어서", "유튜브로 독학하다 한계를 느껴서", "새로운 분야에 도전해보고 싶어서",
        "회사 업무에 바로 적용해야 해서", "코딩 테스트 대비를 위해", "포트폴리오 퀄리티를 높이려고",
        "유명한 강사님이라 믿고", "기존 지식을 정리하고 싶어서", "가장 리뷰가 좋길래",
        "할인 이벤트를 하길래", "팀원들과 스터디하려고", "기본기가 흔들리는 것 같아서"
    ]
    intro_actions = [
        "수강을 시작했습니다.", "결제하게 되었습니다.", "듣게 되었네요.", "신청했습니다.",
        "선택했는데 후회 없습니다.", "시작해 보았습니다.", "정주행을 시작했습니다.",
        "큰 맘 먹고 질렀습니다.", "수강신청 버튼을 눌렀습니다.", "학습을 시작했습니다."
    ]

    outros = [
        "전반적으로 만족스러운 강의였고 다른 분들께도 추천하고 싶습니다.", "가격 대비 퀄리티가 훌륭해서 돈이 아깝지 않은 선택이었습니다.",
        "이 분야에 입문하고 싶은 분들이라면 이 강의만 들어도 충분해요.", "완강하고 나니 큰 그림이 그려지네요. 정말 감사합니다!",
        "고민하고 계신 분들이 있다면 주저 말고 수강하시길 추천드립니다.", "앞으로 나올 강사님의 다음 시리즈 강의도 기대가 되네요.",
        "제 인생 강의 중 하나로 꼽고 싶을 만큼 유익한 시간이었습니다.", "꾸준히 반복해서 들으면 실력 향상에 큰 도움이 될 것 같아요.",
        "실무 역량을 키우고 싶은 주니어들에게 강력하게 추천하는 바입니다.", "기초를 다지기에 이보다 더 좋은 강의는 없을 것 같네요."
    ]

    # =========================================================================
    # 2. 본론 (카테고리별 분리 - 핵심 로직)
    # 같은 키(key) 안에 있는 주어와 서술어끼리만 만남
    # =========================================================================
    context_data = {
        # [그룹 A] 전달력/강사 스타일 (목소리, 발음, 속도 등)
        'delivery': {
            'subjects': [
                "강사님의 목소리 톤이", "전반적인 딕션이", "설명하는 속도가", "강의 전달력이",
                "말씀하시는 스타일이", "귀에 꽂히는 발성이"
            ],
            'modifiers': [
                "정말", "기대 이상으로", "생각보다 훨씬", "무엇보다", "압도적으로",
                "놀라울 정도로", "확실히", "특히", "솔직히 말해서", "누가 들어도 편안할 만큼"
            ],
            'predicates': [
                "귀에 쏙쏙 박힙니다.", "듣기 편안합니다.", "졸리지 않게 해줍니다.",
                "집중력을 잃지 않게 도와줍니다.", "배속으로 들어도 명확합니다.", "아나운서 같습니다."
            ],
            # 부정문 (단점) - 3배 확장
            'neg_subjects': [
                "다만 말의 속도가", "가끔 발음이", "목소리 크기가", "마이크 상태가",
                "억양이", "호흡이", "말투가", "강세 패턴이",
                "설명 템포가", "쉬는 타이밍이", "음색이", "톤 변화가"
            ],
            'neg_predicates': [
                "조금 빠른 감이 있습니다.", "약간 작게 들릴 때가 있습니다.", "가끔 뭉개지는 구간이 있습니다.",
                "단조로운 편입니다.", "어색할 때가 있습니다.", "불규칙합니다.",
                "다소 어눌하게 느껴집니다.", "집중하기 어려울 수 있습니다.", "개선의 여지가 있습니다."
            ]
        },

        # [그룹 B] 자료/시각적 요소 (PPT, 코드, 화질)
        'material': {
            'subjects': [
                "강의 자료 퀄리티가", "제공되는 PPT가", "실습 예제 코드가", "화면 구성이",
                "자막과 스크립트가", "영상 화질이", "판서 내용이"
            ],
            'modifiers': [
                "정말", "매우", "상당히", "깔끔하고", "체계적이고",
                "가독성 좋게", "보기 편하게", "세심하게"
            ],
            'predicates': [
                "가독성이 좋습니다.", "복습하기에 최적입니다.", "정리가 잘 되어 있습니다.",
                "군더더기 없이 깔끔합니다.", "눈에 확 들어옵니다.", "따라 치기 편합니다."
            ],
            # 부정문 (단점) - 3배 확장
            'neg_subjects': [
                "교안의 일부 오타가", "화면 글씨 크기가", "코드 해상도가", "자료 다운로드 속도가",
                "PPT 디자인이", "예제 파일 구성이", "자막 싱크가", "색상 대비가",
                "도표 가독성이", "파일 용량이", "레이아웃이", "첨부 자료 정리가"
            ],
            'neg_predicates': [
                "조금 거슬릴 수 있습니다.", "모바일에서는 작게 보입니다.", "수정이 필요해 보입니다.",
                "아쉬운 부분입니다.", "불편할 때가 있습니다.", "개선되면 좋겠습니다.",
                "다소 부족한 감이 있습니다.", "보완이 필요합니다.", "만족스럽지 못했습니다."
            ]
        },

        # [그룹 C] 내용/커리큘럼 (난이도, 깊이, 실무활용)
        'content': {
            'subjects': [
                "전체적인 커리큘럼이", "이론과 실습 비율이", "실무 관련 꿀팁들이",
                "챕터별 요약 정리가", "초반 빌드업 과정이", "다루는 내용의 깊이가"
            ],
            'modifiers': [
                "알차고", "탄탄하고", "빈틈없고", "실용적이고",
                "체계적이고", "논리적이고", "단계별로"
            ],
            'predicates': [
                "실무에 바로 쓸 수 있겠네요.", "돈이 전혀 아깝지 않습니다.", "이해하기 쉽게 구성되었습니다.",
                "많은 통찰력을 줍니다.", "성취감을 느끼게 해줍니다.", "완벽에 가깝습니다."
            ],
            # 부정문 (단점) - 3배 확장
            'neg_subjects': [
                "초반 진도가", "후반부 난이도가", "실습 환경 세팅이", "설명의 깊이가",
                "과제 난이도가", "예제 선택이", "커리큘럼 순서가", "실무 연계가",
                "심화 내용이", "기초 설명이", "프로젝트 난이도가", "학습 분량이"
            ],
            'neg_predicates': [
                "조금 가파르게 느껴집니다.", "초보자에겐 어려울 수 있습니다.", "다소 불친절하게 느껴졌습니다.",
                "아쉬운 점이 있습니다.", "부족하다고 생각합니다.", "개선이 필요합니다.",
                "어렵게 느껴질 수 있습니다.", "쉽지 않습니다.", "재고해볼 필요가 있습니다."
            ]
        }
    }

    @classmethod
    def get_sentence_part(cls, category, type_key):
        """특정 카테고리(delivery, material, content)의 요소(주어, 수식어, 서술어)를 랜덤 반환"""
        return random.choice(cls.context_data[category][type_key])

    @classmethod
    def generate_review(cls):
        # 1. 서론
        intro = f"{random.choice(cls.intro_times)} {random.choice(cls.intro_motivations)} {random.choice(cls.intro_actions)}"

        # 2. 긍정/부정 비율 선택 (weighted random)
        patterns = cls.SENTIMENT_PATTERNS
        total_weight = sum(p[2] for p in patterns)
        rand_val = random.uniform(0, total_weight)

        cumulative = 0
        num_positive, num_negative = 2, 1  # 기본값
        for pos, neg, weight in patterns:
            cumulative += weight
            if rand_val <= cumulative:
                num_positive, num_negative = pos, neg
                break

        # 3. 본론 생성
        categories = list(cls.context_data.keys())

        # 긍정/부정 문장에서 사용할 카테고리 선택
        total_sentences = num_positive + num_negative
        picked_cats = random.sample(categories, min(total_sentences, len(categories)))
        if len(picked_cats) < total_sentences:
            # 카테고리가 부족하면 반복 사용
            picked_cats.extend(random.choices(categories, k=total_sentences - len(picked_cats)))

        # 긍정 문장 생성
        positive_sentences = []
        positive_cats = picked_cats[:num_positive]
        for cat in positive_cats:
            subj = cls.get_sentence_part(cat, 'subjects')
            mod = cls.get_sentence_part(cat, 'modifiers')
            pred = cls.get_sentence_part(cat, 'predicates')
            positive_sentences.append(f"{subj} {mod} {pred}")

        # 부정 문장 생성 (긍정에서 언급한 카테고리 중에서 선택 - 일관성 유지)
        negative_sentences = []
        if num_negative > 0:
            # 긍정 카테고리가 있으면 그 중에서 선택, 없으면 전체에서 선택
            neg_cats = positive_cats if positive_cats else categories
            for _ in range(num_negative):
                neg_cat = random.choice(neg_cats)
                neg_subj = cls.get_sentence_part(neg_cat, 'neg_subjects')
                neg_pred = cls.get_sentence_part(neg_cat, 'neg_predicates')
                negative_sentences.append(f"{neg_subj} {neg_pred}")

        # 4. 결론
        outro = random.choice(cls.outros)

        # 5. 합치기
        all_sentences = positive_sentences + negative_sentences
        body = " ".join(all_sentences)
        full_review = f"{intro} {body} {outro}"

        # 길이 보정
        if len(full_review) < 100:
             full_review += " 개인적으로 공부하면서 메모해둔 내용들이 실무에서 정말 큰 도움이 되고 있습니다."

        return full_review

class KoreanContentGenerator:
    """한글 게시글/댓글 생성기"""

    # 게시글 주제 템플릿
    POST_TOPICS = [
        "강의 추천", "질문", "후기", "스터디 모집", "정보 공유",
        "취업 준비", "프로젝트 공유", "공부 방법", "진로 상담", "자료 요청"
    ]

    # 제목 템플릿
    TITLE_TEMPLATES = [
        "{topic} 관련해서 질문 있습니다",
        "{topic} 어떻게 하시나요?",
        "{topic} 도움 부탁드립니다",
        "{topic} 경험 공유합니다",
        "{topic} 궁금한 점 있어요",
        "초보자 {topic} 질문드려요",
        "{topic} 추천 부탁드립니다",
        "{topic}에 대한 의견 나눠요",
        "{topic} 시작하려는데 조언 구합니다",
        "{topic} 같이 하실 분 계신가요?",
    ]

    # 본문 문장 풀
    CONTENT_SENTENCES = [
        "안녕하세요. 처음 글 올립니다.",
        "도움이 필요해서 글 남깁니다.",
        "이 분야를 공부한 지 얼마 안 됐는데요.",
        "여러분의 의견이 궁금합니다.",
        "경험 있으신 분들께 조언 구합니다.",
        "관련 자료를 찾다가 궁금한 점이 생겼어요.",
        "같은 고민을 하시는 분들이 계실까 싶어 공유합니다.",
        "효율적인 방법을 알고 싶습니다.",
        "시행착오를 줄이고 싶어서 문의드립니다.",
        "더 나은 방법이 있을까요?",
        "실무에서는 어떻게 적용하시나요?",
        "기초부터 차근차근 배우고 싶은데 추천 부탁드립니다.",
        "많은 분들의 조언 기다리겠습니다.",
        "미리 감사드립니다.",
    ]

    # 댓글 템플릿
    COMMENT_TEMPLATES = [
        "좋은 질문이네요!", "저도 궁금했던 부분입니다.", "도움이 되셨으면 좋겠어요.",
        "제 경험상 이렇게 하면 될 것 같아요.", "감사합니다! 참고할게요.",
        "좋은 정보 감사합니다.", "저도 비슷한 경험이 있어요.",
        "한번 시도해보시는 건 어떨까요?", "공감합니다!", "응원합니다!",
        "같이 공부하면 좋을 것 같네요.", "저도 관심 있습니다.",
        "유익한 글이네요.", "많이 배워갑니다.", "화이팅하세요!",
    ]

    @classmethod
    def generate_post_title(cls):
        """게시글 제목 생성"""
        topic = random.choice(cls.POST_TOPICS)
        template = random.choice(cls.TITLE_TEMPLATES)
        return template.format(topic=topic)

    @classmethod
    def generate_post_content(cls):
        """게시글 본문 생성"""
        num_sentences = random.randint(3, 6)
        sentences = random.sample(cls.CONTENT_SENTENCES, min(num_sentences, len(cls.CONTENT_SENTENCES)))
        return "\n\n".join(sentences)

    @classmethod
    def generate_comment(cls):
        """댓글 내용 생성"""
        return random.choice(cls.COMMENT_TEMPLATES)

SEED_CONFIG = {
    'USER': {
        'ACTIVE_RATE': 0.95,       # 활성 유저 비율
        'VERIFIED_RATE': 0.85,     # 이메일 인증 비율
        'LOGIN_RATE': 0.8,         # 최근 로그인 기록이 있을 확률
        'MARKETING_AGREE': 0.6,    # 마케팅 동의 비율
        'VERIFY_SAMPLE_RATE': 0.3, # 미인증 유저 중 인증 시도 데이터 생성 비율
    },
    'COMMUNITY': {
        'BOARD': {
            'MIN_POSTS_PER_BOARD': 1,     # 게시판당 최소 게시글 수
            'MAX_POSTS_PER_BOARD': 20,    # 게시판당 최대 게시글 수
        },
        'POST_UPDATE_RATE': 0.2,   # 게시글 수정 비율
        'COMMENT': {
            'AVG_PER_POST': 2,     # 게시글 당 평균 댓글 수
            'DEVIATION': 2,        # 표준편차
            'MIN': 0, 'MAX': 8,
            'UPDATE_RATE': 0.1,    # 댓글 수정 비율
        },
        'REPLY': {
            'TARGET_RATIO': 0.2,   # 전체 댓글 중 대댓글이 달릴 비율
            'COUNT_RANGE': (1, 2), # 대댓글 달릴 시 개수 범위
        },
        'LIKE': {
            'RATIO_MIN': 0.005,    # 유저 중 최소 0.5%가 좋아요
            'RATIO_MAX': 0.015,    # 유저 중 최대 1.5%가 좋아요
        },
        'SCRAP': {
            'AVG_PER_USER': 2,     # 유저당 평균 스크랩 수
            'DEVIATION': 2,        # 표준편차
            'MAX': 10,             # 최대 스크랩 수
        }
    },
    'COURSE': {
        'ENROLLMENT': {
            'RATE_MIN': 0.003,                                     # 유저당 최소 수강 강좌 비율 (전체 강좌 대비)
            'RATE_MAX': 0.06,                                      # 유저당 최대 수강 강좌 비율
            'STATUS_OPTS': ['enrolled', 'completed', 'dropped'],    # 수강 상태 옵션
            'STATUS_WEIGHTS': [0.5, 0.4, 0.1],                      # 수강중, 완강, 드랍 비율
            'PROGRESS': {
                'ENROLLED': (10, 85),                               # 수강중 진도율 범위
                'COMPLETED': (95, 100),                             # 완강 진도율 범위
                'DROPPED': (0, 40),                                 # 드랍 진도율 범위
            }
        },
        'WISHLIST': {
            'RATE_MIN': 0.15,            # 유저당 최소 위시리스트 강좌 비율
            'RATE_MAX': 0.45,            # 유저당 최대 위시리스트 강좌 비율
        },
        'REVIEW': {
            'WRITE_RATE': 1,                                        # 완강자 중 리뷰 작성 비율
            'LONG_TEXT_RATE': 0.8,                                    # 긴 리뷰 작성 확률
            'LONG_TEXT_PARAGRAPHS': (1,4),             # 긴 리뷰 단락 수
            'SHORT_TEXT_WORDS': (5, 20),                # 짧은 리뷰 단어 수
            'MIN_DAYS_AFTER_ENROLL': 20,                              # 수강 후 최소 일수
            'RATING': {'AVG': 4.3, 'DEV': 0.6, 'MIN': 1, 'MAX': 5}    # 평점 분포
        }
    }
}


class Command(BaseCommand):
    help = '가짜 데이터로 왕성한 유저 생성하기 (기존 강좌 활용하여)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=50,
            help='생성할 유저 수 (최대 1000명)'
        )
        parser.add_argument(
            '--course-ids',
            type=str,
            help='쉼표로 구분된 강좌 ID 목록 (예: "1,2,3,4,5")'
        )
        parser.add_argument(
            '--all-courses',
            action='store_true',
            help='DB의 모든 강좌 사용'
        )
        parser.add_argument(
            '--posts-per-user',
            type=int,
            default=5,
            help='유저당 평균 게시글 수 (기본값: 5)'
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='기존 가짜 데이터 삭제 후 시드 (강좌는 유지)'
        )

    # 0.0. 메인 핸들러
    def handle(self, *args, **options):
        # 프로덕션 보호
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR('에러 : 이 명령어는 DEBUG(로컬) 모드에서만 실행할 수 있습니다!')
            )
            return

        # 현재 시각 고정 (안전 마진 1초 포함)
        # timezone.now()를 여러 번 호출하면 시간차로 인한 에러 방지
        self.current_time = timezone.now() - timedelta(seconds=1)

        # 옵션 파싱
        num_users = min(options['users'], MAX_USERS)
        posts_per_user = options['posts_per_user']
        flush = options['flush']

        # 강좌 선택
        target_courses = self.get_target_courses(options)
        if not target_courses:
            self.stdout.write(self.style.ERROR('에러 : 사용할 강좌가 없습니다!'))
            return

        self.stdout.write(self.style.SUCCESS(f'선택된 강좌: {len(target_courses)}개'))
        for course in target_courses[:5]:  # 처음 5개만 표시
            self.stdout.write(f'  - [{course.id}] {course.name}')
        if len(target_courses) > 5:
            self.stdout.write(f'  ... 그리고 {len(target_courses) - 5}개 더 있습니다')
        # Flush 경고
        if flush:
            confirm = input('기존 유저/커뮤니티 데이터를 삭제합니다 (강좌는 유지). 계속할까요? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('중단되었습니다.'))
                return
            self.flush_data()

        # 데이터 생성 시작
        self.stdout.write(self.style.SUCCESS('가짜 데이터 생성 시작...'))
        self.stdout.write(f'유저 수: {num_users}, 유저당 평균 게시글 수: {posts_per_user}')

        try:
            with transaction.atomic():
                # Phase 1: User 생성
                users = self.create_users(num_users)                             # 유저
                self.create_user_consents(users)                                 # 유저 동의
                self.create_email_verifications(users)                           # 이메일 인증

                # Phase 2: 게시판 생성 (없으면)
                boards = self.ensure_boards()                                    # 게시판

                # Phase 3: 커뮤니티 활동 (왕성하게!)
                posts = self.create_posts(users, boards, posts_per_user)         # 게시글
                self.create_comments(users, posts)                               # 댓글
                self.create_post_likes(users, posts)                             # 좋아요
                self.create_scraps(users, posts)                                 # 스크랩

                # Phase 4: 강좌 활동 (지정된 강좌들에 대해)
                enrollments = self.create_enrollments(users, target_courses)     # 수강신청
                self.create_wishlists(users, target_courses, enrollments)        # 위시리스트
                reviews = self.create_course_reviews(enrollments)                # 강좌리뷰

            self.stdout.write(self.style.SUCCESS('가짜 데이터 생성 완료!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'에러: {str(e)}'))
            traceback.print_exc() 
            raise

    # 0.1. 강좌 선택
    def get_target_courses(self, options):
        """타겟 강좌 선택"""
        if options['all_courses']:
            # 모든 강좌 사용
            courses = list(Course.objects.all())
            self.stdout.write(f'DB의 모든 강좌 사용: {len(courses)}개')
            return courses

        elif options['course_ids']:
            # 지정된 ID 사용
            course_ids_str = options['course_ids']
            try:
                course_ids = [int(x.strip()) for x in course_ids_str.split(',')]
            except ValueError:
                raise CommandError('잘못된 강좌 ID 형식입니다. 쉼표로 구분된 정수 형식이어야 합니다 (예: "1,2,3")')

            courses = list(Course.objects.filter(id__in=course_ids))
            found_ids = [c.id for c in courses]
            missing_ids = set(course_ids) - set(found_ids)

            if missing_ids:
                self.stdout.write(
                    self.style.WARNING(f'경고: 찾을 수 없는 강좌 ID: {sorted(missing_ids)}')
                )

            return courses

        else:
            # 아무 옵션도 없으면 처음 10개 강좌 사용
            courses = list(Course.objects.all()[:DEFAULT_COURSE_LIMIT])
            if courses:
                self.stdout.write(
                    self.style.WARNING('강좌가 지정되지 않았습니다. 기본적으로 처음 10개 강좌를 사용합니다.')
                )
            return courses

    # 0.2. 기존 데이터 삭제
    def flush_data(self):
        """기존 데이터 삭제 (강좌 제외)"""
        self.stdout.write('기존 유저/커뮤니티 데이터 삭제 중 (강좌 유지)...')

        # 역순으로 삭제
        CourseAIReview.objects.all().delete()
        CourseReview.objects.all().delete()
        Wishlist.objects.all().delete()
        Enrollment.objects.all().delete()
        Scrap.objects.all().delete()
        PostLike.objects.all().delete()
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Board.objects.all().delete()
        EmailVerification.objects.all().delete()
        UserConsent.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # superuser 유지

        self.stdout.write(self.style.SUCCESS('기존 데이터 삭제 완료 (강좌 유지).'))

    # ==================== Phase 1: User 생성 ====================

    # 1.1. USER 생성
    def create_users(self, count):
        """USER 생성"""
        self.stdout.write(f'{count}명의 사용자 생성 중...')

        users = []
        existing_usernames = set(User.objects.values_list('username', flat=True))
        existing_emails = set(User.objects.values_list('email', flat=True))

        base_date = self.current_time - timedelta(days=USER_JOIN_LOOKBACK_DAYS)
        
        # [최적화] 비밀번호 해싱은 루프 밖에서 한 번만 수행
        hashed_password = make_password(DEFAULT_PASSWORD)

        for i in range(count):
            username = generate_unique_username(existing_usernames)
            email = generate_unique_email(existing_emails)
            existing_usernames.add(username)
            existing_emails.add(email)

            date_joined = random_datetime_between(
                base_date,
                self.current_time - timedelta(days=1)
            )

            # 마지막 로그인 (80% 확률로 활성 유저)
            last_login = None
            if random.random() < SEED_CONFIG['USER']['LOGIN_RATE']:
                last_login = random_datetime_between(
                    date_joined,
                    self.current_time
                )

            user = User(
                username=username,
                email=email,
                password=hashed_password,  # 미리 해싱된 값 사용
                name=fake.name(),
                is_email_verified=random.random() < SEED_CONFIG['USER']['VERIFIED_RATE'],
                is_active=random.random() < SEED_CONFIG['USER']['ACTIVE_RATE'],
                is_staff=False,
                is_superuser=False,
                date_joined=date_joined,
                last_login=last_login,
            )
            users.append(user)

        User.objects.bulk_create(users, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(users)}명의 사용자 생성 완료'))

        return list(User.objects.filter(is_superuser=False).order_by('-id')[:count])

    # 1.2 USER_CONSENT 및 EMAIL_VERIFICATION 생성
    def create_user_consents(self, users):
        """USER_CONSENT 생성 (모든 유저)"""
        self.stdout.write('유저 동의 생성 중...')

        consents = []
        for user in users:
            consent = UserConsent(
                user=user,
                terms_service=True,  # 필수
                terms_privacy=True,  # 필수
                marketing_opt_in=random.random() < SEED_CONFIG['USER']['MARKETING_AGREE'],
                agreed_at=user.date_joined,
            )
            consents.append(consent)

        UserConsent.objects.bulk_create(consents, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(consents)}개의 유저 동의 생성 완료'))

    # 1.3 EMAIL_VERIFICATION 생성
    def create_email_verifications(self, users):
        """EMAIL_VERIFICATION 생성 (미인증 유저의 30%만)""" # 바꾸고 싶으면 SEED_CONFIG['USER']['VERIFY_SAMPLE_RATE'] 조정
        self.stdout.write('이메일 인증 생성 중...')

        verifications = []
        unverified_users = [u for u in users if not u.is_email_verified]

        if unverified_users:
            sample_size = max(1, int(len(unverified_users) * SEED_CONFIG['USER']['VERIFY_SAMPLE_RATE']))
            for user in random.sample(unverified_users, k=sample_size):
                created_at = self.current_time - timedelta(days=random.randint(0, EMAIL_VERIFY_LOOKBACK_DAYS_MAX))
                verification = EmailVerification(
                    email=user.email,
                    code_hash=fake.sha256(),
                    expires_at=created_at + timedelta(hours=EMAIL_VERIFY_EXPIRE_HOURS),
                    verified_at=None,
                    created_at=created_at,
                )
                verifications.append(verification)

        if verifications:
            EmailVerification.objects.bulk_create(verifications, batch_size=BATCH_SIZE)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(verifications)}개의 이메일 인증 생성'))
        else:
            self.stdout.write('✓ 이메일 인증이 필요하지 않음')

    # ==================== Phase 2: 게시판 ====================

    # 2.1 게시판 생성
    def ensure_boards(self):
        """게시판 생성 (없으면)"""
        existing_boards = list(Board.objects.all())

        if existing_boards:
            self.stdout.write(f'✓ 기존 {len(existing_boards)}개 게시판 사용')
            return existing_boards

        self.stdout.write('게시판 생성 중...')
        boards = []
        service_start = self.current_time - timedelta(days=BOARD_SERVICE_LOOKBACK_DAYS)

        for board_info in BOARD_DATA:
            board = Board(
                name=board_info['name'],
                description=board_info['description'],
                created_at=service_start,
            )
            boards.append(board)

        Board.objects.bulk_create(boards, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(boards)}개 게시판 생성'))

        return list(Board.objects.all())

    # ==================== Phase 3: 커뮤니티 활동 ====================

    # 3.1 POST 생성
    def create_posts(self, users, boards, avg_posts_per_user):
        """POST 생성 (게시판당 1~20개)"""
        self.stdout.write(f'게시글 생성 중 (게시판당 1~20개)...')

        posts = []
        active_users = [u for u in users if u.is_active]
        base_date = self.current_time - timedelta(days=POST_ACTIVITY_LOOKBACK_DAYS)

        # 게시판별로 게시글 생성
        for board in boards:
            num_posts = random.randint(
                SEED_CONFIG['COMMUNITY']['BOARD']['MIN_POSTS_PER_BOARD'],
                SEED_CONFIG['COMMUNITY']['BOARD']['MAX_POSTS_PER_BOARD']
            )

            for _ in range(num_posts):
                # 랜덤 유저 선택
                author = random.choice(active_users)

                created_at = random_datetime_between(
                    max(base_date, author.date_joined),
                    self.current_time
                )

                # 20% 확률로 게시글 수정
                updated_at = created_at
                if random.random() < SEED_CONFIG['COMMUNITY']['POST_UPDATE_RATE']:
                    if created_at >= self.current_time:
                        updated_at = created_at
                    else:
                        updated_at = random_datetime_between(
                            created_at,
                            self.current_time
                        )

                post = Post(
                    author=author,
                    board=board,
                    title=KoreanContentGenerator.generate_post_title(),
                    content=KoreanContentGenerator.generate_post_content(),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                posts.append(post)

        Post.objects.bulk_create(posts, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(posts)}개 게시글 생성 (게시판 {len(boards)}개)'))

        return list(Post.objects.all().order_by('-id')[:len(posts)])

    # 3.2 COMMENT 및 대댓글 생성
    def create_comments(self, users, posts):
        """COMMENT 생성 (일반 댓글 + 대댓글)"""
        self.stdout.write('댓글 및 대댓글 생성 중...')

        comments = []

        for post in posts:
            # 게시글당 댓글 수 (0~8개, 평균 2개)
            num_comments = gaussian_int(
                SEED_CONFIG['COMMUNITY']['COMMENT']['AVG_PER_POST'],
                SEED_CONFIG['COMMUNITY']['COMMENT']['DEVIATION'],
                SEED_CONFIG['COMMUNITY']['COMMENT']['MIN'],
                SEED_CONFIG['COMMUNITY']['COMMENT']['MAX']
            )
            post_comments = []

            for _ in range(num_comments):
                if post.created_at >= self.current_time:
                    created_at = post.created_at
                else:
                    created_at = random_datetime_between(
                        post.created_at,
                        self.current_time
                    )

                updated_at = created_at
                if random.random() < SEED_CONFIG['COMMUNITY']['COMMENT']['UPDATE_RATE']:  # 10%
                    if created_at >= self.current_time:
                        updated_at = created_at
                    else:
                        updated_at = random_datetime_between(created_at, self.current_time)

                comment = Comment(
                    author=random.choice(users),
                    post=post,
                    parent=None,
                    content=KoreanContentGenerator.generate_comment(),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                post_comments.append(comment)

            if post_comments:
                Comment.objects.bulk_create(post_comments, batch_size=BATCH_SIZE)
                comments.extend(post_comments)

        # 대댓글 생성 (기존 댓글의 20%)
        self.stdout.write('대댓글 생성 중...')
        all_comments = list(Comment.objects.filter(parent=None))
        replies = []

        if all_comments:
            reply_count = int(len(all_comments) * SEED_CONFIG['COMMUNITY']['REPLY']['TARGET_RATIO'])
            for comment in random.sample(all_comments, k=min(reply_count, len(all_comments))):
                # 각 댓글에 1~2개 대댓글
                num_replies = random.randint(*SEED_CONFIG['COMMUNITY']['REPLY']['COUNT_RANGE'])
                for _ in range(num_replies):
                    if comment.created_at >= self.current_time:
                        created_at = comment.created_at
                    else:
                        created_at = random_datetime_between(
                            comment.created_at,
                            self.current_time
                        )

                    reply = Comment(
                        author=random.choice(users),
                        post=comment.post,
                        parent=comment,
                        content=KoreanContentGenerator.generate_comment(),
                        created_at=created_at,
                        updated_at=created_at,
                    )
                    replies.append(reply)

        if replies:
            Comment.objects.bulk_create(replies, batch_size=BATCH_SIZE)

        total = len(comments) + len(replies)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(comments)}개 댓글과 {len(replies)}개 대댓글 생성 (총: {total})'))

    # 3.3 POST_LIKES 생성
    def create_post_likes(self, users, posts):
        """POST_LIKES 생성 (왕성하게!)"""
        self.stdout.write('게시글 좋아요 생성 중...')

        likes = []
        seen = set()

        for post in posts:
            # 각 게시글마다 유저의 20~40% 좋아요 (왕성!)
            like_ratio = random.uniform(SEED_CONFIG['COMMUNITY']['LIKE']['RATIO_MIN'], SEED_CONFIG['COMMUNITY']['LIKE']['RATIO_MAX'])
            num_likes = int(len(users) * like_ratio)
            likers = random.sample(users, k=min(num_likes, len(users)))

            for user in likers:
                pair = (user.id, post.id)
                if pair not in seen:
                    seen.add(pair)
                    # 방어: post.created_at이 current_time과 같거나 이후면 그대로 사용
                    if post.created_at >= self.current_time:
                        like_created_at = post.created_at
                    else:
                        like_created_at = random_datetime_between(
                            post.created_at,
                            self.current_time
                        )

                    like = PostLike(
                        user=user,
                        post=post,
                        created_at=like_created_at
                    )
                    likes.append(like)

        PostLike.objects.bulk_create(likes, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(likes)}개 게시글 좋아요 생성'))

    # 3.4 SCRAP 생성
    def create_scraps(self, users, posts):
        """SCRAP 생성 (왕성하게!)"""
        self.stdout.write('스크랩 생성 중...')

        scraps = []
        seen = set()

        for user in users:
            # 유저당 평균 8개 스크랩 (0~25개)
            num_scraps = gaussian_int(SEED_CONFIG['COMMUNITY']['SCRAP']['AVG_PER_USER'], SEED_CONFIG['COMMUNITY']['SCRAP']['DEVIATION'], 0, min(SEED_CONFIG['COMMUNITY']['SCRAP']['MAX'], len(posts)))
            if num_scraps > 0:
                scraped_posts = random.sample(posts, k=num_scraps)

                for post in scraped_posts:
                    pair = (user.id, post.id)
                    if pair not in seen:
                        seen.add(pair)
                        # 방어: post.created_at이 current_time과 같거나 이후면 그대로 사용
                        if post.created_at >= self.current_time:
                            scrap_created_at = post.created_at
                        else:
                            scrap_created_at = random_datetime_between(
                                post.created_at,
                                self.current_time
                            )

                        scrap = Scrap(
                            user=user,
                            post=post,
                            created_at=scrap_created_at
                        )
                        scraps.append(scrap)

        Scrap.objects.bulk_create(scraps, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(scraps)}개 스크랩 생성'))

    # ==================== Phase 4: 강좌 활동 ====================

    # 4.1 ENROLLMENT 생성
    def create_enrollments(self, users, courses):
        """ENROLLMENT 생성 (지정된 강좌들에 대해)"""
        self.stdout.write('수강 정보 생성 중...')

        enrollments = []
        seen = set()

        for user in users:
            # 유저당 평균 40% 강좌 수강
            num_enrollments = max(1, int(len(courses) * random.uniform(SEED_CONFIG['COURSE']['ENROLLMENT']['RATE_MIN'], SEED_CONFIG['COURSE']['ENROLLMENT']['RATE_MAX'])))
            enrolled_courses = random.sample(courses, k=min(num_enrollments, len(courses)))

            for course in enrolled_courses:
                pair = (user.id, course.id)
                if pair not in seen:
                    seen.add(pair)

                    # 수강 시작일
                    if course.enrollment_start and course.enrollment_start <= self.current_time.date():
                        enrolled_at = random_datetime_between(
                            timezone.make_aware(datetime.combine(course.enrollment_start, datetime.min.time())),
                            self.current_time
                        )
                    else:
                        enrolled_at = random_datetime_between(
                            user.date_joined,
                            self.current_time
                        )

                    # 상태 (enrolled: 50%, completed: 40%, dropped: 10%)
                    status = weighted_choice(
                        SEED_CONFIG['COURSE']['ENROLLMENT']['STATUS_OPTS'],
                        SEED_CONFIG['COURSE']['ENROLLMENT']['STATUS_WEIGHTS']
                    )

                    # 진도율
                    if status == 'enrolled':
                        progress = random.uniform(*SEED_CONFIG['COURSE']['ENROLLMENT']['PROGRESS']['ENROLLED'])
                    elif status == 'completed':
                        progress = random.uniform(*SEED_CONFIG['COURSE']['ENROLLMENT']['PROGRESS']['COMPLETED'])
                    else:  # dropped
                        progress = random.uniform(*SEED_CONFIG['COURSE']['ENROLLMENT']['PROGRESS']['DROPPED'])

                    # 마지막 학습일
                    last_studied = None
                    if status == 'enrolled':
                        # 방어: enrolled_at이 current_time과 같거나 이후면 그대로 사용
                        if enrolled_at >= self.current_time:
                            last_studied = enrolled_at
                        else:
                            last_studied = random_datetime_between(
                                enrolled_at,
                                self.current_time
                            )
                    elif status == 'completed':
                        last_studied = enrolled_at + timedelta(days=random.randint(30, 120))

                    enrollment = Enrollment(
                        user=user,
                        course=course,
                        status=status,
                        progress_rate=Decimal(str(round(progress, 2))),
                        last_studied_at=last_studied,
                        enrolled_at=enrolled_at,
                        created_at=enrolled_at,
                        updated_at=self.current_time,
                    )
                    enrollments.append(enrollment)

        Enrollment.objects.bulk_create(enrollments, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(enrollments)}개 수강 정보 생성'))

        return enrollments

    # 4.2 WISHLIST 생성
    def create_wishlists(self, users, courses, enrollments):
        """WISHLIST 생성 (지정된 강좌들에 대해)"""
        self.stdout.write('Creating wishlists...')

        # 이미 수강중인 강좌 제외
        enrolled_pairs = {(e.user_id, e.course_id) for e in enrollments}

        wishlists = []
        seen = set()

        for user in users:
            # 유저당 평균 30% 강좌 찜
            num_wishes = max(0, int(len(courses) * random.uniform(SEED_CONFIG['COURSE']['WISHLIST']['RATE_MIN'], SEED_CONFIG['COURSE']['WISHLIST']['RATE_MAX'])))

            # 이미 수강중이지 않은 강좌만 선택
            available_courses = [
                c for c in courses
                if (user.id, c.id) not in enrolled_pairs
            ]

            if available_courses and num_wishes > 0:
                wished_courses = random.sample(
                    available_courses,
                    k=min(num_wishes, len(available_courses))
                )

                for course in wished_courses:
                    pair = (user.id, course.id)
                    if pair not in seen:
                        seen.add(pair)
                        # 방어: user.date_joined이 current_time과 같거나 이후면 그대로 사용
                        if user.date_joined >= self.current_time:
                            wishlist_created_at = user.date_joined
                        else:
                            wishlist_created_at = random_datetime_between(
                                user.date_joined,
                                self.current_time
                            )

                        wishlist = Wishlist(
                            user=user,
                            course=course,
                            created_at=wishlist_created_at
                        )
                        wishlists.append(wishlist)

        Wishlist.objects.bulk_create(wishlists, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(wishlists)}개 찜 생성'))

    # 4.3 COURSE_REVIEW 생성
    def create_course_reviews(self, enrollments):
        """COURSE_REVIEW 생성 (완강한 수강생의 60%)"""
        self.stdout.write('코스 리뷰 생성 중...')

        reviews = []
        completed = [e for e in enrollments if e.status == 'completed']

        if completed:
            review_ratio = SEED_CONFIG['COURSE']['REVIEW']['WRITE_RATE']
            for enrollment in random.sample(completed, k=int(len(completed) * review_ratio)):
                # 평점 (정규분포)
                rating = gaussian_int(SEED_CONFIG['COURSE']['REVIEW']['RATING']['AVG'], SEED_CONFIG['COURSE']['REVIEW']['RATING']['DEV'], SEED_CONFIG['COURSE']['REVIEW']['RATING']['MIN'], SEED_CONFIG['COURSE']['REVIEW']['RATING']['MAX'])

                # 리뷰 텍스트 생성 (RealisticReviewGenerator 사용)
                review_text = RealisticReviewGenerator.generate_review()

                # 리뷰 작성일 (수강 시작 + 20일 이후)
                review_start_date = enrollment.enrolled_at + timedelta(days=SEED_CONFIG['COURSE']['REVIEW']['MIN_DAYS_AFTER_ENROLL'])

                # 리뷰 시작일이 미래인 경우 방어 처리
                if review_start_date >= self.current_time:
                    # 수강 시작일 이후 ~ 현재 시각 사이로 설정
                    created_at = random_datetime_between(
                        enrollment.enrolled_at,
                        self.current_time
                    )
                else:
                    created_at = random_datetime_between(
                        review_start_date,
                        self.current_time
                    )

                review = CourseReview(
                    user=enrollment.user,
                    course=enrollment.course,
                    rating=rating,
                    review_text=review_text,
                    created_at=created_at,
                    updated_at=created_at,
                )
                reviews.append(review)

        CourseReview.objects.bulk_create(reviews, batch_size=BATCH_SIZE, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(reviews)}개의 강의 리뷰 생성'))

        return reviews
