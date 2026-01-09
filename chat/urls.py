from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('compose/', views.compose, name='compose'),
    path('inbox/', views.inbox, name='inbox'),
    path('sent/', views.sent, name='sent'),
    path('c/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('api/send_message/', views.send_message, name='send_message'),
    path('api/fetch_messages/', views.fetch_messages, name='fetch_messages'),
    path('api/unread_count/', views.unread_count, name='unread_count'),
    path('api/mark_read/', views.mark_read, name='mark_read'),
    path('api/search_users/', views.search_users, name='search_users'),
]
