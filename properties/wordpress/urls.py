from django.urls import path
from .wordpress_views import (
    WPAuthTestView,
    WPSyncManyView,
    WPSyncOneView,
    WPGetOneView,
    WPDeleteOneView,
)

urlpatterns = [
    path("internal/wp/auth-test/", WPAuthTestView.as_view()),
    path("internal/wp/sync/", WPSyncManyView.as_view()),
    path("internal/wp/sync/<int:property_id>/", WPSyncOneView.as_view()),
    path("internal/wp/property/<int:property_id>/", WPGetOneView.as_view()),
    path("internal/wp/property/<int:property_id>/delete/", WPDeleteOneView.as_view()),
]