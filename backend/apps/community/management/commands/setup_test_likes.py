from django.core.management.base import BaseCommand
from apps.community.models import Post
from apps.accounts.models import User


class Command(BaseCommand):
    help = '테스트 게시글에 좋아요 관계를 설정합니다'

    def handle(self, *args, **kwargs):
        # 좋아요 관계 정의: {user_id: [post_ids]}
        likes_data = {
            100: [101, 102, 104, 106],  # testuser1
            101: [100, 103, 105, 107],  # testuser2
            102: [100, 101, 108, 109],  # testuser3
        }

        self.stdout.write(self.style.WARNING(
            '\n테스트 게시글에 좋아요 관계를 설정합니다...\n'
        ))

        total_likes = 0
        total_errors = 0

        for user_id, post_ids in likes_data.items():
            try:
                user = User.objects.get(pk=user_id)
                self.stdout.write(f'\n[{user.username}]')

                for post_id in post_ids:
                    try:
                        post = Post.objects.get(pk=post_id)
                        # 이미 좋아요를 눌렀는지 확인
                        if post.likes.filter(pk=user.pk).exists():
                            self.stdout.write(self.style.WARNING(
                                f'  - Post {post_id} ({post.title[:30]}...) - 이미 좋아요함'
                            ))
                        else:
                            post.likes.add(user)
                            total_likes += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'  ✓ Post {post_id} ({post.title[:30]}...) 좋아요 추가'
                            ))
                    except Post.DoesNotExist:
                        self.stdout.write(self.style.ERROR(
                            f'  ✗ Post {post_id}를 찾을 수 없습니다.'
                        ))
                        total_errors += 1

            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'\n✗ User {user_id}를 찾을 수 없습니다.'
                ))
                total_errors += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n총 {total_likes}개의 좋아요 관계가 설정되었습니다.'
        ))
        if total_errors > 0:
            self.stdout.write(self.style.WARNING(
                f'{total_errors}개의 오류가 발생했습니다.\n'
            ))
