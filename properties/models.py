from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import mimetypes
import random
import string
from encrypted_model_fields.fields import EncryptedCharField, EncryptedEmailField, EncryptedTextField
from cryptography.fernet import Fernet
def _normalize_title_case(value: str | None) -> str | None:
    """Return value in title case with single spaces."""
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    if not stripped:
        return ''

    parts = stripped.split()
    return ' '.join(part.capitalize() for part in parts)


class TitleCaseMixin:
    """Mixin to normalize configured string fields before saving."""

    title_case_fields: tuple[str, ...] = ()

    def _apply_title_case(self):
        for field_name in self.title_case_fields:
            if hasattr(self, field_name):
                current_value = getattr(self, field_name)
                setattr(self, field_name, _normalize_title_case(current_value))



# =============================================================================
# MODELOS PARA SERVICIOS PÚBLICOS (UNO POR CADA TIPO)
# =============================================================================

class WaterServiceType(models.Model):
    """Tipos de servicio de agua potable"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'water_service_types'
        verbose_name = "Tipo de Servicio de Agua"
        verbose_name_plural = "Tipos de Servicio de Agua"
        ordering = ['name']
        
    def __str__(self):
        return self.name


class EnergyServiceType(models.Model):
    """Tipos de servicio de energía eléctrica"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'energy_service_types'
        verbose_name = "Tipo de Servicio de Energía"
        verbose_name_plural = "Tipos de Servicio de Energía"
        ordering = ['name']
        
    def __str__(self):
        return self.name


class DrainageServiceType(models.Model):
    """Tipos de servicio de drenaje"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'drainage_service_types'
        verbose_name = "Tipo de Servicio de Drenaje"
        verbose_name_plural = "Tipos de Servicio de Drenaje"
        ordering = ['name']
        
    def __str__(self):
        return self.name


class GasServiceType(models.Model):
    """Tipos de servicio de gas"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gas_service_types'
        verbose_name = "Tipo de Servicio de Gas"
        verbose_name_plural = "Tipos de Servicio de Gas"
        ordering = ['name']
        
    def __str__(self):
        return self.name





# =============================================================================
# MODELOS DE UBICACIÓN (AGREGAR AL PRINCIPIO)
# =============================================================================

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Province(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='provinces')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"
        ordering = ['name']
        unique_together = ['department', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.department.name}"

class District(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    province = models.ForeignKey('Province', on_delete=models.CASCADE, related_name='districts')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Distrito"
        verbose_name_plural = "Distritos"
        ordering = ['name']
        unique_together = ['province', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.province.name}"

class Urbanization(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    district = models.ForeignKey('District', on_delete=models.CASCADE, related_name='urbanizations')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Urbanización"
        verbose_name_plural = "Urbanizaciones"
        ordering = ['name']
        unique_together = ['district', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.district.name}"

# =============================================================================
# MODELOS BÁSICOS DE CONFIGURACIÓN
# =============================================================================

class DocumentType(models.Model):
    code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'document_types'
        
    def __str__(self):
        return self.name

class PropertyType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'property_types'
        
    def __str__(self):
        return self.name

class PropertySubtype(models.Model):
    property_type = models.ForeignKey('PropertyType', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'property_subtypes'
        
    def __str__(self):
        return f"{self.property_type.name} - {self.name}"

class PropertyStatus(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'property_statuses'
        ordering = ['order']
        
    def __str__(self):
        return self.name

class PropertyCondition(models.Model):
   
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_conditions'
        ordering = ['order', 'name']
        verbose_name = "Condición de Propiedad"
        verbose_name_plural = "Condiciones de Propiedad"
    
    def __str__(self):
        return self.name

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'currencies'
        
    def __str__(self):
      return self.name  # ← SOLO EL NOMBRE

class MeasurementUnit(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'measurement_units'
        
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class GarageType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'garage_types'
        
    def __str__(self):
        return self.name

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'service_types'
        
    def __str__(self):
        return self.name

class FloorType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'floor_types'
        
    def __str__(self):
        return self.name


class FloorOption(models.Model):
    """Opciones de piso para preferencias en requerimientos (Sótano, 1er piso, ...)."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'floor_options'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ZoningOption(models.Model):
    """Opciones de zonificación para requisitos (Urbano, Rural, Industrial, Comercial)."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'zoning_options'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class RoomType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'room_types'
        
    def __str__(self):
        return self.name

class LevelType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'level_types'
        
    def __str__(self):
        return self.name

class Profession(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'professions'
        
    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#007bff')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tags'
        
    def __str__(self):
        return self.name

class ImageType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'image_types'
        
    def __str__(self):
        return self.name

class VideoType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'video_types'
        
    def __str__(self):
        return self.name


class NegotiationStatus(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'negotiation_statuses'
        ordering = ['order', 'name']
        verbose_name = 'Estado de negociación'
        verbose_name_plural = 'Estados de negociación'

    def __str__(self):
        return self.name

# =============================================================================
# MODELO DEL PROPIETARIO
# =============================================================================

class PropertyOwner(TitleCaseMixin, models.Model):
    title_case_fields = (
        'first_name',
        'last_name',
        'maternal_last_name',
        'company',
    )
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    
    # Información personal
    first_name = EncryptedCharField(max_length=256, blank=True, null=True)
    last_name = EncryptedCharField(max_length=256, blank=True, null=True)
    maternal_last_name = EncryptedCharField(max_length=256, blank=True, null=True)
    
    # Documento de identidad
    document_type = models.ForeignKey('DocumentType', on_delete=models.PROTECT, null=True, blank=True)
    document_number = models.CharField(max_length=50, verbose_name="Número de documento", blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Género", blank=True, null=True)
    phone = EncryptedCharField(max_length=256, blank=True, null=True)
    secondary_phone = EncryptedCharField(max_length=256, blank=True, null=True)
    email = EncryptedEmailField(max_length=255, blank=True, null=True)
    profession = models.ForeignKey('Profession', on_delete=models.SET_NULL, null=True, blank=True)
    photo = models.ImageField(upload_to='owners/photos/', null=True, blank=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    # Dirección del contacto
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Departamento")
    province = models.ForeignKey('Province', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Provincia")
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Distrito")
    urbanization = models.ForeignKey('Urbanization', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Urbanización")
    address_exact = models.TextField(blank=True, null=True, verbose_name="Dirección Exacta")
    address_coordinates = models.CharField(max_length=512, blank=True, null=True, verbose_name="Coordenadas")
    
    # Etiquetas para búsqueda rápida
    tags = models.ManyToManyField('Tag', blank=True)
    
    # Auditoría
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'property_owners'
        
    def __str__(self):
        parts = []
        if self.first_name:
            parts.append(str(self.first_name))
        if self.last_name:
            parts.append(str(self.last_name))
        return " ".join(parts) if parts else "Sin nombre"

    @property
    def full_name(self):
        """Retorna el nombre completo del contacto, manejando campos encriptados."""
        parts = []
        if self.first_name:
            parts.append(str(self.first_name))
        if self.last_name:
            parts.append(str(self.last_name))
        if self.maternal_last_name:
            parts.append(str(self.maternal_last_name))
        return " ".join(parts) if parts else "Sin nombre"
    
    @property
    def display_phone(self):
        """Retorna el teléfono como string para mostrar en templates."""
        return str(self.phone) if self.phone else ""

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

# =============================================================================
# MODELO PRINCIPAL DE PROPIEDAD
# =============================================================================

AVAILABILITY_STATUS_CHOICES = [
    ("available", "Disponible"),
    ("reserved", "Reservada"),
    ("sold", "Vendida"),
    ("unavailable", "No disponible"),
    ("paused", "Pausada"),
]

REQUIRED_DOC_CODES = [
    "estudio_del_titulo",
    "contrato_de_reserva",
    "contrato_de_corretaje",
    "contrato_compra_venta",
    "contrato_arras",
    "autovaluo",
    "dni",
    "titulo_de_dominio",
    "vigencia_de_poder",
    "partida_registral",
    "otros",
]

MARKETING_UNLOCK_DOCS = {"partida_registral", "contrato_de_corretaje"}

LEGAL_ONLY_DOCS = {"estudio_del_titulo"}

class Property(TitleCaseMixin, models.Model):
    title_case_fields = (
        'title',
        'department',
        'province',
        'district',
        'urbanization',
    )
    # Información básica
    code = models.CharField(max_length=20, unique=True, blank=True, default='')
    codigo_unico_propiedad = models.CharField(max_length=11, unique=True, blank=True, null=True, verbose_name="Código Único Propiedad")
    title = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    
    # Relaciones principales
    owner = models.ForeignKey('PropertyOwner', on_delete=models.CASCADE, related_name='properties', blank=True, null=True)
    property_type = models.ForeignKey('PropertyType', on_delete=models.PROTECT, blank=True, null=True)
    property_subtype = models.ForeignKey('PropertySubtype', on_delete=models.PROTECT, blank=True, null=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS_CHOICES, default="available", db_index=True, verbose_name="Estado comercial")
    status = models.ForeignKey('PropertyStatus', on_delete=models.PROTECT, blank=True, null=True)
    condition = models.ForeignKey('PropertyCondition', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Condición Física")
    operation_type = models.ForeignKey('OperationType', on_delete=models.PROTECT, blank=True, null=True, verbose_name="Tipo de Operación")
    responsible = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_properties',
        verbose_name="Responsable"
    )
    
    antiquity_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Años de antigüedad",
        help_text="Aplica únicamente para propiedades con estado de antigüedad"
    )
    delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha estimada de entrega",
        help_text="Aplica únicamente para propiedades en construcción"
    )
    
    # Precio y moneda
    price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, default=0)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, blank=True, null=True)
    # Forma de pago (nuevo campo FK a PaymentMethod)
    forma_de_pago = models.ForeignKey('PaymentMethod', on_delete=models.PROTECT, blank=True, null=True, verbose_name="Forma de Pago")
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    has_maintenance = models.BooleanField(default=False)
    
    # Características físicas
    floors = models.PositiveIntegerField(default=1, blank=True, null=True)
    bedrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    half_bathrooms = models.PositiveIntegerField(default=0, blank=True, null=True)
    
    # Garaje
    garage_spaces = models.PositiveIntegerField(default=0, blank=True, null=True)
    garage_type = models.ForeignKey('GarageType', on_delete=models.SET_NULL, null=True, blank=True)
    # Costo de estacionamiento: puede estar incluido en el precio o ser un costo adicional
    parking_cost_included = models.BooleanField(default=False, verbose_name='Estacionamiento incluido en precio')
    parking_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Costo Estacionamiento', help_text='Costo adicional por estacionamiento si no está incluido en el precio')
    
    # Áreas
    land_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    land_area_unit = models.ForeignKey('MeasurementUnit', on_delete=models.PROTECT, related_name='land_properties', null=True, blank=True)
    built_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    built_area_unit = models.ForeignKey('MeasurementUnit', on_delete=models.PROTECT, related_name='built_properties', null=True, blank=True)
    front_measure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    depth_measure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Ubicación
    real_address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Dirección Real (de documentos)",
        help_text="Dirección exacta que aparece en documentos legales"
    )
    exact_address = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        verbose_name="Dirección Exacta (para mapa)"
    )
    coordinates = models.CharField(max_length=512, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    urbanization = models.CharField(max_length=100, blank=True, null=True)
    
    # Servicios
    water_service = models.ForeignKey('WaterServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='water_properties', verbose_name="Servicio de Agua")
    energy_service = models.ForeignKey('EnergyServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='energy_properties', verbose_name="Servicio de Energía")
    drainage_service = models.ForeignKey('DrainageServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='drainage_properties', verbose_name="Servicio de Drenaje")
    gas_service = models.ForeignKey('GasServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='gas_properties', verbose_name="Servicio de Gas")
    
    # Información adicional
    amenities = models.TextField(blank=True, null=True)
    zoning = models.CharField(max_length=100, blank=True, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    # Auditoría y workflow
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, blank=True, null=True)
    assigned_agent = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    # Flag explícito para marcar un registro como Borrador (editable, no publicado)
    is_draft = models.BooleanField(default=False)
    is_ready_for_sale = models.BooleanField(default=False)
    # Ubicación dentro de un edificio (solo aplica cuando la propiedad es un departamento)
    UNIT_LOCATION_CHOICES = [
        ('basement', 'Sótano'),
        ('1', '1er piso'),
        ('2', '2do piso'),
        ('3', '3er piso'),
        ('4', '4to piso'),
        ('5', '5to piso'),
        ('6', '6to piso'),
        ('7', '7mo piso'),
        ('8', '8vo piso'),
        ('9', '9no piso'),
        ('10', '10mo piso'),
    ]
    unit_location = models.CharField(max_length=20, choices=UNIT_LOCATION_CHOICES, blank=True, null=True, verbose_name='Ubicación (nivel)')
    # Proyecto: agrupa propiedades bajo un mismo nombre de proyecto
    is_project = models.BooleanField(default=False, verbose_name='Proyecto')
    project_name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Nombre de proyecto', help_text='Nombre para agrupar propiedades cuando se trate de un proyecto')
    # Ascensor: almacena 'yes'/'no' cuando aplica (departamentos). Nullable para compatibilidad.
    ASCENSOR_CHOICES = (
        ('yes', 'Sí'),
        ('no', 'No'),
    )
    ascensor = models.CharField(max_length=3, choices=ASCENSOR_CHOICES, null=True, blank=True, verbose_name='Ascensor')
    
    class Meta:
        db_table = 'properties'
        verbose_name_plural = 'Properties'
        
    def __str__(self):
        return f"{self.code} - {self.title}"

    def get_documents_map(self):
        """
        Retorna dict: {doc_code: file_url_or_none}
        Prioriza 1 archivo por tipo (el más reciente).
        """
        # trae docs reales que existan
        qs = self.documents.select_related("document_type").order_by("-uploaded_at")
        latest_by_code = {}
        for d in qs:
            code = getattr(d.document_type, "code", None)
            if not code:
                continue
            if code not in latest_by_code:
                latest_by_code[code] = d

        # arma mapa completo (incluye los que faltan)
        result = {}
        for code in REQUIRED_DOC_CODES:
            doc = latest_by_code.get(code)
            if doc and doc.file:
                try:
                    result[code] = doc.file.url
                except Exception:
                    # por si no hay storage configurado con url()
                    result[code] = str(doc.file)
            else:
                result[code] = None
        return result

    def has_any_docs(self, codes: set[str]) -> bool:
        docs_map = self.get_documents_map()
        return any(docs_map.get(c) for c in codes)

    @property
    def marketing_enabled(self) -> bool:
        return self.has_any_docs(MARKETING_UNLOCK_DOCS)

    @property
    def legal_enabled(self) -> bool:
        # regla: se habilita legal si marketing ya está habilitado
        return self.marketing_enabled
    
    @property
    def department_name(self):
        """Devuelve el nombre del departamento si el campo es numérico (ID), sino el valor original."""
        val = self.department
        if val and val.isdigit():
            # Evitar error si Department no está definido o no se encuentra
            try:
                obj = Department.objects.filter(id=int(val)).first()
                return obj.name if obj else val
            except Exception:
                pass
        return val or ''

    @property
    def province_name(self):
        """Devuelve el nombre de la provincia si el campo es numérico (ID)."""
        val = self.province
        if val and val.isdigit():
            try:
                obj = Province.objects.filter(id=int(val)).first()
                return obj.name if obj else val
            except Exception:
                pass
        return val or ''

    @property
    def district_name(self):
        """Devuelve el nombre del distrito si el campo es numérico (ID)."""
        val = self.district
        if val and val.isdigit():
            try:
                obj = District.objects.filter(id=int(val)).first()
                return obj.name if obj else val
            except Exception:
                pass
        return val or ''

    @property
    def urbanization_name(self):
        """Devuelve el nombre de la urbanización si el campo es numérico (ID)."""
        val = self.urbanization
        if val and val.isdigit():
            try:
                obj = Urbanization.objects.filter(id=int(val)).first()
                return obj.name if obj else val
            except Exception:
                pass
        return val or ''

    def save(self, *args, **kwargs):
        self._apply_title_case()
        # Generar código único si no existe
        if not self.code:
            last_property = Property.objects.order_by('-id').first()
            last_id = last_property.id if last_property else 0
            self.code = f"PROP{last_id + 1:06d}"
        # Generar código único aleatorio si no existe
        if not self.codigo_unico_propiedad:
            while True:
                letras = ''.join(random.choices(string.ascii_uppercase, k=2))
                numeros = ''.join(random.choices(string.digits, k=9))
                nuevo_codigo = f"{letras}{numeros}"
                if not Property.objects.filter(codigo_unico_propiedad=nuevo_codigo).exists():
                    self.codigo_unico_propiedad = nuevo_codigo
                    break
        super().save(*args, **kwargs)


# =============================================================================
# MODELOS PARA MEDIOS Y DOCUMENTOS
# =============================================================================

class PropertyImage(TitleCaseMixin, models.Model):
    title_case_fields = ('caption',)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/images/')
    # Campo para almacenar el blob directamente en la tabla (opcional)
    image_blob = models.BinaryField(null=True, blank=True)
    image_content_type = models.CharField(max_length=100, blank=True, null=True)
    image_type = models.ForeignKey('ImageType', on_delete=models.PROTECT, null=True, blank=True)
    image_ambiente = models.ForeignKey('RoomType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ambiente de la imagen")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    sensible = models.BooleanField(default=False, verbose_name='Sensible')
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_images'
        ordering = ['order']
        
    def __str__(self):
        return f"Imagen {self.id} - {self.property.code}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        return super().save(*args, **kwargs)


# =============================================================================
# MODELOS PARA EL MOTOR DE MATCHING
# =============================================================================
class MatchingWeight(models.Model):
    """Pesos configurables para cada criterio de matching.

    Se pueden ajustar manualmente desde el admin y son usados por
    `properties.matching` para ponderar la puntuación.
    """
    key = models.CharField(max_length=100, unique=True, help_text='Identificador del criterio, ej: property_type, district, price')
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matching_weights'
        verbose_name = 'Peso de Matching'
        verbose_name_plural = 'Pesos de Matching'

    def __str__(self):
        return f"{self.key}: {self.weight}"


class MatchEvent(models.Model):
    """Registro de coincidencias consideradas positivas (ej. visita agendada).

    Se usa para el aprendizaje simple: cuando un requerimiento vinculado a
    un contacto programa una visita a una propiedad, se crea un MatchEvent
    que luego permite ajustar pesos.
    """
    requirement = models.ForeignKey('Requirement', on_delete=models.CASCADE, related_name='match_events')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='match_events')
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True, help_text='Datos opcionales sobre el evento')

    class Meta:
        db_table = 'match_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"MatchEvent RQ:{self.requirement_id} PROP:{self.property_id} @ {self.created_at.strftime('%Y-%m-%d')}"

class PropertyVideo(TitleCaseMixin, models.Model):
    title_case_fields = ('title',)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='videos')
    video_type = models.ForeignKey('VideoType', on_delete=models.PROTECT, null=True, blank=True)
    video = models.FileField(upload_to='properties/videos/')
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_videos'
        
    def __str__(self):
        return f"Video {self.id} - {self.property.code}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

class PropertyDocument(TitleCaseMixin, models.Model):
    title_case_fields = ('title',)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey('DocumentType', on_delete=models.PROTECT, null=True, blank=True)
    file = models.FileField(upload_to='properties/documents/')
    title = EncryptedCharField(max_length=255)
    description = EncryptedTextField(blank=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'property_documents'
        constraints = [
            models.UniqueConstraint(
                fields=['property', 'document_type'],
                name='uq_property_documents_property_document_type'
            )
        ]
        indexes = [
            models.Index(fields=['property', 'document_type'], name='idx_propdoc_prop_doctype'),
        ]
        
    def __str__(self):
        return f"Documento {self.id} - {self.property.code}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

# =============================================================================
# MODELO PARA TIPOS DE CONTRATO (USADO EN PropertyFinancialInfo)
# =============================================================================
class ContractType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contract_types'
        ordering = ['name']
        verbose_name = 'Tipo de Contrato'
        verbose_name_plural = 'Tipos de Contrato'

    def __str__(self):
        return self.name

# =============================================================================
# MODELO PARA INFORMACIÓN FINANCIERA
# =============================================================================

class PropertyFinancialInfo(models.Model):
    property = models.OneToOneField('Property', on_delete=models.CASCADE, related_name='financial_info')
    initial_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    negotiation_status = models.ForeignKey('NegotiationStatus', on_delete=models.SET_NULL, null=True, blank=True, related_name='financial_records')
    # Tipo de contrato: FK a ContractType (exclusivo / semi exclusivo / no exclusivo)
    contract_type = models.ForeignKey('ContractType', on_delete=models.PROTECT, null=True, blank=True, related_name='financial_records', verbose_name='Tipo de Contrato')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'property_financial_info'
        verbose_name = 'Información financiera de la propiedad'
        verbose_name_plural = 'Información financiera de propiedades'

    def __str__(self):
        return f"Finanzas {self.property.code}" if getattr(self, 'property_id', None) else 'Finanzas sin propiedad'


# =============================================================================
# MODELO PARA FORMAS DE PAGO
# =============================================================================
class PaymentMethod(TitleCaseMixin, models.Model):
    title_case_fields = ('name',)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_methods'
        ordering = ('order', 'name')

    def __str__(self):
        return self.name


# =============================================================================
# MODELO PARA AMBIENTES
# =============================================================================

class PropertyRoom(TitleCaseMixin, models.Model):
    title_case_fields = ('name',)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='rooms')
    level = models.ForeignKey('LevelType', on_delete=models.PROTECT)
    room_type = models.ForeignKey('RoomType', on_delete=models.PROTECT)
    name = models.CharField(max_length=100, blank=True)
    width = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    area = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    floor_type = models.ForeignKey('FloorType', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'property_rooms'
        ordering = ['level', 'order']
        
    def __str__(self):
        return f"{self.property.code} - {self.room_type.name} - {self.level.name}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        if self.width and self.length and not self.area:
            self.area = self.width * self.length
        super().save(*args, **kwargs)


# =============================================================================
# MODELO DE REQUERIMIENTOS (BUSQUEDAS DE CLIENTES)
# =============================================================================
class Requirement(TitleCaseMixin, models.Model):
    """Modelo para almacenar requerimientos/requests de clientes.

    - Los campos PII usan EncryptedCharField/EncryptedTextField.
    - Auditoría básica: created_by, modified_by, created_at, updated_at.
    """
    BUDGET_TYPE_CHOICES = (
        ('approx', 'Aproximado'),
        ('range', 'Rango'),
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='requirements_created')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='requirements_modified')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Contacto vinculado (reemplaza client_name y phone)
    contact = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True, related_name='requirements')
    
    # Datos del cliente (PII cifrada) - DEPRECADOS, usar contact FK
    client_name = EncryptedCharField(max_length=256, blank=True, null=True)
    phone = EncryptedCharField(max_length=80, blank=True, null=True)

    # Tipos y subtipos
    property_type = models.ForeignKey('PropertyType', on_delete=models.PROTECT, null=True, blank=True)
    property_subtype = models.ForeignKey('PropertySubtype', on_delete=models.PROTECT, null=True, blank=True)

    # Presupuesto
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES, default='approx')
    budget_approx = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Área de terreno (aproximado o rango)
    AREA_TYPE_CHOICES = (
        ('approx', 'Aproximado'),
        ('range', 'Rango'),
    )
    area_type = models.CharField(max_length=20, choices=AREA_TYPE_CHOICES, default='approx')
    land_area_approx = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    land_area_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    land_area_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # FRENTERA (aproximada o rango)
    FRONTERA_TYPE_CHOICES = (
        ('approx', 'Aproximada'),
        ('range', 'Rango'),
    )
    frontera_type = models.CharField(max_length=20, choices=FRONTERA_TYPE_CHOICES, default='approx')
    frontera_approx = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    frontera_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    frontera_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Moneda asociada al presupuesto
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT, null=True, blank=True)

    # Medio de pago y estado
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.PROTECT, null=True, blank=True)
    status = models.ForeignKey('PropertyStatus', on_delete=models.SET_NULL, null=True, blank=True)

    # Ubicación
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    province = models.ForeignKey('Province', on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True, blank=True)
    # Nota: `urbanization` single-FK eliminado; se usa solo `districts` M2M
    districts = models.ManyToManyField('District', blank=True, related_name='requirements_multiple')

    # Preferencia de pisos (selección múltiple): Sótano, 1º, 2º ... 20º
    preferred_floors = models.ManyToManyField('FloorOption', blank=True, related_name='requirements')

    # Zonificación (M2M): Urbano, Rural, Industrial, Comercial
    zonificaciones = models.ManyToManyField('ZoningOption', blank=True, related_name='requirements')

    # Cantidad de pisos para casas (1-5). Se guarda como entero sencillo.
    NUMBER_OF_FLOORS_CHOICES = [
        (1, '1 piso'),
        (2, '2 pisos'),
        (3, '3 pisos'),
        (4, '4 pisos'),
        (5, '5 pisos'),
    ]
    number_of_floors = models.PositiveSmallIntegerField(
        choices=NUMBER_OF_FLOORS_CHOICES,
        null=True,
        blank=True,
        verbose_name='Cantidad de pisos'
    )
    # Ascensor: almacena 'yes'/'no' cuando aplica (departamentos). Nullable para mantener compatibilidad.
    ASCENSOR_CHOICES = (
        ('yes', 'Sí'),
        ('no', 'No'),
    )
    ascensor = models.CharField(max_length=3, choices=ASCENSOR_CHOICES, null=True, blank=True, verbose_name='Ascensor')
    # Características
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    half_bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    floors = models.PositiveSmallIntegerField(null=True, blank=True)
    garage_spaces = models.PositiveSmallIntegerField(null=True, blank=True)

    notes = EncryptedTextField(blank=True, null=True)

    class Meta:
        db_table = 'requirements'
        verbose_name = 'Requerimiento'
        verbose_name_plural = 'Requerimientos'
        ordering = ['-created_at']

    def __str__(self):
        # Evitar mostrar PII en representaciones por defecto
        type_name = self.property_type.name if self.property_type else ''
        return f"Requerimiento {self.id} {type_name}"

    def save(self, *args, **kwargs):
        # Aplicar TitleCase si hay campos configurados
        self._apply_title_case()
        super().save(*args, **kwargs)

# =============================================================================
# MODELO DE AUDITORÍA DE CAMBIOS EN PROPIEDADES
# =============================================================================

class PropertyChange(models.Model):
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='changes')
    field_name = models.CharField(max_length=120)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_changes'
        ordering = ['-changed_at']

    def __str__(self):
        actor = self.changed_by.get_full_name() if self.changed_by else 'Sistema'
        return f"{self.property.code} | {self.field_name} @ {self.changed_at.strftime('%Y-%m-%d %H:%M')} by {actor}"


# =============================================================================
# MODELOS PARA INTEGRACIÓN CON WHATSAPP BUSINESS
# =============================================================================


# Nuevo modelo para números de WhatsApp
class WhatsAppNumber(models.Model):
    """Catálogo de números de WhatsApp para enlaces UTM (nuevo, seguro)"""
    number = models.CharField(max_length=50, unique=True, help_text="Número de WhatsApp (solo dígitos)")
    display_name = models.CharField(max_length=100, help_text="Nombre o alias para mostrar")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'whatsapp_numbers'
        verbose_name = "Número WhatsApp"
        verbose_name_plural = "Números WhatsApp"
        ordering = ['display_name']

    def __str__(self):
        return f"{self.display_name} ({self.number})"


class SocialNetwork(models.Model):
    """Catálogo de redes sociales para enlaces UTM/WhatsApp"""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Clase de ícono FontAwesome opcional")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'social_networks'
        verbose_name = "Red Social"
        verbose_name_plural = "Redes Sociales"
        ordering = ['name']

    def __str__(self):
        return self.name



class PropertyWhatsAppLink(models.Model):
    """Enlace único de WhatsApp por propiedad y red social (usando WhatsAppNumber)"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='whatsapp_links')
    social_network = models.ForeignKey('SocialNetwork', on_delete=models.PROTECT, related_name='whatsapp_links')
    whatsapp_number = models.ForeignKey('WhatsAppNumber', on_delete=models.PROTECT, related_name='whatsapp_links')
    link_name = models.CharField(max_length=100, help_text="Nombre del enlace (ej: 'Facebook Ads - Villa Marina')")
    unique_identifier = models.CharField(max_length=50, unique=True, db_index=True, help_text="Identificador único para tracking")
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, default='whatsapp')
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    utm_content = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='whatsapp_links_created')

    class Meta:
        db_table = 'property_whatsapp_links'
        ordering = ['-created_at']
        unique_together = [['property', 'social_network', 'whatsapp_number']]
        verbose_name = "Enlace WhatsApp de Propiedad"
        verbose_name_plural = "Enlaces WhatsApp de Propiedades"

    def __str__(self):
        return f"{self.property.code} - {self.link_name} ({self.social_network})"

    def get_whatsapp_url(self):
        """Genera URL de WhatsApp con mensaje inicial y validación."""
        import urllib.parse
        import logging

        logger = logging.getLogger(__name__)

        if not self.whatsapp_number or not self.whatsapp_number.number:
            logger.error(f"ERROR: PropertyWhatsAppLink (ID: {self.id}) no tiene un número de WhatsApp válido asignado. No se puede generar URL.")
            return "#error-no-numero"

        try:
            # Asegurarse de que el número solo contenga dígitos y quizás un '+' al inicio
            phone_number = ''.join(filter(str.isdigit, str(self.whatsapp_number.number)))
            
            text = f"Hola {self.unique_identifier}"
            text_encoded = urllib.parse.quote(text)
            
            url = f"https://wa.me/{phone_number}?text={text_encoded}"
            logger.info(f"URL de WhatsApp generada para Link ID {self.id}: {url}")
            return url
        except Exception as e:
            logger.error(f"Error generando URL de WhatsApp para Link ID {self.id}: {e}", exc_info=True)
            return "#error-generacion-url"


class LeadStatus(models.Model):
    """Estados personalizados para leads de WhatsApp"""
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='lead_statuses')
    name = models.CharField(max_length=100, help_text="Nombre del estado (ej: En Espera, Interesado, etc.)")
    color = models.CharField(max_length=7, default='#007bff', help_text="Color en formato hex (ej: #007bff para azul)")
    order = models.PositiveIntegerField(default=0, help_text="Orden de aparición en los filtros")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lead_statuses'
        ordering = ['order', 'name']
        unique_together = [['property', 'name']]
        verbose_name = "Estado de Lead"
        verbose_name_plural = "Estados de Lead"
    
    def __str__(self):
        return f"{self.property.code} - {self.name}"


class Lead(models.Model):
    """Lead generado desde WhatsApp"""
    
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='whatsapp_leads')
    whatsapp_link = models.ForeignKey(PropertyWhatsAppLink, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    phone_number = models.CharField(max_length=20, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    social_network = models.ForeignKey('SocialNetwork', on_delete=models.PROTECT, related_name='leads')
    
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    notes = models.TextField(blank=True, null=True)
    
    first_message_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_leads')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'whatsapp_leads'
        ordering = ['-created_at']
        unique_together = [['property', 'phone_number']]
        verbose_name = "Lead de WhatsApp"
        verbose_name_plural = "Leads de WhatsApp"
    
    def __str__(self):
        return f"{self.phone_number} - {self.property.code} ({self.social_network})"


class WhatsAppConversation(models.Model):
    """Conversación de WhatsApp entre usuario y telefonista"""
    MESSAGE_TYPE_CHOICES = (
        ('incoming', 'Entrante'),
        ('outgoing', 'Saliente'),
    )
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='messages')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='whatsapp_conversations')
    
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    message_body = models.TextField()
    message_id = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    
    sent_by_user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_messages')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Para mensajes con multimedia
    media_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(max_length=20, blank=True, null=True, help_text="image, video, document, audio")
    
    class Meta:
        db_table = 'whatsapp_conversations'
        ordering = ['created_at']
        verbose_name = "Conversación de WhatsApp"
        verbose_name_plural = "Conversaciones de WhatsApp"
    
    def __str__(self):
        return f"{self.lead.phone_number} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class UTMClick(models.Model):
    """Registro de clics UTM en enlaces de WhatsApp para tracking independiente."""
    whatsapp_link = models.ForeignKey('PropertyWhatsAppLink', on_delete=models.CASCADE, related_name='utm_clicks', db_constraint=False)
    tracking_id = models.CharField(max_length=50, db_index=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)
    utm_content = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.TextField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True, help_text="IPv4/IPv6")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'utm_clicks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_id']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'UTM Click'
        verbose_name_plural = 'UTM Clicks'

    def __str__(self):
        return f"{self.tracking_id} @ {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class OperationType(models.Model):
    """Tipos de operación: Venta, Alquiler, Anticresis, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'operation_types'
        ordering = ['order', 'name']
        verbose_name = "Tipo de Operación"
        verbose_name_plural = "Tipos de Operación"
    
    def __str__(self):
        return self.name


# =============================================================================
# MODELO PARA AGENDA Y EVENTOS
# =============================================================================

class EventType(models.Model):
    """Tipos de eventos: Visita, Reunión, Llamada, etc."""
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#047D7D', help_text='Color en formato hex (ej: #047D7D)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'event_types'
        verbose_name = "Tipo de Evento"
        verbose_name_plural = "Tipos de Evento"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(TitleCaseMixin, models.Model):
    """Modelo para eventos y visitas agendadas"""
    title_case_fields = ('titulo', 'interesado')
    
    code = models.CharField(max_length=20, unique=True, editable=False)
    event_type = models.ForeignKey('EventType', on_delete=models.PROTECT, verbose_name='Tipo de evento')
    titulo = models.CharField(max_length=200, verbose_name='Título')
    fecha_evento = models.DateField(verbose_name='Fecha del evento')
    hora_inicio = models.TimeField(verbose_name='Hora de inicio')
    hora_fin = models.TimeField(verbose_name='Hora de término')
    detalle = models.TextField(blank=True, verbose_name='Detalle de la visita')
    
    # Contacto vinculado (reemplaza interesado CharField)
    contact = models.ForeignKey('PropertyOwner', on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='events', verbose_name='Contacto')
    interesado = models.CharField(max_length=200, blank=True, verbose_name='Interesado')  # DEPRECADO, usar contact
    
    property = models.ForeignKey('Property', on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='property_events', verbose_name='Inmueble')
    
    # Auditoría
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                   related_name='created_events', verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'events'
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-fecha_evento', '-hora_inicio']
    
    def __str__(self):
        return f"{self.code} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generar código único para el evento
            import random
            import string
            from django.utils import timezone
            year = timezone.now().year
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.code = f"EVT{year}{random_str}"
        
        # Aplicar title case
        self._apply_title_case()
        
        super().save(*args, **kwargs)


class AgencyConfig(TitleCaseMixin, models.Model):
    """Configuración global de los datos de la inmobiliaria"""
    nombre_comercial = models.CharField(max_length=255, verbose_name="Nombre Comercial")
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social")
    ruc = models.CharField(max_length=11, verbose_name="RUC")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    departamento = models.CharField(max_length=100, verbose_name="Departamento")
    provincia = models.CharField(max_length=100, verbose_name="Provincia")
    distrito = models.CharField(max_length=100, verbose_name="Distrito")
    urbanizacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Urbanización")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    correo_electronico = models.EmailField(verbose_name="Correo Electrónico")
    logo = models.ImageField(upload_to='agency/logos/', blank=True, null=True, verbose_name="Logo")
    
    title_case_fields = ('nombre_comercial', 'razon_social', 'direccion', 'departamento', 'provincia', 'distrito', 'urbanizacion')

    class Meta:
        db_table = 'agency_config'
        verbose_name = "Datos de la Inmobiliaria"
        verbose_name_plural = "Datos de la Inmobiliaria"

    def __str__(self):
        return self.nombre_comercial
    
    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

class RequirementMatch(models.Model):
    requirement = models.ForeignKey(
        'Requirement',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    property = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        related_name='requirement_matches'
    )

    score = models.DecimalField(max_digits=6, decimal_places=2)  # 0.00 - 100.00
    details = models.JSONField(default=dict, blank=True)          # lo que viene de matching.py
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'requirement_matches'
        unique_together = [('requirement', 'property')]
        indexes = [
            models.Index(fields=['requirement', '-score']),
            models.Index(fields=['property', '-score']),
        ]
        ordering = ['-score']

    def __str__(self):
        return f"Req {self.requirement_id} - Prop {self.property_id} => {self.score}%"


