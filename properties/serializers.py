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

    class Meta:
        model = models.PropertyDocument
        fields = ('id', 'title', 'description', 'file_url', 'is_approved')

    def get_file_url(self, obj):
        request = self.context.get('request') if self.context else None
        if obj and getattr(obj, 'file', None) and request:
            return request.build_absolute_uri(obj.file.url)
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
