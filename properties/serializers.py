# serializers.py

from rest_framework import serializers
from . import models
from rest_framework import serializers
from properties.models import Property

class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.PropertyImage
        fields = ('id', 'caption', 'order', 'is_primary', 'image_url')

    def get_image_url(self, obj):
        request = self.context.get('request') if self.context else None
        if obj and getattr(obj, 'image', None) and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class PropertyVideoSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = models.PropertyVideo
        fields = ('id', 'title', 'description', 'video_url')

    def get_video_url(self, obj):
        request = self.context.get('request') if self.context else None
        if obj and getattr(obj, 'video', None) and request:
            return request.build_absolute_uri(obj.video.url)
        return None


class PropertyDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    document_type = serializers.CharField(source="document_type.name", read_only=True)  # 👈 agrega esto

    class Meta:
        model = models.PropertyDocument
        fields = ('id', 'title', 'description', 'document_type', 'file_url', 'is_approved')

    def get_file_url(self, obj):
        request = self.context.get('request') if self.context else None
        if obj and getattr(obj, 'file', None):
            url = obj.file.url
            return request.build_absolute_uri(url) if request else url
        return None

    class Meta:
        model = models.PropertyDocument
        fields = ('id', 'title', 'description', 'document_type', 'file_url', 'is_approved')


class PropertyRoomSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source='level.name', read_only=True)
    room_type = serializers.CharField(source='room_type.name', read_only=True)

    class Meta:
        model = models.PropertyRoom
        fields = ('id', 'level', 'room_type', 'name', 'width', 'length', 'area', 'floor_type', 'description', 'order')


class PropertyFinancialInfoSerializer(serializers.ModelSerializer):
    negotiation_status = serializers.CharField(source='negotiation_status.name', read_only=True)

    class Meta:
        model = models.PropertyFinancialInfo
        fields = ('initial_commission_percentage', 'final_commission_percentage', 'final_amount', 'negotiation_status')


class PropertyOwnerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = models.PropertyOwner
        fields = ('id', 'first_name', 'last_name', 'maternal_last_name', 'full_name', 'phone', 'secondary_phone', 'email')

    def get_full_name(self, obj):
        try:
            if hasattr(obj, 'full_name') and callable(obj.full_name):
                return obj.full_name()
            parts = [p for p in (obj.first_name, obj.last_name, obj.maternal_last_name) if p]
            return ' '.join(parts) if parts else None
        except Exception:
            return None


class PropertySerializer(serializers.ModelSerializer):
    # Campos que la app necesita y que no están directamente en el modelo
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    property_type = serializers.CharField(source='property_type.name', read_only=True)
    status = serializers.CharField(source='status.name', read_only=True)
    owner = PropertyOwnerSerializer(read_only=True)
    responsible_name = serializers.SerializerMethodField()

    images = PropertyImageSerializer(many=True, read_only=True)
    videos = PropertyVideoSerializer(many=True, read_only=True)
    documents = PropertyDocumentSerializer(many=True, read_only=True)
    rooms = PropertyRoomSerializer(many=True, read_only=True)
    financial_info = PropertyFinancialInfoSerializer(read_only=True)

    class Meta:
        model = models.Property
        # Lista de campos que se enviarán a la app
        fields = (
            'id', 'code', 'title', 'description', 'price', 'currency_symbol', 'property_type',
            'status', 'bedrooms', 'bathrooms', 'half_bathrooms', 'land_area', 'built_area',
            'garage_spaces', 'garage_type', 'has_maintenance', 'maintenance_fee',
            'unit_location',
            'owner', 'responsible_name', 'assigned_agent', 'created_at', 'updated_at',
            'latitude', 'longitude', 'images', 'videos', 'documents', 'rooms', 'financial_info',
            'real_address', 'exact_address', 'coordinates', 'department', 'province', 'district', 'urbanization',
        )

    def get_latitude(self, obj):
        try:
            coords_str = str(obj.coordinates)
            return float(coords_str.split(',')[0].strip())
        except (ValueError, IndexError, AttributeError):
            return None

    def get_longitude(self, obj):
        try:
            coords_str = str(obj.coordinates)
            return float(coords_str.split(',')[1].strip())
        except (ValueError, IndexError, AttributeError):
            return None

    def get_responsible_name(self, obj):
        try:
            responsible = obj.responsible
            if responsible is None:
                return None
            if hasattr(responsible, 'get_full_name'):
                full = responsible.get_full_name()
                if full:
                    return full
            return getattr(responsible, 'username', None)
        except Exception:
            return None

class PropertyWithDocsSerializer(serializers.ModelSerializer):
    direccion = serializers.CharField(source="exact_address", read_only=True)
    owner = serializers.CharField(source='owner.full_name', read_only=True)
    created_by = serializers.SerializerMethodField()
    property_documents = serializers.SerializerMethodField()
    can_marketing_upload_media = serializers.SerializerMethodField()
    can_legal_upload_study = serializers.SerializerMethodField()

    class Meta:
        model = models.Property
        fields = (
            "id",
            "code",
            "direccion",
            "title",
            "owner",
            "is_active",
            "created_at",
            "created_by",
            "can_marketing_upload_media",
            "can_legal_upload_study",
            "property_documents",
        )

    def _docs_map(self, obj):
        """
        Devuelve el dict {DocumentType.name: file_url o None}
        """
        request = self.context.get("request")

        # Base: todos los tipos activos => None
        types = models.DocumentType.objects.filter(is_active=True).order_by("name")
        data = {t.name: None for t in types}

        # Fill: documentos existentes
        for d in obj.documents.select_related("document_type").all():
            if not d.document_type:
                continue
            key = d.document_type.name
            if getattr(d, "file", None):
                url = d.file.url
                data[key] = request.build_absolute_uri(url) if request else url

        return data
    
    def get_created_by(self, obj):
        u = getattr(obj, "created_by", None)
        if not u:
            return None
        # CustomUser hereda AbstractUser, esto existe
        full = u.get_full_name() if hasattr(u, "get_full_name") else ""
        return full.strip() or getattr(u, "username", None) or str(u)

    def get_property_documents(self, obj):
        return self._docs_map(obj)

    def get_can_marketing_upload_media(self, obj):
        # Regla: si existe (con file) Partida_registral o Contrato_de_corretaje => True
        required = {"Partida_registral", "Contrato_de_corretaje"}
        for d in obj.documents.select_related("document_type").all():
            if d.document_type and d.document_type.name in required and getattr(d, "file", None):
                return True
        return False

    def get_can_legal_upload_study(self, obj):
        """
        Habilitación para LEGAL: depende de base docs + usuario con Area LEGAL (si está logueado).
        Si no está autenticado => False.
        """
        base_ok = self.get_can_marketing_upload_media(obj)

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        # Asumiendo que luego renombramos department -> area:
        user_area_code = None
        if getattr(user, "area_id", None) and getattr(user.area, "code", None):
            user_area_code = user.area.code

        return base_ok and user_area_code == "LEGAL"
    
class PropertyDocumentCreateSerializer(serializers.ModelSerializer):
    document_type = serializers.PrimaryKeyRelatedField(
        queryset=models.DocumentType.objects.filter(is_active=True)
    )

    class Meta:
        model = models.PropertyDocument
        fields = ("document_type", "file")

    def validate(self, attrs):
        prop = self.context["property"]
        doc_type = attrs["document_type"]

        # Evitar duplicados por (property, document_type)
        if models.PropertyDocument.objects.filter(property=prop, document_type=doc_type).exists():
            raise serializers.ValidationError({
                "document_type": "Ya existe un documento de este tipo para esta propiedad."
            })

        # file obligatorio
        if not attrs.get("file"):
            raise serializers.ValidationError({"file": "Este campo es requerido."})

        return attrs

    def create(self, validated_data):
        prop = self.context["property"]
        request = self.context["request"]

        # ✅ IMPORTANTE: tu BD exige uploaded_by_id NOT NULL
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Debes estar autenticado para subir documentos.")

        validated_data.setdefault("is_approved", False)

        # Opcional: si tu modelo tiene title/description pero no quieres pedirlos,
        # los puedes autogenerar sin romper nada:
        dt = validated_data["document_type"]
        validated_data.setdefault("title", getattr(dt, "name", "") or "")
        validated_data.setdefault("description", "")

        return models.PropertyDocument.objects.create(
            property=prop,
            uploaded_by=user,   # ✅ CLAVE para tu error
            **validated_data
        )