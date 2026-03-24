from django.contrib import admin
from .models import CustomUser, Area, Role, UserProfile, RoleFieldPermission
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
import csv
from django.http import HttpResponse

User = get_user_model()
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'area', 'role', 'is_active', 'is_verified','is_superuser')
    list_filter = ('is_active', 'is_verified', 'is_active_agent', 'area', 'role', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('date_joined', 'last_login')
    actions = ['normalizar_telefonos', 'descargar_backup_csv']
    fieldsets = (
        ('Información de Cuenta', {
            'fields': ('username', 'email', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
        ('Organización', {
            'fields': ('area', 'role', 'commission_rate')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_verified', 'is_active_agent')
        }),
        ('Fechas', {
            'fields': ('date_joined', 'last_login')
        }),
        ('Permisos', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )

    @admin.action(description='Normalizar números de teléfono (+51)')
    def normalizar_telefonos(self, request, queryset):
        updated_count = 0
        for user in queryset:
            # Ignorar si el campo está vacío o es nulo
            if not user.phone:
                continue
            
            # Limpiar el número de posibles espacios o guiones accidentales
            clean_phone = user.phone.replace(' ', '').replace('-', '').strip()
            new_phone = user.phone

            # Regla 1: Si tiene 9 dígitos exactos, le agregamos el +51
            if len(clean_phone) == 9 and clean_phone.isdigit():
                new_phone = '+51' + clean_phone
            # Regla 2: Si empieza con 51 y en total tiene 11 dígitos, le agregamos el +
            elif clean_phone.startswith('51') and len(clean_phone) == 11 and clean_phone.isdigit():
                new_phone = '+' + clean_phone

            if user.phone != new_phone:
                user.phone = new_phone
                user.save(update_fields=['phone'])
                updated_count += 1
        
        self.message_user(request, f'Se normalizaron {updated_count} números de teléfono correctamente.')

    @admin.action(description='Descargar backup de usuarios (CSV)')
    def descargar_backup_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="backup_usuarios.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Username', 'Nombre', 'Apellido', 'Email', 'Telefono'])
        for user in queryset:
            writer.writerow([user.id, user.username, user.first_name, user.last_name, user.email, user.phone])
        return response

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('code','name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('area','name', 'code_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code_name', 'description')
    readonly_fields = ('created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'whatsapp_notifications', 'push_notifications', 'created_at')
    list_filter = ('email_notifications', 'whatsapp_notifications', 'push_notifications', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RoleFieldPermission)
class RoleFieldPermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'field_name', 'can_view', 'can_edit', 'updated_at')
    list_filter = ('role', 'can_view', 'can_edit', 'created_at')
    search_fields = ('role__name', 'field_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Información General', {
            'fields': ('role', 'field_name')
        }),
        ('Permisos', {
            'fields': ('can_view', 'can_edit'),
            'description': 'Controla si el rol puede ver o editar este campo'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('role', 'field_name')
