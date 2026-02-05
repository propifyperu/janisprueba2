from django.contrib import admin
from .models import CustomUser, Area, Role, UserProfile, RoleFieldPermission

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'area', 'role', 'is_active', 'is_verified','is_superuser')
    list_filter = ('is_active', 'is_verified', 'is_active_agent', 'area', 'role', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    readonly_fields = ('date_joined', 'last_login')
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

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code_name', 'is_active', 'created_at')
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
