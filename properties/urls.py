from django.urls import path, include
from . import views
from .api import PropertyViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='properties')

urlpatterns = [
    path('ultra-simple/', views.simple_properties_view, name='ultra_simple_list'),
    path('simple-list/', views.SimplePropertyListView.as_view(), name='simple_property_list'),
    path('dashboard/', views.PropertyDashboardView.as_view(), name='list'),
    path('marketing/whatsapp/track/<int:link_id>/', views.track_whatsapp_click, name='track_whatsapp_click'),
    path('crear/', views.create_property_view, name='create'),
    path('mis-propiedades/', views.MyPropertiesView.as_view(), name='my_properties'),
    path('<int:pk>/', views.PropertyDetailView.as_view(), name='detail'),
    path('borradores/', views.drafts_list_view, name='drafts'),
    path('borradores/<int:pk>/borrar/', views.delete_draft_view, name='delete_draft'),
    path('<int:pk>/timeline/', views.property_timeline_view, name='timeline'),
    path('<int:pk>/editar/', views.edit_property_view, name='edit'),
    path('contactos/', views.ContactListView.as_view(), name='contact_list'),
    path('contactos/crear/', views.ContactCreateView.as_view(), name='contact_create'),
    path('contactos/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contactos/<int:pk>/editar/', views.ContactEditView.as_view(), name='contact_edit'),
    # Requerimientos (búsquedas de clientes)
    path('requerimientos/', views.RequirementListView.as_view(), name='requirements_list'),
    path('requerimientos/<int:pk>/', views.RequirementDetailView.as_view(), name='requirements_detail'),
    path('requerimientos/crear/', views.requirement_create_view, name='requirements_create'),
    path('requerimientos/mis-requerimientos/', views.MyRequirementsView.as_view(), name='requirements_my'),
    path('requerimientos/<int:pk>/editar/', views.RequirementUpdateView.as_view(), name='requirements_edit'),
    path('requerimientos/<int:pk>/borrar/', views.requirement_delete_view, name='requirements_delete'),
    # Agenda y Eventos
    path('agenda/', views.agenda_calendar_view, name='agenda_calendar'),
    path('agenda/eventos/crear/', views.event_create_view, name='event_create'),
    path('agenda/eventos/<int:pk>/editar/', views.event_edit_view, name='event_edit'),
    path('agenda/eventos/<int:pk>/borrar/', views.event_delete_view, name='event_delete'),
    path('api/events/', views.api_events_json, name='api_events'),
    # APIs
    path('api/property-subtypes/', views.api_property_subtypes, name='api_property_subtypes'),
    path('api/provinces/', views.api_provinces, name='api_provinces'),
    path('api/districts/', views.api_districts, name='api_districts'),
    path('api/urbanizations/', views.api_urbanizations, name='api_urbanizations'),
    path('api/document-types/', views.api_document_types, name='api_document_types'),
    path('api/image-types/', views.api_image_types, name='api_image_types'),
    path('api/roomtypes/', views.api_roomtypes, name='api_roomtypes'),
    path('api/video-types/', views.api_video_types, name='api_video_types'),
    # WhatsApp
    path('whatsapp/enlaces/<int:property_id>/', views.whatsapp_links_list, name='whatsapp_links'),
    path('whatsapp/enlaces/<int:property_id>/crear/', views.whatsapp_link_create, name='whatsapp_link_create'),
    path('whatsapp/enlaces/<int:link_id>/borrar/', views.whatsapp_link_delete, name='whatsapp_link_delete'),
    path('whatsapp/leads/', views.leads_list, name='leads_list'),
    path('whatsapp/leads/<int:property_id>/', views.leads_list, name='leads_list_by_property'),
    path('whatsapp/leads/detalle/<int:lead_id>/', views.lead_detail, name='lead_detail'),
    path('crm/', views.crm_dashboard, name='crm_dashboard'),
    path('marketing/propiedades/', views.marketing_properties_list, name='marketing_properties_list'),
    path('marketing/dashboard/', views.marketing_utm_dashboard, name='marketing_utm_dashboard'),
    path('api/', include(router.urls)),
    # Servir imágenes almacenadas como blob en la tabla `property_images`
    path('images/blob/<int:pk>/', views.image_blob_view, name='image_blob'),
    path('', views.PropertyDashboardView.as_view(), name='dashboard_root'),
]
