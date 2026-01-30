from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("api/list/", views.notifications_list, name="api_list"),
    path("api/unread-count/", views.notifications_unread_count, name="api_unread_count"),
    path("api/<int:pk>/mark-read/", views.notification_mark_read, name="api_mark_read"),
    path("api/mark-read-bulk/", views.notifications_mark_read_bulk, name="api_mark_read_bulk"),
]