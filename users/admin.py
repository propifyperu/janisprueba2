from django.contrib import admin
from .models import CustomUser, Department, Role, UserProfile

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'department', 'role', 'is_active', 'is_verified')
    list_filter = ('is_active', 'is_verified', 'is_active_agent', 'department', 'role', 'date_joined')
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
            'fields': ('department', 'role', 'commission_rate')
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

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
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
