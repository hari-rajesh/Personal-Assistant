from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from .models import CustomUser, Task
from rest_framework.response import Response
from .serializers import CustomUserSerializer, TaskSerializer, UserUpdateSerializer
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from .oauth import send_email_via_gmail
from django.http import HttpResponse
from .utils import send_sms_via_twilio

class CreateUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class EditUserView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

from django.utils import timezone


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if username is None or password is None:
        return Response({'error': 'Please provide both username and password.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Fetch all overdue tasks for the user
    overdue_tasks = Task.objects.filter(user=user, deadline__lt=timezone.now(), status='Pending')

    if overdue_tasks.exists():
        subject = 'Overdue Tasks Notification'
        message = 'You have the following overdue tasks:\n\n'

        for task in overdue_tasks:
            message += f'- {task.title} (Due: {task.deadline})\n'

        message += '\nPlease take action to complete them.\n\nBest,\nTask Manager'
        recipient_list = user.email

        # Send email via Gmail API using OAuth
        success = send_email_via_gmail(subject, message, recipient_list)
        if success:
            print('Email sent successfully')
        else:
            print('Failed to send email')

        recipient_phone = user.phonenumber

        sms_body = message
        sms_success = send_sms_via_twilio(sms_body, recipient_phone)
        if sms_success:
            print('SMS sent successfully')
        else:
            print('Failed to send SMS')


    token, created = Token.objects.get_or_create(user=user)
    return Response({'token': token.key}, status=status.HTTP_200_OK)



class TaskCreateView(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user) 

class TaskDetailView(generics.RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user) 


class TaskUpdateView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        task = serializer.save()
        if task.is_overdue():
            subject = f'Overdue Task: "{task.title}"'
            message = f'Hi {task.user.username},\n\nYour task "{task.title}" is overdue since {task.deadline}.\n\nBest,\nTask Manager'
            recipient_list = task.user.email

            # Send email via Gmail API using OAuth
            # success = send_email_via_gmail(subject, message, recipient_list)
            # if success:
            #     print('Email sent successfully')
            # else:
            #     print('Failed to send email')


class TaskDeleteView(generics.DestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tasks_by_category(request):
    user = request.user
    category = request.query_params.get('category', None)
    if category:
        tasks = Task.objects.filter(user=user, category=category)
    else:
        tasks = Task.objects.filter(user=user)

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)


