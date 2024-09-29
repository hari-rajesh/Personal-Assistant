from celery import shared_task
from .utils import send_sms_via_twilio
from .oauth import send_email_via_gmail
from django.utils import timezone
from datetime import timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

@shared_task
def send_reminders(task_id, phone_number, email, task_name, deadline):
    sms_body = f"Reminder: Your task '{task_name}' is due at {deadline}. Please complete it soon."
    email_subject = f"Reminder: Task '{task_name}' Deadline Approaching"
    email_body = f"Dear User, your task '{task_name}' is due at {deadline}. Please complete it soon."

    if phone_number:
        logger.info(f"Sending SMS for task: {task_name}")
        try:
            send_sms_via_twilio(sms_body, phone_number)
        except Exception as e:
            logger.error(f"Failed to send SMS for task '{task_name}': {e}")

    if email:
        logger.info(f"Sending Email for task: {task_name}")
        try:
            send_email_via_gmail(email_subject, email_body, email)
        except Exception as e:
            logger.error(f"Failed to send email for task '{task_name}': {e}")


@shared_task
def check_task_deadlines():
    from .models import Task  # Your task model
    logger.info("Checking task deadlines")  # Added logging

    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)

    tasks = Task.objects.filter(deadline__lte=one_hour_from_now, deadline__gt=now)

    logger.info(f"Tasks found: {tasks.count()}")  # Log number of tasks found

    for task in tasks:
        logger.info(f"Sending reminders for task: {task.title}")
        send_reminders.delay(task.id, task.user.mobile_number, task.user.email, task.title, task.deadline)
