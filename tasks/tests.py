from django.contrib.auth.models import User
from django.test import TestCase
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

    def test_task_list_filters_by_search_query(self):
        Task.objects.create(user=self.user, title='Buy milk', due_date=timezone.localdate())
        Task.objects.create(user=self.user, title='Math homework', due_date=timezone.localdate())
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'), {'q': 'milk'})

        self.assertContains(response, 'Buy milk')
        self.assertNotContains(response, 'Math homework')

    def test_task_list_search_ignores_other_users_tasks(self):
        Task.objects.create(user=self.user, title='Project report', due_date=timezone.localdate())
        Task.objects.create(user=self.other, title='Project report', due_date=timezone.localdate())
        self.client.login(username='alice', password='password123')

        response = self.client.get(reverse('task-list'), {'q': 'project'})

        self.assertContains(response, 'Project report', count=1)
