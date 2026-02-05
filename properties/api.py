from rest_framework.viewsets import GenericViewSet
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status


from .models import Property, Requirement
from .serializers import PropertySerializer, PropertyWithDocsSerializer, RequirementSerializer, PropertyDocumentCreateSerializer


class PropertyViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    """
    Read-only API for Properties.
    - list:    GET /dashboard/api/properties/
    - retrieve GET /dashboard/api/properties/{id}/
    - with-docs(detail): GET /dashboard/api/properties/{id}/with-docs/
    - with-docs(list):   GET /dashboard/api/properties/with-docs/
    """
    queryset = (
        Property.objects.filter(is_active=True)
        .select_related(
            'currency', 'property_type', 'status', 'responsible',
            'assigned_agent', 'owner', 'created_by'
        )
        .prefetch_related('documents__document_type')
    )

    serializer_class = PropertySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['province', 'district', 'property_type', 'status', 'currency']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action in ("with_docs", "with_docs_list"):
            return PropertyWithDocsSerializer
        return PropertySerializer

    @action(detail=True, methods=["get"], url_path="with-docs")
    def with_docs(self, request, *args, **kwargs):
        prop = self.get_object()
        serializer = self.get_serializer(prop, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="with-docs")
    def with_docs_list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="documents", parser_classes=[MultiPartParser, FormParser],)
    def create_document(self, request, *args, **kwargs):
        prop = self.get_object()

        serializer = PropertyDocumentCreateSerializer(
            data=request.data,
            context={"property": prop, "request": request}, 
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        out = PropertyWithDocsSerializer(prop, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

class RequirementViewSet(ModelViewSet):
    """
    CRUD completo para Requerimientos.
    """
    queryset = Requirement.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RequirementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property_type', 'budget_type']
    ordering_fields = ['created_at', 'budget_min', 'budget_max']

    def perform_destroy(self, instance):
        # Soft delete: marcar como inactivo en lugar de borrar físicamente
        instance.is_active = False
        instance.save()