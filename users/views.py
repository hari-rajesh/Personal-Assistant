from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from .models import  Task, Profile
from .serializers import TaskSerializer, ProfileSerializer, UserSerializer, LoginSerializers, UpdateSerializer, PhoneNumberSerializer
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from .oauth import send_email_via_gmail
from django.http import HttpResponse
from .utils import send_sms_via_twilio
from django.shortcuts import render, redirect
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.http import JsonResponse
import requests
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from rest_framework.views import APIView
from google_auth_oauthlib.flow import Flow
import logging
from django.views.decorators.csrf import csrf_exempt


@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={201: 'User Created Successfully', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='put',
    request_body=UpdateSerializer,
    responses={200: 'User Updated Successfully', 400: 'Bad Request'}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_view(request):
    user = request.user
    serializer = UpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(generics.DestroyAPIView):
    User = get_user_model()
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get('pk') 
        user_to_delete = self.get_object()

        if request.user.profile.user_type == 'admin' or request.user.id == user_to_delete.id:
            user_to_delete.delete()
            return Response({"detail": "User Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "You are not authorized to delete this user."}, status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializers,
    responses={200: 'Login Successful', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializers(data=request.data)
    if serializer.is_valid():
        user1 = serializer.validated_data['user']
        username = request.data.get('username')
        password = request.data.get('password')   
        user = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        overdue_tasks = Task.objects.filter(user=user, deadline__lt=timezone.now(), status='Pending')

        if overdue_tasks.exists():
            subject = 'Overdue Tasks Notification'
            message = 'You have the following overdue tasks:\n\n'

            for task in overdue_tasks:
                message += f'- {task.title} (Due: {task.deadline})\n'

            message += '\nPlease take action to complete them.\n\nBest,\nTask Manager'
            recipient_list = user.email

            # ##Send email via Gmail API using OAuth
            # if user.profile.enable_email:
            #     success = send_email_via_gmail(subject, message, recipient_list)
            #     if success:
            #         print('Email sent successfully')
            #     else:
            #         print('Failed to send email')

            # ##Send SMS via Twillio 
            # recipient_phone = "+91"+user.mobile_number
            # if user.profile.enable_sms:
            #     sms_body = message
            #     sms_success = send_sms_via_twilio(sms_body, recipient_phone)
            #     if sms_success:
            #         print('SMS sent successfully')
            #     else:
            #         print('Failed to send SMS')

        refresh = RefreshToken.for_user(user1)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@swagger_auto_schema(
    method='post',
    responses={200: 'Logout Successful', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh = request.data.get('refresh')
        token = RefreshToken(refresh)
        token.blacklist()
        return Response({"message": "User logged out successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": "Invalid Token or Token already blacklisted"}, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh Token')
        }
    ),
    responses={200: 'Token Refreshed Successfully', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_view(request):
    try:
        refresh = request.data.get('refresh')
        token = RefreshToken(refresh)
        return Response({
            'access': str(token.access_token),
            'refresh':str(token)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



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

            ##Send email via Gmail API using OAuth

            if task.user.profile.enable_email:

                success = send_email_via_gmail(subject, message, recipient_list)
                if success:
                    print('Email sent successfully')
                else:
                    print('Failed to send email')
                recipient_phone = "+91" + task.user.mobile_number
            if task.user.profile.enable_sms:
                sms_body = message
                sms_success = send_sms_via_twilio(sms_body, recipient_phone)
                if sms_success:
                    print('SMS sent successfully')
                else:
                    print('Failed to send SMS')


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



class ProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure user is logged in

    # Get the profile of the logged-in user
    def get_object(self):
        return Profile.objects.get(user=self.request.user)
    
from rest_framework import serializers
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter


User = get_user_model()
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


from django.apps import apps

from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = apps.get_model(settings.AUTH_USER_MODEL)

class GoogleLoginCallback(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'error': 'Authorization code not provided'}, status=status.HTTP_400_BAD_REQUEST)

        token_url = 'https://oauth2.googleapis.com/token'
        payload = {
            'code': code,
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'redirect_uri': settings.REDIRECT_URI,
            'grant_type': 'authorization_code',
        }

        try:
            response = requests.post(token_url, data=payload, timeout=10)
            response.raise_for_status()
            tokens = response.json()

            if 'access_token' in tokens and 'id_token' in tokens:
                access_token = tokens['access_token']
                id_token_jwt = tokens['id_token']

                idinfo = id_token.verify_oauth2_token(
                    id_token_jwt, google_requests.Request(), settings.CLIENT_ID)

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')

                email = idinfo['email']
                name = idinfo.get('name', '')
                
                # Create or update user in the database
                user, created = User.objects.get_or_create(email=email)
                if created:
                    user.username = email  # Set username to email if it's a new user
                    user.set_unusable_password()  # Set an unusable password for social auth users
                user.first_name = name.split()[0] if name else ''
                user.last_name = ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
                user.save()


                return Response({
                    'user_id': user.id,
                    'email': user.email,
                    'name': user.get_full_name(),
                    'message': 'User successfully added/updated',
                    # 'access_token': access_token,  # Uncomment if using JWT
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to obtain tokens', 'details': tokens}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            return Response({'error': 'Network error occurred', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as e:
            return Response({'error': 'Invalid token', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class UpdatePhoneNumberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']

            request.user.mobile_number = mobile_number
            request.user.save()

            return Response({'message': 'Mobile number updated successfully!'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)













#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

class GoogleLoginView(APIView):
    """
    Redirects to Google's OAuth 2.0 consent screen for login.
    """
    def get(self, request, *args, **kwargs):
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=settings.REDIRECT_URI
        )

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent'  # Ensure refresh token is granted
        )
        
        return redirect(authorization_url)


class GoogleCallbackView(APIView):
    def get(self, request, *args, **kwargs):
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=settings.REDIRECT_URI
        )

        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials

        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        profile = request.user.profile
        profile.google_access_token = credentials.token
        profile.google_refresh_token = credentials.refresh_token
        profile.google_token_expiry = timezone.now() + timedelta(seconds=credentials.expiry)
        profile.save()

        return JsonResponse({'message': 'Google OAuth login successful'})




class TaskSyncGoogleCalendarView(APIView):

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User is not authenticated'}, status=401)

        profile = request.user.profile
        access_token = profile.google_access_token
        refresh_token = profile.google_refresh_token

        if not access_token or not refresh_token:
            return JsonResponse({'error': 'User is not authenticated with Google'}, status=400)

        # Build credentials from the user's profile tokens
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET
        )

        # Build the Google Calendar API service
        service = build('calendar', 'v3', credentials=credentials)

        # Example task data (you may want to get this from the request)
        task_data = request.data  # Assuming task data is passed in the request
        event = {
            'summary': task_data.get('title', 'Sample Task from Django App'),
            'description': task_data.get('description', 'This is a task synced from the Django app.'),
            'start': {
                'dateTime': task_data.get('start', '2024-09-30T09:00:00-07:00'),
                'timeZone': 'America/Los_Angeles',
            },
            'end': {
                'dateTime': task_data.get('end', '2024-09-30T10:00:00-07:00'),
                'timeZone': 'America/Los_Angeles',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            return JsonResponse({'message': 'Task synced to Google Calendar', 'event': event}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)