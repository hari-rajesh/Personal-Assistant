from celery import shared_task
from .utils import send_sms_via_twilio
from .oauth import send_email_via_gmail
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_reminders(task, task_id, phone_number, email, task_name, deadline):
    sms_body = f"Reminder: Your task '{task_name}' is due at {deadline}. Please complete it soon."
    email_subject = f"Reminder: Task '{task_name}' Deadline Approaching"
    email_body = f"Dear User, your task '{task_name}' is due at {deadline}. Please complete it soon."

    notification_sent = False

    if phone_number:
        logger.info(f"Sending SMS for task: {task_name}")
        try:
            send_sms_via_twilio(sms_body, phone_number)
            notification_sent = True
        except Exception as e:
            logger.error(f"Failed to send SMS for task '{task_name}': {e}")

    if email:
        logger.info(f"Sending Email for task: {task_name}")
        try:
            send_email_via_gmail(email_subject, email_body, email)
            notification_sent = True 
        except Exception as e:
            logger.error(f"Failed to send email for task '{task_name}': {e}")
    if notification_sent:
        logger.info(f"Updating last_notification_sent for task: {task_name}")
        task.last_notification_sent = timezone.now()
        try:
            task.save()
            logger.info(f"Successfully updated last_notification_sent for task: {task_name}")
            
        except Exception as e:
            logger.error(f"Failed to update last_notification_sent for task '{task_name}': {e}")


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
