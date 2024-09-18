from django.urls import path
from .views import CreateUserView, TaskCreateView, TaskDeleteView, TaskDetailView, TaskListView, TaskUpdateView, login_view

urlpatterns = [
    path('create-user/', CreateUserView.as_view(), name='create_user'),
    path('login/', login_view, name='login'),  # User login
    path('tasks/', TaskListView.as_view(), name='task_list'),  # GET request to list tasks
    path('tasks/create/', TaskCreateView.as_view(), name='task_create'),  # Create a task
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),  # GET request to retrieve a task
    path('tasks/<int:pk>/edit/', TaskUpdateView.as_view(), name='edit_task'),  # PUT/PATCH request to update a task
    path('tasks/<int:pk>/delete/', TaskDeleteView.as_view(), name='delete_task'),  # DELETE request to remove a task
]
