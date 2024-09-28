from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from datetime import timedelta, datetime
from django.utils import timezone 
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    mobile_number = models.CharField(max_length=50)

    def __str__(self):
        return self.username
    



class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    RECURRENCE_CHOICES = [
        ('None', 'None'),
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    ]

    CATEGORY_CHOICES = [
        ('Work', 'Work'),
        ('Personal', 'Personal'),
        ('Shopping', 'Shopping'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Personal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    deadline = models.DateTimeField()
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='None')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.recurrence == 'Daily':
            self.deadline += timedelta(days=1)
        elif self.recurrence == 'Weekly':
            self.deadline += timedelta(weeks=1)
        elif self.recurrence == 'Monthly':
            self.deadline += timedelta(weeks=4)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def is_overdue(self):
        return self.deadline and self.deadline < timezone.now()
    


class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('premium', 'Premium_User'),
        ('guest', 'Guest_User'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='guest')

    google_access_token = models.CharField(max_length=500, blank=True, null=True)  # Store the access token
    google_refresh_token = models.CharField(max_length=500, blank=True, null=True) # Store the refresh token
    google_token_expires_at = models.DateTimeField(blank=True, null=True)

    def has_valid_google_access_token(self):
        """
        Checks if the stored Google access token is still valid.
        """
        return self.google_token_expiry and self.google_token_expiry > timezone.now()

    def __str__(self):
        return self.user.username
    

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()