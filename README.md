# CMU Multiuser TODO List (Django + JavaScript)

This project is a multiuser TODO list web app for students:
- Track class tasks with due dates.
- Get morning reminders for tasks due today.

## Features

- User sign-up, login, and logout.
- Per-user task list (users only see their own tasks).
- Create, edit, delete, and complete/uncomplete tasks.
- Due-date tracking, with separate "due today" and overdue views.
- JavaScript browser notifications for morning reminders.
- Daily reminder email command for scheduled morning sends.

## Quick start

1. Install dependencies:
   - `python -m pip install django`
2. Run migrations:
   - `python manage.py migrate`
3. Start the server:
   - `python manage.py runserver`
4. Open: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
5. Create an account at `/signup/`.

## Morning reminders

### In-app browser reminder (JavaScript)
- Click **Enable Browser Reminder** on the task list page.
- The app shows one browser notification each morning (after 5 AM local time) when you open the app.

### Daily email reminders (backend command)
- Command:
  - `python manage.py send_morning_reminders`
- This sends each user an email with their incomplete tasks due today.
- In development, emails print to the console (`EMAIL_BACKEND` is console backend).

To automate it on Windows, create a Task Scheduler task that runs every morning:
- Program/script: `python`
- Add arguments: `manage.py send_morning_reminders`
- Start in: your project folder

## Testing

- Run tests with:
  - `python manage.py test`

## Contribution History

- _Merged PRs will be appended here automatically by GitHub Actions._

## Contribution History

- Ghee-clarified-butter 2026-03-24 #1 Pull request for 17-356 class
