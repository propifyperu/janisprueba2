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
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


from .models import Property, Requirement
from .serializers import PropertySerializer, PropertyWithDocsSerializer, RequirementSerializer, PropertyDocumentCreateSerializer, PropertyDocumentUpdateSerializer, DocumentTypeSerializer


class PropertyViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    LEGAL_BASE_CODES = {"103", "110"}   # partida registral / contrato corretaje
    LEGAL_STUDY_CODE = "101"           # estudio de títulos

    PARTIDA_CODE = "110"  # ✅ AJUSTA si tu Partida es otro code
    def _has_partida_min(self, prop) -> bool:
        """
        True si la propiedad tiene Partida Registral con:
        - file cargado OR
        - reference_number lleno
        """
        qs = prop.documents.filter(document_type__code=self.PARTIDA_CODE)

        has_file = qs.filter(file__isnull=False).exclude(file="").exists()
        has_ref  = qs.exclude(reference_number__isnull=True).exclude(reference_number="").exists()

        return has_file or has_ref

    def _user_area_code(self, user) -> str:
        a = getattr(user, "area", None) or getattr(getattr(user, "role", None), "area", None)

        # si tienes code úsalo; si no, usa name
        code = (getattr(a, "code", "") or "").strip().lower()
        if code:
            return code

        name = (getattr(a, "name", "") or "").strip().lower()
        return name  # ej: "legal", "marketing", etc.

    def _property_has_legal_base(self, prop) -> bool:
        return prop.documents.filter(
            document_type__code__in=self.LEGAL_BASE_CODES,
            file__isnull=False,
        ).exclude(file="").exists()

    def _assert_can_upload_doc(self, request, prop, doc_type):
        doc_code = str(getattr(doc_type, "code", "")).strip()

        # SOLO REGLA PARA ESTUDIO DE TÍTULOS (101)
        if doc_code == self.LEGAL_STUDY_CODE:
            if self._user_area_code(request.user) != "legal":
                raise PermissionDenied("Solo el área LEGAL puede subir/reemplazar el Estudio de Títulos.")

            if not self._property_has_legal_base(prop):
                raise PermissionDenied(
                    "Antes de subir el Estudio de Títulos debes cargar primero la Partida Registral o el Contrato de Corretaje."
                )
            
    def _assert_can_delete_doc(self, request, doc_type):
        doc_code = str(getattr(doc_type, "code", "")).strip()
        if doc_code == self.LEGAL_STUDY_CODE and self._user_area_code(request.user) != "legal":
            raise PermissionDenied("Solo el área LEGAL puede eliminar el Estudio de Títulos.")
        
    queryset = (
        Property.objects.all()
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
    
    @action(detail=True, methods=["post"], url_path="publish", permission_classes=[permissions.IsAuthenticated],)
    def publish(self, request, *args, **kwargs):
        prop = self.get_object()

        # ✅ regla simple: solo dueño publica (igual que delete)
        if not request.user.is_superuser and getattr(prop, "created_by_id", None) != request.user.id:
            raise PermissionDenied("No puedes publicar una propiedad que no es tuya.")

        if not getattr(prop, "is_draft", False):
            return Response({"detail": "Esta propiedad ya está publicada."}, status=status.HTTP_400_BAD_REQUEST)

        if getattr(prop, "availability_status", "") != "catchment":
            return Response({"detail": "Solo puedes publicar propiedades en 'En proceso de captación'."}, status=status.HTTP_400_BAD_REQUEST)

        if not self._has_partida_min(prop):
            return Response({
                "detail": (
                    "Para publicar tu propiedad, primero completa la Partida Registral "
                    "(sube el archivo o registra el número). Luego vuelve a intentar."
                ),
                "missing": ["partida_registral"]
            }, status=status.HTTP_400_BAD_REQUEST)

        # ✅ publicar
        prop.is_draft = False
        prop.is_active = True
        prop.availability_status = "available" 
        prop.save(update_fields=["is_draft", "is_active", "availability_status"])

        return Response({
            "detail": "Propiedad publicada. Ahora está visible y figura como Disponible.",
            "property_id": prop.id
        }, status=status.HTTP_200_OK)
    
    @action( detail=True, methods=["delete"], url_path=r"documents/delete-by-type/(?P<document_type_id>[^/.]+)", permission_classes=[permissions.IsAuthenticated],)
    def delete_document_by_type(self, request, document_type_id=None, *args, **kwargs):
        prop = self.get_object()

        if getattr(prop, "created_by_id", None) != getattr(request.user, "id", None):
            raise PermissionDenied("No puedes eliminar documentos de una propiedad que no es tuya.")

        doc = get_object_or_404(
            models.PropertyDocument,
            property=prop,
            document_type_id=document_type_id,
        )

        self._assert_can_delete_doc(request, doc.document_type)

        if getattr(doc, "file", None):
            doc.file.delete(save=False)

        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

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
    
    @action(detail=False, methods=["get"], url_path="my-properties/with-docs", permission_classes=[permissions.IsAuthenticated],)
    def my_properties_with_docs(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(created_by=request.user)

        # si quieres que también incluya propiedades donde soy responsible o assigned_agent,
        # lo vemos luego. Por ahora SOLO "mías" = created_by.

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = PropertyWithDocsSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = PropertyWithDocsSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"], url_path="documents", parser_classes=[MultiPartParser, FormParser],)
    def create_document(self, request, *args, **kwargs):
        prop = self.get_object()

        serializer = PropertyDocumentCreateSerializer(
            data=request.data,
            context={"property": prop, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        doc_type = serializer.validated_data["document_type"]
        self._assert_can_upload_doc(request, prop, doc_type)

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
        self._assert_can_upload_doc(request, prop, doc.document_type)

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