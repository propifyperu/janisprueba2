from django.contrib.auth.models import AbstractUser
from django.db import models

class Area(models.Model):
    code = models.CharField(max_length=30, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.name

class Role(models.Model):
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='roles', null=True, blank=True,)
    name = models.CharField(max_length=50, unique=True)
    code_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active_agent = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username

class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Configuración de notificaciones
    email_notifications = models.BooleanField(default=True)
    whatsapp_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=False)
    # Preferencia de apariencia del usuario: 'green' (por defecto) o 'black'
    THEME_CHOICES = (
        ('green', 'Verde (predeterminado)'),
        ('black', 'Negro'),
    )
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='green')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Perfil de {self.user.username}"


class RoleFieldPermission(models.Model):
    """Controla qué campos pueden ver los usuarios de cada rol"""
    
    # Campos disponibles en Property que pueden ser restringidos
    VISIBLE_FIELDS = (
        ('title', 'Título'),
        ('description', 'Descripción'),
        ('price', 'Precio'),
        ('currency', 'Moneda'),
        ('maintenance_fee', 'Cuota de Mantenimiento'),
        ('property_type', 'Tipo de Propiedad'),
        ('property_subtype', 'Subtipo de Propiedad'),
        ('status', 'Estado'),
        ('bedrooms', 'Dormitorios'),
        ('bathrooms', 'Baños'),
        ('half_bathrooms', 'Medios Baños'),
        ('garage_spaces', 'Espacios de Garaje'),
        ('garage_type', 'Tipo de Garaje'),
        ('land_area', 'Área de Terreno'),
        ('built_area', 'Área Construida'),
        ('front_measure', 'Medida del Frente'),
        ('depth_measure', 'Profundidad'),
        ('coordinates', 'Coordenadas'),
        ('exact_address', 'Dirección Exacta'),
        ('real_address', 'Dirección Real'),
        ('department', 'Departamento'),
        ('province', 'Provincia'),
        ('district', 'Distrito'),
        ('urbanization', 'Urbanización'),
        ('water_service', 'Servicio de Agua'),
        ('energy_service', 'Servicio de Energía'),
        ('drainage_service', 'Servicio de Drenaje'),
        ('gas_service', 'Servicio de Gas'),
        ('amenities', 'Servicios/Amenidades'),
        ('zoning', 'Zonificación'),
        ('price_history', 'Historial de Precios'),
        ('images', 'Imágenes'),
        ('videos', 'Videos'),
        ('documents', 'Documentos'),
        ('financial_info', 'Información Financiera'),
        ('rooms', 'Ambientes'),
        ('owner_contact', 'Contacto del Propietario'),
        ('responsible', 'Responsable'),
        ('assigned_agent', 'Agente Asignado'),
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='field_permissions'
    )
    field_name = models.CharField(
        max_length=50,
        choices=VISIBLE_FIELDS,
        help_text='Campo de la propiedad'
    )
    can_view = models.BooleanField(
        default=True,
        help_text='¿Puede ver este campo?'
    )
    can_edit = models.BooleanField(
        default=False,
        help_text='¿Puede editar este campo?'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'role_field_permissions'
        unique_together = ('role', 'field_name')
        verbose_name = 'Permiso de Campo por Rol'
        verbose_name_plural = 'Permisos de Campos por Roles'
    
    def __str__(self):
        return f"{self.role.name} - {self.get_field_name_display()}"