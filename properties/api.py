from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property
from .serializers import PropertySerializer


class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only API for Properties used by mobile apps.

    - Lists only active properties
    - Uses related prefetch/select for efficiency
    """
    queryset = Property.objects.filter(is_active=True).select_related(
        'currency', 'property_type', 'status', 'responsible', 'assigned_agent'
    ).prefetch_related('images', 'videos', 'documents', 'rooms')
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['province', 'district', 'property_type', 'status', 'currency']
    search_fields = ['title', 'description', 'address']
    ordering_fields = ['price', 'created_at', 'updated_at']
