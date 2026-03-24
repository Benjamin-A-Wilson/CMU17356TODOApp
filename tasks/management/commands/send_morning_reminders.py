from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from tasks.models import Task


class Command(BaseCommand):
    help = 'Send each user an email with tasks due today.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent_count = 0

        for user in User.objects.exclude(email=''):
            tasks_due_today = Task.objects.filter(
                user=user,
                due_date=today,
                completed=False,
            ).order_by('due_date', 'title')
            if not tasks_due_today.exists():
                continue

            task_lines = '\n'.join([f'- {task.title}' for task in tasks_due_today])
            send_mail(
                subject='Your TODOs for today',
                message=(
                    f'Hi {user.username},\n\n'
                    f'Here are your tasks due today ({today}):\n'
                    f'{task_lines}\n\n'
                    'Good luck with classes!'
                ),
                from_email='noreply@cmu-todo.local',
                recipient_list=[user.email],
                fail_silently=False,
            )
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(f'Sent reminders to {sent_count} user(s).'))
