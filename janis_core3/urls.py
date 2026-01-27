"""
URL configuration for janis_core3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .api_views import revoke_refresh_token
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from .media_views import media_proxy
from django.urls import re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('dashboard/', include(('properties.urls', 'properties'), namespace='properties')),
    path('', RedirectView.as_view(url='/users/login/', permanent=False)),
    path('security/', include(('security.urls', 'security'), namespace='security')),
    path('whatsapp/', include(('whatsapp.urls', 'whatsapp'), namespace='whatsapp')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('tasks/', include('tasks.urls', namespace='tasks')),
    # JWT token endpoints for mobile clients
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/revoke/', revoke_refresh_token, name='token_revoke'),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Proxy media route for private Azure blobs (always enabled)
urlpatterns += [
    re_path(r'^media-proxy/(?P<path>.*)$', media_proxy, name='media_proxy'),
]
