from django.urls import path
from .views import (
    PropertyDashboardView, create_property_view, PropertyDetailView,
    ContactListView, ContactCreateView, ContactDetailView, ContactEditView,
    api_property_subtypes, api_provinces, api_districts, api_urbanizations,
    api_document_types, api_image_types, api_roomtypes
)

urlpatterns = [
    path('dashboard/', PropertyDashboardView.as_view(), name='list'),
    path('crear/', create_property_view, name='create'),
    path('<int:pk>/', PropertyDetailView.as_view(), name='detail'),
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
    path('', PropertyDashboardView.as_view(), name='dashboard_root'),
]
