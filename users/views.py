from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from .models import  Task
from .serializers import TaskSerializer, ProfileSerializer, UserSerializer, LoginSerializer, UpdateSerializer
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from .oauth import send_email_via_gmail
from django.http import HttpResponse
from .utils import send_sms_via_twilio
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model



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
        user_id = kwargs.get('pk')  # Assuming you're using 'pk' to identify the user
        user_to_delete = self.get_object()

        # Check if the requesting user is either the user themselves or an admin
        if request.user.profile.user_type == 'admin' or request.user.id == user_to_delete.id:
            user_to_delete.delete()
            return Response({"detail": "User Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "You are not authorized to delete this user."}, status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={200: 'Login Successful', 400: 'Bad Request'}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user1 = serializer.validated_data['user']
        username = request.data.get('username')
        password = request.data.get('password')   
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


from .models import Profile
from .serializers import ProfileSerializer

class ProfileDetailUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure user is logged in

    # Get the profile of the logged-in user
    def get_object(self):
        return Profile.objects.get(user=self.request.user)