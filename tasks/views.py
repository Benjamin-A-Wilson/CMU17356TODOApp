from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import SignUpForm, TaskForm
from .models import Task


def _handle_task_form_submission(request, form, success_message):
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        if task.user_id is None:
            task.user = request.user
        task.save()
        messages.success(request, success_message)
        return redirect('task-list')
    return None


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('task-list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('task-list')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).order_by('completed', 'due_date')
    today = timezone.localdate()
    due_today = tasks.filter(due_date=today, completed=False)
    overdue = tasks.filter(due_date__lt=today, completed=False)
    context = {
        'tasks': tasks,
        'today': today,
        'due_today': due_today,
        'due_today_titles': list(due_today.values_list('title', flat=True)),
        'overdue': overdue,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    response = _handle_task_form_submission(request, form, 'Task added.')
    if response:
        return response

    return render(request, 'tasks/task_form.html', {'form': form, 'page_title': 'Add Task'})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST or None, instance=task)
    response = _handle_task_form_submission(request, form, 'Task updated.')
    if response:
        return response

    return render(request, 'tasks/task_form.html', {'form': form, 'page_title': 'Edit Task'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('task-list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save(update_fields=['completed', 'updated_at'])
    return redirect('task-list')
