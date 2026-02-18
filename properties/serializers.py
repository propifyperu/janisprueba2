# serializers.py
from rest_framework import serializers
from . import models

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
    document_type = serializers.CharField(source="document_type.name", read_only=True)
    document_type_id = serializers.IntegerField(source="document_type.id", read_only=True)
    document_type_code = serializers.CharField(source="document_type.code", read_only=True)

    class Meta:
        model = models.PropertyDocument
        fields = (
            "id",
            "title",
            "description",
            "document_type",
            "document_type_id",
            "document_type_code",
            "file_url",
            "is_approved",
            # ✅ NUEVOS
            "reference_number",
            "valid_from",
            "valid_to",
        )

    def get_file_url(self, obj):
        request = self.context.get("request") if self.context else None
        if obj and getattr(obj, "file", None):
            url = obj.file.url
            return request.build_absolute_uri(url) if request else url
        return None

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
        request = self.context.get("request")

        types = models.DocumentType.objects.filter(is_active=True).order_by("name")
        data = {t.name: {"file_url": None, "reference_number": None, "valid_from": None, "valid_to": None} for t in types}

        for d in obj.documents.select_related("document_type").all():
            if not d.document_type:
                continue
            key = d.document_type.name

            file_url = None
            if getattr(d, "file", None):
                url = d.file.url
                file_url = request.build_absolute_uri(url) if request else url

            data[key] = {
                "file_url": file_url,
                "reference_number": getattr(d, "reference_number", None),
                "valid_from": getattr(d, "valid_from", None),
                "valid_to": getattr(d, "valid_to", None),
            }

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
    
    def _has_doc(self, obj, codes: set[str]) -> bool:
        # Usa la relación reverse: documents (related_name='documents')
        return obj.documents.filter(
            document_type__code__in=codes,
            file__isnull=False,
        ).exists()

    def get_can_legal_upload_study(self, obj):
        return bool(getattr(obj, "has_legal_base", False))

    def get_can_marketing_upload_media(self, obj):
        return bool(getattr(obj, "has_study", False))
    
class PropertyDocumentCreateSerializer(serializers.ModelSerializer):
    ALLOW_METADATA_ONLY_CODES = {"110", "107"}

    document_type = serializers.PrimaryKeyRelatedField(
        queryset=models.DocumentType.objects.filter(is_active=True)
    )

    class Meta:
        model = models.PropertyDocument
        fields = ("document_type", "file", "reference_number", "valid_from", "valid_to")

    def validate(self, attrs):
        prop = self.context["property"]
        doc_type = attrs["document_type"]

        if models.PropertyDocument.objects.filter(property=prop, document_type=doc_type).exists():
            raise serializers.ValidationError({
                "document_type": "Ya existe un documento de este tipo para esta propiedad."
            })

        # ✅ file requerido SOLO si NO es metadata-only
        code = (getattr(doc_type, "code", "") or "").strip().lower()
        if not attrs.get("file") and code not in self.ALLOW_METADATA_ONLY_CODES:
            raise serializers.ValidationError({"file": "Este campo es requerido."})

        vf = attrs.get("valid_from")
        vt = attrs.get("valid_to")
        if vf and vt and vt < vf:
            raise serializers.ValidationError("valid_to no puede ser menor que valid_from.")

        return attrs

    def create(self, validated_data):
        prop = self.context["property"]
        request = self.context["request"]

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Debes estar autenticado para subir documentos.")

        validated_data.setdefault("is_approved", False)

        dt = validated_data["document_type"]
        validated_data.setdefault("title", getattr(dt, "name", "") or "")
        validated_data.setdefault("description", "")

        return models.PropertyDocument.objects.create(
            property=prop,
            uploaded_by=user,
            **validated_data
        )

class RequirementSerializer(serializers.ModelSerializer):

    client_phone = serializers.CharField(write_only=True, required=False)
    client_first_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    client_last_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    client_email = serializers.EmailField(write_only=True, required=False, allow_blank=True, allow_null=True)
    
    agent_phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    # campos de lectura para mostrar detalles en la respuesta (GET)
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
            
            'property_type', 'property_subtype', 'status', 'payment_method',
            'budget_type', 'budget_approx', 'budget_min', 'budget_max', 'currency',
            
            'department', 'province', 'district', 'districts',
            
            'area_type', 'land_area_approx', 'land_area_min', 'land_area_max',
            'frontera_type', 'frontera_approx', 'frontera_min', 'frontera_max',
            
            'bedrooms', 'bathrooms', 'half_bathrooms', 'garage_spaces',
            'floors', 'number_of_floors', 'ascensor',
            'preferred_floors', 'zonificaciones',
            
            'notes', 'created_at'
        ]
        extra_kwargs = {
            'districts': {'required': False},
            'currency': {'required': False},
        }

    def to_internal_value(self, data):
        # permitir que el agente externo envíe null y tratarlos como lista vacía
        if isinstance(data, dict):
            data = data.copy()
            for field in ['districts', 'preferred_floors', 'zonificaciones']:
                if field in data and data[field] is None:
                    data[field] = []
        return super().to_internal_value(data)

    def validate(self, data):
        # lógica de consistencia: si envían min/max, es un rango. si es approx, limpiamos min/max
        if data.get('budget_min') is not None or data.get('budget_max') is not None:
            data['budget_type'] = 'range'
            data['budget_approx'] = None
        elif data.get('budget_approx') is not None:
            data['budget_type'] = 'approx'
            data['budget_min'] = None
            data['budget_max'] = None

        # consistencia area
        if data.get('land_area_min') is not None or data.get('land_area_max') is not None:
            data['area_type'] = 'range'
            data['land_area_approx'] = None
        elif data.get('land_area_approx') is not None:
            data['area_type'] = 'approx'
            data['land_area_min'] = None
            data['land_area_max'] = None

        # consistencia frontera
        if data.get('frontera_min') is not None or data.get('frontera_max') is not None:
            data['frontera_type'] = 'range'
            data['frontera_approx'] = None
        elif data.get('frontera_approx') is not None:
            data['frontera_type'] = 'approx'
            data['frontera_min'] = None
            data['frontera_max'] = None
        return data

    def get_contact_name(self, obj):
        if obj.contact:
            return f"{obj.contact.first_name} {obj.contact.last_name}".strip()
        return None

    def get_agent_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def create(self, validated_data):
        c_phone = validated_data.pop('client_phone', None)
        
        if not c_phone:
            c_phone = self.initial_data.get('contact_phone')

        c_first = validated_data.pop('client_first_name', '')
        c_last = validated_data.pop('client_last_name', '')
        c_email = validated_data.pop('client_email', '')
        a_phone = validated_data.pop('agent_phone', None)
        districts = validated_data.pop('districts', [])
        preferred_floors = validated_data.pop('preferred_floors', [])
        zonificaciones = validated_data.pop('zonificaciones', [])

        
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
        if preferred_floors:
            requirement.preferred_floors.set(preferred_floors)
        if zonificaciones:
            requirement.zonificaciones.set(zonificaciones)

        return requirement

    def update(self, instance, validated_data):
        # Limpiar campos write_only que no son del modelo para evitar problemas en update
        for field in ['client_phone', 'client_first_name', 'client_last_name', 'client_email', 'agent_phone']:
            validated_data.pop(field, None)
        return super().update(instance, validated_data)

class PropertyDocumentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PropertyDocument
        fields = ("file", "reference_number", "valid_from", "valid_to")

    def validate(self, attrs):
        vf = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        vt = attrs.get("valid_to", getattr(self.instance, "valid_to", None))
        if vf and vt and vt < vf:
            raise serializers.ValidationError("valid_to no puede ser menor que valid_from.")
        return attrs

    def update(self, instance, validated_data):
        request = self.context["request"]

        # si mandan file, reemplaza y resetea aprobación
        new_file = validated_data.get("file", None)
        if new_file:
            instance.file = new_file
            instance.is_approved = False

        # metadata (si viene)
        for f in ("reference_number", "valid_from", "valid_to"):
            if f in validated_data:
                setattr(instance, f, validated_data[f])

        if getattr(request, "user", None) and request.user.is_authenticated:
            instance.uploaded_by = request.user

        instance.save()
        return instance

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DocumentType
        fields = ("id", "code", "name", "description", "is_active")