from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('create/', views.task_create, name='task_create'),
    path('update-status/<int:pk>/', views.task_update_status, name='task_update_status'),
    path('edit/', views.task_edit, name='task_edit'),
    path('delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('add-comment/', views.task_add_comment, name='task_add_comment'),
]
