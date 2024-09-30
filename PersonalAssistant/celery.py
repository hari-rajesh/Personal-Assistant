from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PersonalAssistant.settings')

app = Celery('PersonalAssistant')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-tasks-deadline-every-2-minutes': {  
        'task': 'users.tasks.check_task_deadlines', 
        'schedule': crontab(minute='*/2'), 
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
