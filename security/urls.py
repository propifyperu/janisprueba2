from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('devices/', views.device_list, name='device_list'),
    path('devices/<int:pk>/status/', views.device_status_update, name='device_status_update'),
    path('verify-device/', views.verify_device, name='verify_device'),
    path('verify-device/<int:device_id>/', views.verify_device, name='verify_device_id'),
]
