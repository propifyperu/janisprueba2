from django.urls import path
from .views import twilio_webhook

app_name = 'whatsapp'

urlpatterns = [
    path('twilio/', twilio_webhook, name='twilio_webhook'),
]
