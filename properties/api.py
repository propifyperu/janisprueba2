from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework import permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.db.models import Exists, OuterRef
from . import models
from django.shortcuts import get_object_or_404


from .models import Property, Requirement
from .serializers import PropertySerializer, PropertyWithDocsSerializer, RequirementSerializer, PropertyDocumentCreateSerializer, PropertyDocumentUpdateSerializer, DocumentTypeSerializer


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
        .annotate(
            has_legal_base=Exists(
                models.PropertyDocument.objects.filter(
                    property_id=OuterRef("pk"),
                    document_type__code__in=["103", "110"],
                    file__isnull=False,
                ).exclude(file="")
            ),
            has_study=Exists(
                models.PropertyDocument.objects.filter(
                    property_id=OuterRef("pk"),
                    document_type__code="101",
                    file__isnull=False,
                ).exclude(file="")
            ),
        )
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

        prop = self.get_queryset().get(pk=prop.pk)

        out = PropertyWithDocsSerializer(prop, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)
    

    @action(detail=True, methods=["patch"], url_path=r"documents/by-type/(?P<document_type_id>[^/.]+)", parser_classes=[MultiPartParser, FormParser],)
    def update_document_by_type(self, request, document_type_id=None, *args, **kwargs):
        prop = self.get_object()
        doc = get_object_or_404(
            models.PropertyDocument,
            property=prop,
            document_type_id=document_type_id,
        )

        serializer = PropertyDocumentUpdateSerializer(
            doc,
            data=request.data,
            partial=True,
            context={"request": request, "property": prop},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        prop = self.get_queryset().get(pk=prop.pk)

        out = PropertyWithDocsSerializer(prop, context={"request": request})
        return Response(out.data, status=status.HTTP_200_OK)

class RequirementViewSet(ModelViewSet):
    """
    CRUD completo para Requerimientos.
    """
    serializer_class = RequirementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['property_type', 'budget_type', 'contact__phone']
    search_fields = ['contact__phone', 'contact__first_name', 'contact__last_name']
    ordering_fields = ['created_at', 'budget_min', 'budget_max']

    def get_queryset(self):
        # El usuario ya está autenticado por Token, así que filtramos solo SUS requerimientos.
        return Requirement.objects.filter(is_active=True, created_by=self.request.user).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def general(self, request):
        """
        Retorna todos los requerimientos generales (de todos los agentes).
        """
        queryset = Requirement.objects.filter(is_active=True).order_by('-created_at')
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        # Soft delete: marcar como inactivo en lugar de borrar físicamente
        instance.is_active = False
        instance.save()

class DocumentTypeViewSet(GenericViewSet, ListModelMixin):
    queryset = models.DocumentType.objects.filter(is_active=True)
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None