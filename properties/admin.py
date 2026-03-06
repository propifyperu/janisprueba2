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
    PropertyCondition, OperationType,
    PaymentMethod,
    # Propiedades
    Property, PropertyOwner, PropertyImage, PropertyVideo, PropertyDocument,
    PropertyFinancialInfo, PropertyRoom, ImageType, VideoType,
    AgencyConfig,
    # WhatsApp
    PropertyWhatsAppLink, SocialNetwork, WhatsAppNumber, UTMClick,
    # Agenda
    EventType, Event
)

from .models import Requirement, RequirementMatch
from .models import CanalLead, LeadStatus, Lead
from .models import MatchingWeight, MatchEvent


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
    list_display = ('id','code','name', 'province', 'is_active')
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
    list_display = ('id','code', 'name', 'is_active')
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


@admin.register(PropertyCondition)
class PropertyConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'code', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'name')

 

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


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'code', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order', 'name')


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
    list_display = ('name', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


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
    fields = ('room_type', 'level', 'name', 'width', 'length', 'area', 'floor_type', 'description', 'order')


@admin.register(PropertyOwner)
class PropertyOwnerAdmin(admin.ModelAdmin):
    list_display = ('id','full_name', 'document_type','document_number', 'phone', 'email', 'is_active', 'created_at')
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
    list_display = ('id','ascensor','source','source_url','source_published_at','operation_type','district','district_fk','urbanization','code','condition','availability_status','exact_address','responsible','assigned_agent', 'title', 'property_type', 'status', 'price', 'owner', 'is_active', 'created_at','created_by','wp_post_id','wp_slug','wp_last_sync','is_draft','is_ready_for_sale')
    list_filter = ('is_active', 'status', 'property_type', 'created_at', 'department', 'unit_location')
    search_fields = ('code', 'title', 'owner__first_name', 'owner__last_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'code', 'codigo_unico_propiedad')
    inlines = [PropertyImageInline, PropertyVideoInline, PropertyDocumentInline, PropertyRoomInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('code', 'codigo_unico_propiedad', 'title', 'description')
        }),
        ('Clasificación', {
            'fields': ('property_type', 'property_subtype', 'condition', 'operation_type', 'status','availability_status')
        }),
        ('Propietario y Responsable', {
            'fields': ('owner', 'responsible', 'created_by')
        }),
        ('Precio y Moneda', {
            'fields': ('price', 'currency', 'forma_de_pago', 'maintenance_fee', 'has_maintenance')
        }),
        ('Características Físicas', {
            'fields': ('floors', 'bedrooms', 'bathrooms', 'half_bathrooms', 'garage_spaces', 'garage_type')
        }),
        ('Áreas', {
            'fields': ('land_area', 'land_area_unit', 'built_area', 'built_area_unit', 'front_measure', 'depth_measure')
        }),
        ('Ubicación', {
            'fields': ('real_address', 'exact_address', 'coordinates', 'department', 'province', 'district', 'urbanization', 'unit_location')
        }),
        ('Servicios', {
            'fields': ('water_service', 'energy_service', 'drainage_service', 'gas_service')
        }),
        ('Estado de Construcción', {
            'fields': ('antiquity_years', 'delivery_date'),
            'classes': ('collapse',)
        }),
        ('Estado y Auditoría', {
            'fields': ('is_active', 'is_ready_for_sale', 'assigned_agent', 'created_at', 'updated_at','is_draft'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)
    
    def get_readonly_fields(self, request, obj=None):
        """Make created_by readonly"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.append('created_by')
        return readonly


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('id','property', 'order', 'is_primary', 'uploaded_at','wp_media_id','wp_source_url','wp_last_sync')
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
    list_display = ('property', 'title', 'file','document_type', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('property__code', 'title')
    ordering = ('-uploaded_at',)


@admin.register(PropertyFinancialInfo)
class PropertyFinancialInfoAdmin(admin.ModelAdmin):
    list_display = ('property', 'negotiation_status', 'final_commission_percentage', 'updated_at')
    list_filter = ('negotiation_status', 'updated_at')
    search_fields = ('property__code',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)


@admin.register(PropertyRoom)
class PropertyRoomAdmin(admin.ModelAdmin):
    list_display = ('property', 'room_type', 'level', 'name', 'area')
    list_filter = ('room_type', 'level', 'floor_type')
    search_fields = ('property__code', 'name', 'description')
    ordering = ('property', 'level', 'order')


# ===================== ADMIN PARA WHATSAPP =====================
@admin.register(PropertyWhatsAppLink)
class PropertyWhatsAppLinkAdmin(admin.ModelAdmin):
    list_display = ('property', 'link_name', 'social_network', 'unique_identifier', 'is_active', 'created_at')
    list_filter = ('social_network', 'is_active', 'created_at')
    search_fields = ('property__code', 'link_name', 'unique_identifier')
    readonly_fields = ('unique_identifier', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('property', 'link_name', 'social_network', 'whatsapp_phone_id', 'is_active')
        }),
        ('Tracking UTM', {
            'fields': ('utm_source', 'utm_medium', 'utm_campaign', 'utm_content'),
            'classes': ('collapse',)
        }),
        ('Identificador', {
            'fields': ('unique_identifier',),
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "contact",
        "operation_type",
        "property_type",
        "currency",
        "source_group",
        "source_date",
        "is_active",
        "created_at",
        "summary_json",
    )

    list_filter = (
        "is_active",
        "operation_type",
        "property_type",
        "currency",
        "payment_method",
        "source_group",
    )

    search_fields = (
        "id",
        "contact__first_name",
        "contact__last_name",
        "contact__maternal_last_name",
        "notes_message_ws",
        "notes",
    )

    ordering = ("-source_date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "contact",
            "operation_type",
            "property_type",
            "property_subtype",
            "currency",
            "payment_method",
            "property_status",
        ).prefetch_related("districts")

@admin.register(RequirementMatch)
class RequirementMatchAdmin(admin.ModelAdmin):
    list_display = ("id", "requirement", "property", "score", "computed_at")
    list_filter = ("computed_at",)
    search_fields = ("requirement__id", "property__code", "property__title")
    autocomplete_fields = ("requirement", "property")

@admin.register(SocialNetwork)
class SocialNetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)
    ordering = ('name',)



# Nuevo admin para WhatsAppNumber
@admin.register(WhatsAppNumber)
class WhatsAppNumberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "number", "is_active", "created_at")
    search_fields = ("display_name", "number")
    list_filter = ("is_active",)
    ordering = ("display_name",)


# Admin para UTMClick
@admin.register(UTMClick)
class UTMClickAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_id', 'whatsapp_link', 'utm_source', 'utm_medium',
        'utm_campaign', 'ip_address', 'created_at'
    )
    list_filter = ('utm_source', 'utm_medium', 'utm_campaign', 'created_at')
    search_fields = ('tracking_id', 'whatsapp_link__link_name', 'ip_address')
    date_hierarchy = 'created_at'


# ===================== ADMIN PARA AGENDA Y EVENTOS =====================
@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('code', 'titulo', 'event_type', 'fecha_evento','assigned_agent', 'hora_inicio', 'hora_fin', 'created_by', 'created_at')
    list_filter = ('event_type', 'fecha_evento', 'is_active', 'created_at')
    search_fields = ('code', 'titulo', 'interesado', 'property__code')
    readonly_fields = ('code', 'created_at', 'updated_at')
    fieldsets = (
        ('Información del Evento', {
            'fields': ('code', 'event_type', 'titulo')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha_evento', 'hora_inicio', 'hora_fin')
        }),
        ('Detalles', {
            'fields': ('interesado', 'property', 'detalle')
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-fecha_evento', '-hora_inicio')
    date_hierarchy = 'fecha_evento'


# ===================== ADMIN PARA MATCHING =====================
@admin.register(MatchingWeight)
class MatchingWeightAdmin(admin.ModelAdmin):
    list_display = ('key', 'weight', 'updated_at')
    search_fields = ('key',)
    ordering = ('key',)


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('requirement', 'property', 'created_at')
    search_fields = ('requirement__id', 'property__code')
    ordering = ('-created_at',)


@admin.register(AgencyConfig)
class AgencyConfigAdmin(admin.ModelAdmin):
    list_display = ('nombre_comercial', 'ruc', 'correo_electronico')

@admin.register(CanalLead)
class CanalLeadAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(LeadStatus)
class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "email",
        "lead_status",
        "canal_lead",
        "date_entry",
        "created_by",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "lead_status",
        "canal_lead",
        "date_entry",
        "created_at",
    )
    search_fields = (
        "full_name",
        "phone",
        "email",
        "notes",
        "id_chatwoot",
    )
    readonly_fields = ("created_by", "created_at", "updated_at")
    filter_horizontal = ("operation_types", "properties", "assigned_to")
    ordering = ("-created_at",)

    fieldsets = (
        ("Datos básicos", {
            "fields": ("full_name", "phone", "email")
        }),
        ("Relaciones", {
            "fields": ("operation_types", "properties", "assigned_to", "lead_status", "canal_lead")
        }),
        ("Datos comerciales", {
            "fields": ("notes", "date_entry", "id_chatwoot", "date_last_message", "user_last_message")
        }),
        ("Auditoría", {
            "fields": ("created_by", "created_at", "updated_at", "is_active"),
            "classes": ("collapse",)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)