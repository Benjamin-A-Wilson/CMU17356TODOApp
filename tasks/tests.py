from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Task


class TaskListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')

    def test_user_only_sees_their_tasks(self):
        Task.objects.create(user=self.user, title='My task', due_date=timezone.localdate())
        Task.objects.create(user=self.other, title='Other task', due_date=timezone.localdate())
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'))

        self.assertContains(response, 'My task')
        self.assertNotContains(response, 'Other task')

    def test_signup_creates_new_user(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password1': 'safepass12345',
            'password2': 'safepass12345',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newstudent').exists())

    @patch('django.utils.timezone.localdate', return_value=date(2025, 3, 15))
    def test_due_today_tasks_appear_in_todays_focus(self, _mock_localdate):
        Task.objects.create(
            user=self.user,
            title='Due today headline',
            due_date=date(2025, 3, 15),
            completed=False,
        )
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'))

        self.assertContains(response, "Today's Focus")
        self.assertContains(response, 'Due today headline')

    @patch('django.utils.timezone.localdate', return_value=date(2025, 3, 15))
    def test_completed_tasks_due_today_not_in_focus_list(self, _mock_localdate):
        Task.objects.create(
            user=self.user,
            title='Already done',
            due_date=date(2025, 3, 15),
            completed=True,
        )
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'))

        self.assertContains(response, 'No tasks due today. Nice work.')
        self.assertNotContains(response, '<li>Already done</li>', html=True)

    @patch('django.utils.timezone.localdate', return_value=date(2025, 3, 15))
    def test_overdue_tasks_shown_in_warning_section(self, _mock_localdate):
        Task.objects.create(
            user=self.user,
            title='Late item',
            due_date=date(2025, 3, 10),
            completed=False,
        )
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'))

        self.assertContains(response, 'Overdue Tasks')
        self.assertContains(response, 'Late item')


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')

    def test_str_includes_title_and_username(self):
        task = Task.objects.create(
            user=self.user,
            title='Read paper',
            due_date=timezone.localdate(),
        )
        self.assertEqual(str(task), 'Read paper (alice)')

    @patch('tasks.models.timezone.localdate', return_value=date(2025, 6, 1))
    def test_is_due_today_true_when_dates_match(self, _mock_localdate):
        task = Task(user=self.user, title='t', due_date=date(2025, 6, 1))
        self.assertTrue(task.is_due_today)

    @patch('tasks.models.timezone.localdate', return_value=date(2025, 6, 1))
    def test_is_due_today_false_when_dates_differ(self, _mock_localdate):
        task = Task(user=self.user, title='t', due_date=date(2025, 6, 2))
        self.assertFalse(task.is_due_today)


class LoginRequiredViewTests(TestCase):
    urls_to_check = (
        'task-list',
        'task-create',
    )

    def test_anonymous_user_redirected_to_login_for_protected_views(self):
        for name in self.urls_to_check:
            with self.subTest(url_name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response.url)

    def test_anonymous_cannot_access_task_update_delete_toggle(self):
        user = User.objects.create_user(username='owner', password='pass12345')
        task = Task.objects.create(
            user=user,
            title='Secret',
            due_date=timezone.localdate(),
        )
        for name, kwargs in (
            ('task-update', {'pk': task.pk}),
            ('task-delete', {'pk': task.pk}),
            ('task-toggle', {'pk': task.pk}),
        ):
            with self.subTest(url_name=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/accounts/login/', response.url)


class SignupViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')

    def test_signup_get_renders_form(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')

    def test_authenticated_user_redirected_from_signup(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('signup'))
        self.assertRedirects(response, reverse('task-list'))

    def test_signup_invalid_password_mismatch_does_not_create_user(self):
        response = self.client.post(reverse('signup'), {
            'username': 'ghost',
            'email': 'ghost@example.com',
            'password1': 'onepassword123',
            'password2': 'otherpassword123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='ghost').exists())


class TaskCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')

    def test_create_get_renders_form(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Task')

    def test_create_post_saves_task_for_logged_in_user(self):
        self.client.login(username='alice', password='password123')
        due = timezone.localdate() + timedelta(days=3)
        response = self.client.post(reverse('task-create'), {
            'title': 'New homework',
            'description': 'Chapter 4',
            'due_date': due.isoformat(),
            'completed': False,
        })
        self.assertRedirects(response, reverse('task-list'))
        task = Task.objects.get(title='New homework')
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.description, 'Chapter 4')
        self.assertFalse(task.completed)


class TaskUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.task = Task.objects.create(
            user=self.user,
            title='Original',
            description='Old',
            due_date=timezone.localdate(),
        )
        self.other_task = Task.objects.create(
            user=self.other,
            title='Bob only',
            due_date=timezone.localdate(),
        )

    def test_update_get_renders_form_with_task(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-update', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original')

    def test_update_post_persists_changes(self):
        self.client.login(username='alice', password='password123')
        new_due = timezone.localdate() + timedelta(days=1)
        response = self.client.post(reverse('task-update', kwargs={'pk': self.task.pk}), {
            'title': 'Updated title',
            'description': 'New body',
            'due_date': new_due.isoformat(),
            'completed': True,
        })
        self.assertRedirects(response, reverse('task-list'))
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated title')
        self.assertEqual(self.task.description, 'New body')
        self.assertTrue(self.task.completed)

    def test_update_other_users_task_returns_404(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-update', kwargs={'pk': self.other_task.pk}))
        self.assertEqual(response.status_code, 404)


class TaskDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.task = Task.objects.create(
            user=self.user,
            title='To remove',
            due_date=timezone.localdate(),
        )
        self.other_task = Task.objects.create(
            user=self.other,
            title='Protected',
            due_date=timezone.localdate(),
        )

    def test_delete_get_shows_confirmation(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-delete', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'To remove')

    def test_delete_post_removes_task(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('task-delete', kwargs={'pk': self.task.pk}))
        self.assertRedirects(response, reverse('task-list'))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_other_users_task_returns_404(self):
        self.client.login(username='alice', password='password123')
        response = self.client.post(reverse('task-delete', kwargs={'pk': self.other_task.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.other_task.pk).exists())


class TaskToggleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other = User.objects.create_user(username='bob', password='password123')
        self.task = Task.objects.create(
            user=self.user,
            title='Toggle me',
            due_date=timezone.localdate(),
            completed=False,
        )
        self.other_task = Task.objects.create(
            user=self.other,
            title='Not yours',
            due_date=timezone.localdate(),
        )

    def test_toggle_sets_completed_true(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-toggle', kwargs={'pk': self.task.pk}))
        self.assertRedirects(response, reverse('task-list'))
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_toggle_sets_completed_false_when_already_done(self):
        self.task.completed = True
        self.task.save()
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-toggle', kwargs={'pk': self.task.pk}))
        self.assertRedirects(response, reverse('task-list'))
        self.task.refresh_from_db()
        self.assertFalse(self.task.completed)

    def test_toggle_other_users_task_returns_404(self):
        self.client.login(username='alice', password='password123')
        response = self.client.get(reverse('task-toggle', kwargs={'pk': self.other_task.pk}))
        self.assertEqual(response.status_code, 404)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendMorningRemindersCommandTests(TestCase):
    def setUp(self):
        mail.outbox.clear()

    @patch('django.utils.timezone.localdate', return_value=date(2025, 4, 10))
    def test_sends_email_for_incomplete_tasks_due_today(self, _mock_localdate):
        user = User.objects.create_user(
            username='pat',
            email='pat@example.com',
            password='pass12345',
        )
        Task.objects.create(
            user=user,
            title='Morning quiz',
            due_date=date(2025, 4, 10),
            completed=False,
        )
        call_command('send_morning_reminders')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Morning quiz', mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['pat@example.com'])

    @patch('django.utils.timezone.localdate', return_value=date(2025, 4, 10))
    def test_skips_users_with_blank_email(self, _mock_localdate):
        User.objects.create_user(username='noemail', email='', password='pass12345')
        call_command('send_morning_reminders')
        self.assertEqual(len(mail.outbox), 0)

    @patch('django.utils.timezone.localdate', return_value=date(2025, 4, 10))
    def test_skips_when_no_incomplete_tasks_due_today(self, _mock_localdate):
        User.objects.create_user(
            username='idle',
            email='idle@example.com',
            password='pass12345',
        )
        call_command('send_morning_reminders')
        self.assertEqual(len(mail.outbox), 0)

    @patch('django.utils.timezone.localdate', return_value=date(2025, 4, 10))
    def test_excludes_completed_tasks_from_reminder_email(self, _mock_localdate):
        user = User.objects.create_user(
            username='done',
            email='done@example.com',
            password='pass12345',
        )
        Task.objects.create(
            user=user,
            title='Finished',
            due_date=date(2025, 4, 10),
            completed=True,
        )
        call_command('send_morning_reminders')
        self.assertEqual(len(mail.outbox), 0)
