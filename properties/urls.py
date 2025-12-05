from django.urls import path
from django.urls import path, include
from .views import (
    PropertyDashboardView, create_property_view, PropertyDetailView,
    edit_property_view,
    property_timeline_view, drafts_list_view, delete_draft_view,
    ContactListView, ContactCreateView, ContactDetailView, ContactEditView,
    api_property_subtypes, api_provinces, api_districts, api_urbanizations,
    api_document_types, api_image_types, api_roomtypes, api_video_types,
    SimplePropertyListView, simple_properties_view
)
from .api import PropertyViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='properties')

urlpatterns = [
    path('ultra-simple/', simple_properties_view, name='ultra_simple_list'),
    path('simple-list/', SimplePropertyListView.as_view(), name='simple_property_list'),
    path('dashboard/', PropertyDashboardView.as_view(), name='list'),
    path('crear/', create_property_view, name='create'),
    path('<int:pk>/', PropertyDetailView.as_view(), name='detail'),
    path('borradores/', drafts_list_view, name='drafts'),
    path('borradores/<int:pk>/borrar/', delete_draft_view, name='delete_draft'),
    path('<int:pk>/timeline/', property_timeline_view, name='timeline'),
    path('<int:pk>/editar/', edit_property_view, name='edit'),
    path('contactos/', ContactListView.as_view(), name='contact_list'),
    path('contactos/crear/', ContactCreateView.as_view(), name='contact_create'),
    path('contactos/<int:pk>/', ContactDetailView.as_view(), name='contact_detail'),
    path('contactos/<int:pk>/editar/', ContactEditView.as_view(), name='contact_edit'),
    path('api/property-subtypes/', api_property_subtypes, name='api_property_subtypes'),
    path('api/provinces/', api_provinces, name='api_provinces'),
    path('api/districts/', api_districts, name='api_districts'),
    path('api/urbanizations/', api_urbanizations, name='api_urbanizations'),
    path('api/document-types/', api_document_types, name='api_document_types'),
    path('api/image-types/', api_image_types, name='api_image_types'),
    path('api/roomtypes/', api_roomtypes, name='api_roomtypes'),
    path('api/video-types/', api_video_types, name='api_video_types'),
    path('api/', include(router.urls)),
    path('', PropertyDashboardView.as_view(), name='dashboard_root'),
]
