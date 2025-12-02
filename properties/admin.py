from django.contrib import admin
from .models import (
    # Servicios
    WaterServiceType, EnergyServiceType, DrainageServiceType, GasServiceType,
    # Ubicación
    Department, Province, District, Urbanization,
    # Tipos y Catálogos
    DocumentType, PropertyType, PropertySubtype, PropertyStatus, Currency,
    MeasurementUnit, GarageType, ServiceType, FloorType, RoomType, LevelType,
    Profession, Tag,
    # Propiedades
    Property, PropertyOwner, PropertyImage, PropertyVideo, PropertyDocument,
    PropertyFinancialInfo, PropertyRoom, ImageType, VideoType
)


# ===================== ADMIN PARA SERVICIOS =====================
@admin.register(WaterServiceType)
class WaterServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(EnergyServiceType)
class EnergyServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(DrainageServiceType)
class DrainageServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(GasServiceType)
class GasServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


# ===================== ADMIN PARA UBICACIÓN =====================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'is_active')
    list_filter = ('is_active', 'department')
    search_fields = ('name',)
    ordering = ('department', 'name')


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'is_active')
    list_filter = ('is_active', 'province')
    search_fields = ('name',)
    ordering = ('province', 'name')


@admin.register(Urbanization)
class UrbanizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'is_active')
    list_filter = ('is_active', 'district')
    search_fields = ('name',)
    ordering = ('district', 'name')


# ===================== ADMIN PARA CATÁLOGOS =====================
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(PropertySubtype)
class PropertySubtypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'property_type', 'is_active')
    list_filter = ('is_active', 'property_type')
    search_fields = ('name',)


@admin.register(PropertyStatus)
class PropertyStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order',)


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(MeasurementUnit)
class MeasurementUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'symbol')


@admin.register(GarageType)
class GarageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(FloorType)
class FloorTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(LevelType)
class LevelTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)


@admin.register(ImageType)
class ImageTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(VideoType)
class VideoTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


# ===================== ADMIN PARA PROPIEDADES =====================
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image_type', 'image', 'caption', 'order', 'is_primary')


class PropertyVideoInline(admin.TabularInline):
    model = PropertyVideo
    extra = 1
    fields = ('video_type', 'video', 'title', 'description')


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 1
    fields = ('document_type', 'title', 'file')


class PropertyRoomInline(admin.TabularInline):
    model = PropertyRoom
    extra = 1
    fields = ('room_type', 'quantity', 'description')


@admin.register(PropertyOwner)
class PropertyOwnerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'document_number', 'phone', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'gender', 'profession')
    search_fields = ('first_name', 'last_name', 'document_number', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'maternal_last_name', 'gender', 'birth_date', 'photo')
        }),
        ('Documento de Identidad', {
            'fields': ('document_type', 'document_number')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'secondary_phone')
        }),
        ('Profesional', {
            'fields': ('profession', 'company')
        }),
        ('Ubicación', {
            'fields': ('department', 'province', 'district', 'urbanization', 'address_exact', 'address_coordinates')
        }),
        ('Etiquetas y Observaciones', {
            'fields': ('tags', 'observations')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'property_type', 'status', 'price', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'status', 'property_type', 'created_at', 'department')
    search_fields = ('code', 'title', 'owner__first_name', 'owner__last_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PropertyImageInline, PropertyVideoInline, PropertyDocumentInline, PropertyRoomInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('code', 'codigo_unico_propiedad', 'title', 'description')
        }),
        ('Clasificación', {
            'fields': ('property_type', 'property_subtype', 'status')
        }),
        ('Propietario y Responsable', {
            'fields': ('owner', 'responsible')
        }),
        ('Precio y Moneda', {
            'fields': ('price', 'currency', 'maintenance_fee', 'has_maintenance')
        }),
        ('Características Físicas', {
            'fields': ('floors', 'bedrooms', 'bathrooms', 'half_bathrooms', 'garage_spaces', 'garage_type')
        }),
        ('Áreas', {
            'fields': ('land_area', 'land_area_unit', 'built_area', 'built_area_unit', 'front_measure', 'depth_measure')
        }),
        ('Ubicación', {
            'fields': ('real_address', 'exact_address', 'coordinates', 'department', 'province', 'district', 'urbanization')
        }),
        ('Servicios', {
            'fields': ('water_service_type', 'energy_service_type', 'drainage_service_type', 'gas_service_type')
        }),
        ('Estado de Construcción', {
            'fields': ('antiquity_years', 'delivery_date'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image_type', 'caption', 'order', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'image_type', 'uploaded_at')
    search_fields = ('property__code', 'caption')
    ordering = ('property', 'order')


@admin.register(PropertyVideo)
class PropertyVideoAdmin(admin.ModelAdmin):
    list_display = ('property', 'title', 'video_type', 'uploaded_at')
    list_filter = ('video_type', 'uploaded_at')
    search_fields = ('property__code', 'title')
    ordering = ('-uploaded_at',)


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ('property', 'title', 'document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('property__code', 'title')
    ordering = ('-uploaded_at',)


@admin.register(PropertyFinancialInfo)
class PropertyFinancialInfoAdmin(admin.ModelAdmin):
    list_display = ('property', 'expense_type', 'amount', 'updated_at')
    list_filter = ('expense_type', 'updated_at')
    search_fields = ('property__code',)
    ordering = ('-updated_at',)


@admin.register(PropertyRoom)
class PropertyRoomAdmin(admin.ModelAdmin):
    list_display = ('property', 'room_type', 'quantity', 'description')
    list_filter = ('room_type',)
    search_fields = ('property__code', 'description')
    ordering = ('property', 'room_type')
