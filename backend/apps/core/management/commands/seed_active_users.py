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

SEED_CONFIG = {
    'USER': {
        'ACTIVE_RATE': 0.95,       # 활성 유저 비율
        'VERIFIED_RATE': 0.85,     # 이메일 인증 비율
        'LOGIN_RATE': 0.8,         # 최근 로그인 기록이 있을 확률
        'MARKETING_AGREE': 0.6,    # 마케팅 동의 비율
        'VERIFY_SAMPLE_RATE': 0.3, # 미인증 유저 중 인증 시도 데이터 생성 비율
    },
    'COMMUNITY': {
        'POST': {
            'DEVIATION': 2,        # 게시글 수 표준편차
            'DEVIATION_MULTIPLIER': 0.6,         # 기존 avg_posts_per_user * 0.6 구조였던 값
            'MIN_POSTS_PER_USER': 0,             # 기존 max(0, ...)
            'MAX_MULTIPLIER': 3,                 # 기존 avg_posts_per_user * 3
            'TITLE_WORDS_RANGE': (4, 12),        # 기존 random.randint(4, 12)
            'CONTENT_PARAGRAPHS_RANGE': (2, 6),  # 기존 random.randint(2, 6)
        },
        'POST_UPDATE_RATE': 0.3,   # 게시글 수정 비율
        'COMMENT': {
            'AVG_PER_POST': 8,     # 게시글 당 평균 댓글 수
            'DEVIATION': 4,        # 표준편차
            'MIN': 0, 'MAX': 20,
            'UPDATE_RATE': 0.15,   # 댓글 수정 비율
            'CONTENT_WORDS_RANGE': (5, 25) # 댓글 내용 단어 수 범위
        },
        'REPLY': {
            'TARGET_RATIO': 0.4,   # 전체 댓글 중 대댓글이 달릴 비율
            'COUNT_RANGE': (1, 3), # 대댓글 달릴 시 개수 범위
        },
        'LIKE': {
            'RATIO_MIN': 0.2,      # 유저 중 최소 20%가 좋아요
            'RATIO_MAX': 0.4,      # 유저 중 최대 40%가 좋아요
        },
        'SCRAP': {
            'AVG_PER_USER': 8,     # 유저당 평균 스크랩 수
            'DEVIATION': 5,        # 표준편차
            'MAX': 25,             # 최대 스크랩 수
        }
    },
    'COURSE': {
        'ENROLLMENT': {
            'RATE_MIN': 0.0003,                                     # 유저당 최소 수강 강좌 비율 (전체 강좌 대비)
            'RATE_MAX': 0.006,                                      # 유저당 최대 수강 강좌 비율
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
            'WRITE_RATE': 0.6,                                        # 완강자 중 리뷰 작성 비율
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

        base_date = timezone.now() - timedelta(days=USER_JOIN_LOOKBACK_DAYS)
        
        # [최적화] 비밀번호 해싱은 루프 밖에서 한 번만 수행
        hashed_password = make_password(DEFAULT_PASSWORD)

        for i in range(count):
            username = generate_unique_username(existing_usernames)
            email = generate_unique_email(existing_emails)
            existing_usernames.add(username)
            existing_emails.add(email)

            date_joined = random_datetime_between(
                base_date,
                timezone.now() - timedelta(days=1)
            )

            # 마지막 로그인 (80% 확률로 활성 유저)
            last_login = None
            if random.random() < SEED_CONFIG['USER']['LOGIN_RATE']:
                last_login = random_datetime_between(
                    date_joined,
                    timezone.now()
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
                created_at = timezone.now() - timedelta(days=random.randint(0, EMAIL_VERIFY_LOOKBACK_DAYS_MAX))
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
        service_start = timezone.now() - timedelta(days=BOARD_SERVICE_LOOKBACK_DAYS)

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
        """POST 생성 (왕성하게!)"""
        self.stdout.write(f'게시글 생성 중 (유저당 평균 {avg_posts_per_user}개)...')

        posts = []
        active_users = [u for u in users if u.is_active]
        base_date = timezone.now() - timedelta(days=POST_ACTIVITY_LOOKBACK_DAYS)

        for user in active_users:
            # 정규분포로 게시글 수 결정 (일부는 많이, 일부는 적게)
            num_posts = max(SEED_CONFIG['COMMUNITY']['POST']['MIN_POSTS_PER_USER'], gaussian_int(
                avg_posts_per_user,
                SEED_CONFIG['COMMUNITY']['POST']['DEVIATION'],
                SEED_CONFIG['COMMUNITY']['POST']['MIN_POSTS_PER_USER'],
                avg_posts_per_user * SEED_CONFIG['COMMUNITY']['POST']['MAX_MULTIPLIER']
            ))

            for _ in range(num_posts):
                created_at = random_datetime_between(
                    max(base_date, user.date_joined),
                    timezone.now()
                )

                # 30% 확률
                updated_at = created_at
                if random.random() < SEED_CONFIG['COMMUNITY']['POST_UPDATE_RATE']:
                    updated_at = random_datetime_between(
                        created_at,
                        timezone.now()
                    )

                post = Post(
                    author=user,
                    board=random.choice(boards),
                    title=fake.sentence(nb_words=random.randint(*SEED_CONFIG['COMMUNITY']['POST']['TITLE_WORDS_RANGE'])).rstrip('.'),
                    content='\n\n'.join(fake.paragraphs(nb=random.randint(*SEED_CONFIG['COMMUNITY']['POST']['CONTENT_PARAGRAPHS_RANGE']))),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                posts.append(post)

        Post.objects.bulk_create(posts, batch_size=BATCH_SIZE)
        self.stdout.write(self.style.SUCCESS(f'✓ {len(posts)}개 게시글 생성'))

        return list(Post.objects.all().order_by('-id')[:len(posts)])

    # 3.2 COMMENT 및 대댓글 생성
    def create_comments(self, users, posts):
        """COMMENT 생성 (일반 댓글 + 대댓글 왕성하게!)"""
        self.stdout.write('댓글 및 대댓글 생성 중...')

        comments = []

        for post in posts:
            # 게시글당 댓글 수 (0~20개, 평균 8개)
            num_comments = gaussian_int(SEED_CONFIG['COMMUNITY']['COMMENT']['AVG_PER_POST'], SEED_CONFIG['COMMUNITY']['COMMENT']['DEVIATION'], SEED_CONFIG['COMMUNITY']['COMMENT']['MIN'], SEED_CONFIG['COMMUNITY']['COMMENT']['MAX'])
            post_comments = []

            for _ in range(num_comments):
                created_at = random_datetime_between(
                    post.created_at,
                    timezone.now()
                )

                updated_at = created_at
                if random.random() < SEED_CONFIG['COMMUNITY']['COMMENT']['UPDATE_RATE']:  # 15%
                    updated_at = random_datetime_between(created_at, timezone.now())

                comment = Comment(
                    author=random.choice(users),
                    post=post,
                    parent=None,
                    content=fake.sentence(nb_words=random.randint(*SEED_CONFIG['COMMUNITY']['COMMENT']['CONTENT_WORDS_RANGE'])),
                    created_at=created_at,
                    updated_at=updated_at,
                )
                post_comments.append(comment)

            if post_comments:
                Comment.objects.bulk_create(post_comments, batch_size=BATCH_SIZE)
                comments.extend(post_comments)

        # 대댓글 생성 (기존 댓글의 40% - 왕성!)
        self.stdout.write('대댓글 생성 중...')
        all_comments = list(Comment.objects.filter(parent=None))
        replies = []

        if all_comments:
            reply_count = int(len(all_comments) * SEED_CONFIG['COMMUNITY']['REPLY']['TARGET_RATIO'])
            for comment in random.sample(all_comments, k=min(reply_count, len(all_comments))):
                # 각 댓글에 1~3개 대댓글
                num_replies = random.randint(*SEED_CONFIG['COMMUNITY']['REPLY']['COUNT_RANGE'])
                for _ in range(num_replies):
                    created_at = random_datetime_between(
                        comment.created_at,
                        timezone.now()
                    )

                    reply = Comment(
                        author=random.choice(users),
                        post=comment.post,
                        parent=comment,
                        content=fake.sentence(nb_words=random.randint(*SEED_CONFIG['COMMUNITY']['COMMENT']['CONTENT_WORDS_RANGE'])),
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
                    like = PostLike(
                        user=user,
                        post=post,
                        created_at=random_datetime_between(
                            post.created_at,
                            timezone.now()
                        )
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
                        scrap = Scrap(
                            user=user,
                            post=post,
                            created_at=random_datetime_between(
                                post.created_at,
                                timezone.now()
                            )
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
                    if course.enrollment_start and course.enrollment_start <= timezone.now().date():
                        enrolled_at = random_datetime_between(
                            timezone.make_aware(datetime.combine(course.enrollment_start, datetime.min.time())),
                            timezone.now()
                        )
                    else:
                        enrolled_at = random_datetime_between(
                            user.date_joined,
                            timezone.now()
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
                        last_studied = random_datetime_between(
                            enrolled_at,
                            timezone.now()
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
                        updated_at=timezone.now(),
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
                        wishlist = Wishlist(
                            user=user,
                            course=course,
                            created_at=random_datetime_between(
                                user.date_joined,
                                timezone.now()
                            )
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

                # 긴 리뷰 여부
                if random.random() < SEED_CONFIG['COURSE']['REVIEW']['LONG_TEXT_RATE']:
                    review_text = '\n\n'.join(fake.paragraphs(nb=random.randint(*SEED_CONFIG['COURSE']['REVIEW']['LONG_TEXT_PARAGRAPHS'])))
                else:
                    review_text = fake.sentence(nb_words=random.randint(*SEED_CONFIG['COURSE']['REVIEW']['SHORT_TEXT_WORDS']))

                created_at = random_datetime_between(
                    enrollment.enrolled_at + timedelta(days=SEED_CONFIG['COURSE']['REVIEW']['MIN_DAYS_AFTER_ENROLL']),
                    timezone.now()
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