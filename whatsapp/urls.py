from django.urls import path
from .views import whatsapp_webhook

app_name = 'whatsapp'

urlpatterns = [
    path('webhook/', whatsapp_webhook, name='webhook'),
]
