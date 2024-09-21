from django.urls import path
from .views import TaskCreateView, TaskDeleteView, TaskDetailView, TaskListView, TaskUpdateView, tasks_by_category
from .views import  register_view, update_view, login_view, logout_view, refresh_view, ProfileDetailUpdateView, UserDeleteView

urlpatterns = [
    path('register/', register_view, name="register"),
    path('update/', update_view, name="update"),
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('refresh/', refresh_view, name="refresh"),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='delete-user'),  # Ensure it's 'user_id'
    path('tasks/', TaskListView.as_view(), name='task_list'),  # GET request to list tasks
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),  # Create a task
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),  # GET request to retrieve a task
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='edit_task'),  # PUT/PATCH request to update a task
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='delete_task'),  # DELETE request to remove a task
    path('tasks/category/', tasks_by_category, name='tasks-by-category'),
    path('profile/', ProfileDetailUpdateView.as_view(), name='profile-detail-update'),

]
