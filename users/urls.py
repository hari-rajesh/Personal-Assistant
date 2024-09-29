from django.urls import path, include
from .views import (
    register_view, update_view, login_view, logout_view, refresh_view, ProfileDetailUpdateView,
    UserDeleteView
)
from .views import (
    TaskCreateView, TaskDeleteView, TaskDetailView, TaskListView, TaskUpdateView, tasks_by_category,
    UpdatePhoneNumberView, GoogleLoginCallback, GoogleCalendarEventView
)

urlpatterns = [
    path('register/', register_view, name="register"),
    path('update/<int:pk>/', update_view, name='update-user'),
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('refresh/', refresh_view, name="refresh"),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='delete-user'),
    path('profile/', ProfileDetailUpdateView.as_view(), name='profile-detail-update'),
    # path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='edit_task'),
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='delete_task'),
    path('tasks/category/', tasks_by_category, name='tasks-by-category'),
    path('dj-rest-auth/update-phone/', UpdatePhoneNumberView.as_view(), name='update_phone'),
    path('oauth2callback/', GoogleLoginCallback.as_view(), name='oauth2callback'),
    path('googlecalendar/<int:id>/add/', GoogleCalendarEventView.as_view(), name='sync_google_calendar'),
    # path('googlecalendar/', GoogleCalendarEventViewToken.as_view(), name='googlecalendar')
]