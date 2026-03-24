from django.urls import path

from . import views

urlpatterns = [
    path('', views.task_list, name='task-list'),
    path('signup/', views.signup_view, name='signup'),
    path('tasks/new/', views.task_create, name='task-create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task-update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task-delete'),
    path('tasks/<int:pk>/toggle/', views.task_toggle_complete, name='task-toggle'),
]
