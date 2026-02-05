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
    
class RequirementSerializer(serializers.ModelSerializer):

    client_phone = serializers.CharField(write_only=True, required=True)
    client_first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    client_last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    client_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    
    agent_phone = serializers.CharField(write_only=True, required=False)

    # Campos de lectura para mostrar detalles en la respuesta (GET)
    contact_id = serializers.IntegerField(source='contact.id', read_only=True)
    contact_name = serializers.SerializerMethodField()
    contact_phone = serializers.CharField(source='contact.phone', read_only=True)
    contact_email = serializers.CharField(source='contact.email', read_only=True)
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Requirement
        fields = [
            'id',

            'client_phone', 'client_first_name', 'client_last_name', 'client_email',
            'agent_phone',
            
            'contact_id', 'contact_name', 'contact_phone', 'contact_email',
            'agent_name',
            
            'property_type', 'property_subtype',
            'budget_min', 'budget_max', 'currency',
            'districts', 'bedrooms', 'bathrooms', 'garage_spaces',
            'notes', 'created_at'
        ]
        extra_kwargs = {
            'districts': {'required': False},
            'currency': {'required': False},
        }

    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.first_name} {obj.contact.last_name}".strip()
        return None

    def get_agent_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def create(self, validated_data):
        c_phone = validated_data.pop('client_phone')
        c_first = validated_data.pop('client_first_name', '')
        c_last = validated_data.pop('client_last_name', '')
        c_email = validated_data.pop('client_email', '')
        a_phone = validated_data.pop('agent_phone', None)
        districts = validated_data.pop('districts', [])

        # REVISAR Lógica automática: Si envían min/max, es un rango (para que funcione el matching)
        if validated_data.get('budget_min') is not None or validated_data.get('budget_max') is not None:
            validated_data['budget_type'] = 'range'

        
        user = self.context['request'].user # hallar agente
        if a_phone:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            clean_phone = ''.join(filter(str.isdigit, str(a_phone)))
            
            agent = User.objects.filter(phone=clean_phone).first() # buscar agente por teléfono (exacto o últimos 9 dígitos)
            if not agent and len(clean_phone) >= 9:
                agent = User.objects.filter(phone__endswith=clean_phone[-9:]).first()
            
            if agent:
                user = agent

        # OPTIMIZACIÓN: Buscar directamente en BD para evitar cargar todos los usuarios en memoria
        contact = models.PropertyOwner.objects.filter(is_active=True, phone=c_phone).first()
        
        if not contact:
            contact = models.PropertyOwner.objects.create(
                first_name=c_first or 'Cliente WhatsApp',
                last_name=c_last or '',
                phone=c_phone,
                email=c_email,
                created_by=user
            )

        requirement = models.Requirement.objects.create( # crear requerimiento
            contact=contact,
            created_by=user,
            **validated_data
        )

        if districts:
            requirement.districts.set(districts)

        return requirement

    def update(self, instance, validated_data):
        # Limpiar campos write_only que no son del modelo para evitar problemas en update
        for field in ['client_phone', 'client_first_name', 'client_last_name', 'client_email', 'agent_phone']:
            validated_data.pop(field, None)
        return super().update(instance, validated_data)