
from django.urls import path
from .views import (
    PropertyDashboardView, create_property_view, PropertyDetailView,
    ContactListView, ContactCreateView, ContactDetailView, ContactEditView
)

urlpatterns = [
    path('dashboard/', PropertyDashboardView.as_view(), name='list'),
    path('crear/', create_property_view, name='create'),
    path('<int:pk>/', PropertyDetailView.as_view(), name='detail'),
    path('contactos/', ContactListView.as_view(), name='contact_list'),
    path('contactos/crear/', ContactCreateView.as_view(), name='contact_create'),
    path('contactos/<int:pk>/', ContactDetailView.as_view(), name='contact_detail'),
    path('contactos/<int:pk>/editar/', ContactEditView.as_view(), name='contact_edit'),
    path('', PropertyDashboardView.as_view(), name='dashboard_root'),
]
