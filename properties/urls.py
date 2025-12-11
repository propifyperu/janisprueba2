from django.urls import path
from django.urls import path, include
from .views import (
    PropertyDashboardView, create_property_view, PropertyDetailView,
    edit_property_view,
    property_timeline_view, drafts_list_view, delete_draft_view,
    ContactListView, ContactCreateView, ContactDetailView, ContactEditView,
    api_property_subtypes, api_provinces, api_districts, api_urbanizations,
    api_document_types, api_image_types, api_roomtypes, api_video_types,
    SimplePropertyListView, simple_properties_view,
    # WhatsApp
    whatsapp_links_list, whatsapp_link_create, whatsapp_link_delete,
    leads_list, lead_detail, crm_dashboard,
    marketing_properties_list, marketing_utm_dashboard
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
    # WhatsApp
    path('whatsapp/enlaces/<int:property_id>/', whatsapp_links_list, name='whatsapp_links'),
    path('whatsapp/enlaces/<int:property_id>/crear/', whatsapp_link_create, name='whatsapp_link_create'),
    path('whatsapp/enlaces/<int:link_id>/borrar/', whatsapp_link_delete, name='whatsapp_link_delete'),
    path('whatsapp/leads/', leads_list, name='leads_list'),
    path('whatsapp/leads/<int:property_id>/', leads_list, name='leads_list_by_property'),
    path('whatsapp/leads/detalle/<int:lead_id>/', lead_detail, name='lead_detail'),
    path('crm/', crm_dashboard, name='crm_dashboard'),
    path('marketing/propiedades/', marketing_properties_list, name='marketing_properties_list'),
    path('marketing/dashboard/', marketing_utm_dashboard, name='marketing_utm_dashboard'),
    path('api/', include(router.urls)),
    path('', PropertyDashboardView.as_view(), name='dashboard_root'),
]
