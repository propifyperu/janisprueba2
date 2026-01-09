from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('c/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('api/send_message/', views.send_message, name='send_message'),
    path('api/fetch_messages/', views.fetch_messages, name='fetch_messages'),
]
