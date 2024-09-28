from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from .models import  Task, Profile
from .serializers import TaskSerializer, ProfileSerializer, UserSerializer, LoginSerializers, UpdateSerializer, PhoneNumberSerializer, GoogleCalendarEventSerializer
from django.conf import settings
from .oauth import send_email_via_gmail
from .utils import send_sms_via_twilio
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission
from django.apps import apps
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from datetime import datetime
current_time = datetime.now().isoformat()

class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.profile.user_type == 'admin'


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
@permission_classes([IsAdminOrSelf])
def update_view(request, pk):
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if not IsAdminOrSelf().has_object_permission(request, None, user):
        return Response({"error": "You don't have permission to update this user"}, status=status.HTTP_403_FORBIDDEN)

    serializer = UpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserDeleteView(generics.DestroyAPIView):
    User = get_user_model()
    queryset = User.objects.all()
    permission_classes = [IsAdminOrSelf]

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
@permission_classes([IsAdminOrSelf])
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
@permission_classes([IsAdminOrSelf])
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
    permission_classes = [IsAdminOrSelf]


class TaskListView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrSelf]
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user) 
    

class TaskDetailView(generics.RetrieveAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrSelf]

    # def get_queryset(self):
    #     return Task.objects.filter(user=self.request.user) 


class TaskUpdateView(generics.UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrSelf]

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
    permission_classes = [IsAdminOrSelf] 


@api_view(['GET'])
@permission_classes([IsAdminOrSelf])
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
    permission_classes = [IsAdminOrSelf]  # Ensure user is logged in

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

User = apps.get_model(settings.AUTH_USER_MODEL)


class GoogleLoginCallback(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            code = request.query_params.get('code')
            if not code:
                return Response({'error': 'Missing authorization code.'}, status=status.HTTP_400_BAD_REQUEST)

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                'code': code,
                'client_id': settings.CLIENT_ID,
                'client_secret': settings.CLIENT_SECRET,
                'redirect_uri': settings.REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
            response = requests.post(token_url, data=data)
            token_info = response.json()

            if response.status_code == 200 and 'access_token' in token_info:
                access_token = token_info['access_token']
                refresh_token = token_info.get('refresh_token')
                expires_in = token_info['expires_in']
                expiration_time = timezone.now() + timedelta(seconds=expires_in)

                user_info_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
                user_info_response = requests.get(user_info_url)

                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    users = User.objects.filter(email=user_info['email'])
                    user = users.first()

                    if not users.exists():
                        user = User.objects.create(
                            email=user_info['email'],
                            username=user_info.get('email', '').split('@')[0],
                            first_name=user_info.get('given_name', ''),
                            last_name=user_info.get('family_name', '')
                        )

                    # Update or create profile
                    profile, _ = Profile.objects.get_or_create(user=user)
                    profile.google_access_token = access_token
                    profile.google_refresh_token = refresh_token
                    profile.google_token_expires_at = expiration_time
                    profile.save()

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': 'User successfully logged in.',
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }, status=status.HTTP_200_OK)

                return Response({'error': 'Failed to fetch user info.'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'error': 'Failed to obtain access token.'}, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            return Response({'error': f'HTTP Request failed: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'Unexpected error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UpdatePhoneNumberView(APIView):
    permission_classes = [IsAdminOrSelf]

    def post(self, request, *args, **kwargs):
        serializer = PhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data['mobile_number']

            request.user.mobile_number = mobile_number
            request.user.save()

            return Response({'message': 'Mobile number updated successfully!'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




def refresh_google_access_token(refresh_token):
    token_url = 'https://oauth2.googleapis.com/token'
    payload = {
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }

    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        tokens = response.json()
        return tokens['access_token'], tokens.get('expires_in', 3600)
    return None, None  # Return None for both if refresh fails

import pytz

def format_datetime(dt_string):
    original_dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")
    desired_tz = pytz.timezone("Asia/Kolkata")
    localized_dt = desired_tz.localize(original_dt)
    formatted_dt = localized_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    formatted_dt = formatted_dt[:-2] + ":" + formatted_dt[-2:]

    return formatted_dt


def create_google_calendar_event(user1, task):
    token_expiry_time = user1.profile.google_token_expires_at
    refresh_token = user1.profile.google_refresh_token
    access_token = user1.profile.google_access_token
    expires_in = None  # Initialize expires_in at the start of the function     
    # Check if the access token is expired
    if timezone.now() >= token_expiry_time:
        print("Access token has expired. Refreshing the token...")
        # Refresh the access token using the refresh token
        access_token, expires_in = refresh_google_access_token(refresh_token)
        if not access_token:
            return {'error': 'Failed to refresh the access token.'}, None  # Explicitly return error
    
    creds = Credentials(token=access_token)

    service = build('calendar', 'v3', credentials=creds)

    current_time = format_datetime(timezone.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
    task_deadline = format_datetime(task.deadline.strftime("%Y-%m-%d %H:%M:%S.%f"))

    event = {
        'summary': task.title,
        'location': 'Google Meet',
        'description': task.description,
        'start': {
            'dateTime': task_deadline,
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': current_time,
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # Email reminder 1 day before
                {'method': 'popup', 'minutes': 10},       # Popup reminder 10 minutes before
            ],
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event, expires_in
    except Exception as e:
        return {'error': str(e)}, None  # Handle Google API errors


# def create_google_calendar_event(access_token, refresh_token, token_expiry_time, task):
#     expires_in = None  # Initialize expires_in at the start of the function     
#     # Check if the access token is expired
#     if datetime.now() >= token_expiry_time:
#         print("Access token has expired. Refreshing the token...")
#         # Refresh the access token using the refresh token
#         access_token, expires_in = refresh_google_access_token(refresh_token)
#         if not access_token:
#             return {'error': 'Failed to refresh the access token.'}, None  # Explicitly return error

#     creds = Credentials(token=access_token)
#     service = build('calendar', 'v3', credentials=creds)

#     event = {
#         'summary': task.title,  # Use task title
#         'location': task.location if hasattr(task, 'location') else '',  # Use task location if exists
#         'description': task.description,  # Use task description
#         'start': {
#             'dateTime': task.start_time.isoformat(),  # Ensure task has start_time
#             'timeZone': 'America/Los_Angeles',  # Adjust time zone as needed
#         },
#         'end': {
#             'dateTime': task.deadline.isoformat(),  # Ensure task has end_time
#             'timeZone': 'America/Los_Angeles',  # Adjust time zone as needed
#         },
#         'reminders': {
#             'useDefault': False,
#             'overrides': [
#                 {'method': 'email', 'minutes': 24 * 60},  # Email reminder 1 day before
#                 {'method': 'popup', 'minutes': 10},       # Popup reminder 10 minutes before
#             ],
#         },
#     }

#     try:
#         event = service.events().insert(calendarId='primary', body=event).execute()
#         return event, expires_in
#     except Exception as e:
#         return {'error': str(e)}, None  # Handle Google API errors



import logging

logger = logging.getLogger(__name__)

class GoogleCalendarEventView(APIView):
    permission_classes = [IsAdminOrSelf]


    def post(self, request, id):
        print(f"Request user: {request.user}, Data: {request.data}, Task ID: {id}")

        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = GoogleCalendarEventSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


        access_token = serializer.validated_data['access_token']
        # refresh_token = serializer.validated_data['refresh_token']
        token_expiry_time = serializer.validated_data['token_expiry_time']


        try:
            user1 = request.user
            task = Task.objects.get(id=id, user=request.user)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found or you do not have permission to access it.'}, status=status.HTTP_404_NOT_FOUND)


        if not token_expiry_time:
            return Response({'error': 'Token expiry time not provided'}, status=status.HTTP_400_BAD_REQUEST)


        token_expiry_time = datetime.now() + timedelta(seconds=token_expiry_time)

        logger.info(f"Creating calendar event for task {task.id} with access token {access_token[:10]}...")

        event, expires_in = create_google_calendar_event(user1, task)

        if event is None or 'error' in event:
            return Response({'error': event.get('error', 'Unknown error occurred')}, status=status.HTTP_400_BAD_REQUEST)


        if expires_in:
            new_expiry_time = datetime.now() + timedelta(seconds=expires_in)
            return Response({
                'event': event,
                'new_token_expiry_time': new_expiry_time.isoformat()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({'event': event}, status=status.HTTP_201_CREATED)
