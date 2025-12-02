
from django.db import models
from django.contrib.auth import get_user_model
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
    first_name = EncryptedCharField(max_length=256, blank=True)
    last_name = EncryptedCharField(max_length=256, blank=True)
    maternal_last_name = EncryptedCharField(max_length=256, blank=True)
    
    # Documento de identidad (SIN ENCRIPTAR)
    document_type = models.ForeignKey('DocumentType', on_delete=models.PROTECT)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Género")
    phone = EncryptedCharField(max_length=256)
    maternal_last_name = EncryptedCharField(max_length=256, blank=True)
    document_type = models.ForeignKey('DocumentType', on_delete=models.PROTECT, null=True, blank=True)
    photo = models.ImageField(upload_to='owners/photos/', null=True, blank=True)
    document_number = models.CharField(max_length=50, verbose_name="Número de documento", blank=True)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Fecha de nacimiento")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Género", blank=True)
    phone = EncryptedCharField(max_length=256, blank=True)
    secondary_phone = EncryptedCharField(max_length=256, blank=True)
    email = EncryptedEmailField(max_length=255, blank=True)
    profession = models.ForeignKey('Profession', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.CharField(max_length=200, blank=True)
    observations = models.TextField(blank=True)
       # Dirección del contacto (usando los nuevos modelos)
    department = models.ForeignKey('Department', on_delete=models.PROTECT, verbose_name="Departamento")
    province = models.ForeignKey('Province', on_delete=models.PROTECT, verbose_name="Provincia")
    district = models.ForeignKey('District', on_delete=models.PROTECT, verbose_name="Distrito")
    urbanization = models.ForeignKey('Urbanization', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Urbanización")
    address_exact = models.TextField(blank=True, verbose_name="Dirección Exacta")
    address_coordinates = models.CharField(max_length=512, blank=True, verbose_name="Coordenadas")
    
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
        return f"{self.first_name} {self.last_name}"

    def full_name(self):
        if self.maternal_last_name:
            return f"{self.first_name} {self.last_name} {self.maternal_last_name}"
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

# =============================================================================
# MODELO PRINCIPAL DE PROPIEDAD
# =============================================================================

class Property(TitleCaseMixin, models.Model):
    title_case_fields = (
        'title',
        'department',
        'province',
        'district',
        'urbanization',
    )
    # Información básica
    code = models.CharField(max_length=20, unique=True)
    codigo_unico_propiedad = models.CharField(max_length=11, unique=True, blank=True, null=True, verbose_name="Código Único Propiedad")
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Relaciones principales
    owner = models.ForeignKey('PropertyOwner', on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey('PropertyType', on_delete=models.PROTECT)
    property_subtype = models.ForeignKey('PropertySubtype', on_delete=models.PROTECT)
    status = models.ForeignKey('PropertyStatus', on_delete=models.PROTECT)
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
    price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    has_maintenance = models.BooleanField(default=False)
    
    # Características físicas
    floors = models.PositiveIntegerField(default=1)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    half_bathrooms = models.PositiveIntegerField(default=0)
    
    # Garaje
    garage_spaces = models.PositiveIntegerField(default=0)
    garage_type = models.ForeignKey('GarageType', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Áreas
    land_area = models.DecimalField(max_digits=10, decimal_places=2)
    land_area_unit = models.ForeignKey('MeasurementUnit', on_delete=models.PROTECT, related_name='land_properties')
    built_area = models.DecimalField(max_digits=10, decimal_places=2)
    built_area_unit = models.ForeignKey('MeasurementUnit', on_delete=models.PROTECT, related_name='built_properties')
    front_measure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    depth_measure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Ubicación (SIN ENCRIPTAR)
        
    # ===== MEJORA 3: Nuevo campo para dirección real (de documentos) =====
    real_address = models.TextField(
        blank=True, 
        verbose_name="Dirección Real (de documentos)",
        help_text="Dirección exacta que aparece en documentos legales"
    )

    exact_address = models.CharField(
        max_length=512, 
        blank=True, 
        verbose_name="Dirección Exacta (para mapa)"
    )
    coordinates = models.CharField(max_length=512, blank=True)
    department = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    urbanization = models.CharField(max_length=100, blank=True)
    
    # POR ESTO:
# Servicios (con modelos independientes)
    water_service = models.ForeignKey('WaterServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='water_properties', verbose_name="Servicio de Agua")
    energy_service = models.ForeignKey('EnergyServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='energy_properties', verbose_name="Servicio de Energía")
    drainage_service = models.ForeignKey('DrainageServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='drainage_properties', verbose_name="Servicio de Drenaje")
    gas_service = models.ForeignKey('GasServiceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='gas_properties', verbose_name="Servicio de Gas")
    # Información adicional
    amenities = models.TextField(blank=True)
    zoning = models.CharField(max_length=100, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    
    # Auditoría y workflow
    created_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    assigned_agent = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_ready_for_sale = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'properties'
        verbose_name_plural = 'Properties'
        
    def __str__(self):
        return f"{self.code} - {self.title}"

    import random
    import string
    def save(self, *args, **kwargs):
        self._apply_title_case()
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
    image_type = models.ForeignKey('ImageType', on_delete=models.PROTECT)
    image_ambiente = models.ForeignKey('RoomType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ambiente de la imagen")
    image = models.ImageField(upload_to='properties/images/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_images'
        ordering = ['order']
        
    def __str__(self):
        return f"Imagen {self.id} - {self.property.code}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

class PropertyVideo(TitleCaseMixin, models.Model):
    title_case_fields = ('title',)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='videos')
    video_type = models.ForeignKey('VideoType', on_delete=models.PROTECT)
    video = models.FileField(upload_to='properties/videos/')
    title = models.CharField(max_length=255)
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
    document_type = models.ForeignKey('DocumentType', on_delete=models.PROTECT)
    file = models.FileField(upload_to='properties/documents/')
    title = EncryptedCharField(max_length=255)
    description = EncryptedTextField(blank=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'property_documents'
        
    def __str__(self):
        return f"Documento {self.id} - {self.property.code}"

    def save(self, *args, **kwargs):
        self._apply_title_case()
        super().save(*args, **kwargs)

# =============================================================================
# MODELO PARA INFORMACIÓN FINANCIERA
# =============================================================================

class PropertyFinancialInfo(models.Model):
    property = models.OneToOneField('Property', on_delete=models.CASCADE, related_name='financial_info')
    initial_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    negotiation_status = models.ForeignKey('NegotiationStatus', on_delete=models.SET_NULL, null=True, blank=True, related_name='financial_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'property_financial_info'
        verbose_name = 'Información financiera de la propiedad'
        verbose_name_plural = 'Información financiera de propiedades'

    def __str__(self):
        return f"Finanzas {self.property.code}" if self.property_id else 'Finanzas sin propiedad'


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


