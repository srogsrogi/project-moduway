from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = '테스트 사용자의 비밀번호를 설정합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='설정할 비밀번호 (기본값: testpass123)'
        )

    def handle(self, *args, **kwargs):
        test_password = kwargs['password']
        test_user_ids = [100, 101, 102]

        self.stdout.write(self.style.WARNING(
            f'\n테스트 사용자의 비밀번호를 "{test_password}"로 설정합니다...\n'
        ))

        success_count = 0
        for user_id in test_user_ids:
            try:
                user = User.objects.get(pk=user_id)
                user.set_password(test_password)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✓ {user.username} (ID: {user.id}, {user.email}) 비밀번호 설정 완료'
                ))
                success_count += 1
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'✗ ID {user_id} 사용자를 찾을 수 없습니다.'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'\n{success_count}/{len(test_user_ids)}명의 사용자 비밀번호가 설정되었습니다.'
        ))
        self.stdout.write(
            f'로그인 테스트: username/email + "{test_password}"\n'
        )
