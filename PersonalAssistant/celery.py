from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PersonalAssistant.settings')

# Create the Celery app instance
app = Celery('PersonalAssistant')

# Configure Celery to use Django's settings with a namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover task modules in all installed apps
app.autodiscover_tasks()

# Define the Celery beat schedule (periodic tasks)
app.conf.beat_schedule = {
    'check-tasks-deadline-every-2-minutes': {  # Descriptive key for the task
        'task': 'users.tasks.check_task_deadlines',  # Ensure the task path is correct
        'schedule': crontab(minute='*/2'),  # Every 2 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
