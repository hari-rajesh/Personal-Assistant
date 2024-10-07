from celery import shared_task
from .utils import send_sms_via_twilio
from .oauth import send_email_via_gmail
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)



from django.db.models import Q

@shared_task
def check_task_deadlines():
    from .models import Task
    logger.info("Checking task deadlines")

    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)
    one_hour_ago = now - timedelta(hours=1)

    tasks = Task.objects.filter(
        deadline__lte=one_hour_from_now, 
        deadline__gt=now,  
        status__in=['Pending', 'In Progress'], 
    ).filter(
        Q(last_notification_sent__isnull=True) | Q(last_notification_sent__lte=one_hour_ago)
    )
    logger.info(f"Tasks found: {tasks.count()}")
    for task in tasks:
        logger.info(f"Sending reminders for task: {task.title}")
        send_reminders.delay(task, task.id, task.user.mobile_number, task.user.email, task.title, task.deadline)
