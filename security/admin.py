from django.contrib import admin
from .models import AuthorizedDevice

@admin.register(AuthorizedDevice)
class AuthorizedDeviceAdmin(admin.ModelAdmin):
	list_display = ('name', 'user', 'status', 'platform', 'ip_address', 'is_trusted', 'registered_at', 'last_seen_at')
	list_filter = ('status', 'is_trusted', 'platform', 'registered_at', 'last_seen_at')
	search_fields = ('device_id', 'name', 'user__username', 'user__email', 'ip_address', 'user_agent')
	readonly_fields = ('device_id', 'user_agent', 'registered_at', 'updated_at')
	fieldsets = (
		('Información del Dispositivo', {
			'fields': ('name', 'device_id', 'platform', 'user_agent', 'ip_address')
		}),
		('Usuario', {
			'fields': ('user',)
		}),
		('Estado', {
			'fields': ('status', 'is_trusted')
		}),
		('Fechas', {
			'fields': ('registered_at', 'updated_at', 'last_seen_at')
		}),
	)
	actions = ['mark_as_approved', 'mark_as_blocked', 'mark_as_pending']

	def mark_as_approved(self, request, queryset):
		updated = queryset.update(status='approved')
		self.message_user(request, f'{updated} dispositivo(s) marcado(s) como aprobado(s).')
	mark_as_approved.short_description = 'Aprobar dispositivos seleccionados'

	def mark_as_blocked(self, request, queryset):
		updated = queryset.update(status='blocked')
		self.message_user(request, f'{updated} dispositivo(s) marcado(s) como bloqueado(s).')
	mark_as_blocked.short_description = 'Bloquear dispositivos seleccionados'

	def mark_as_pending(self, request, queryset):
		updated = queryset.update(status='pending')
		self.message_user(request, f'{updated} dispositivo(s) marcado(s) como pendiente(s).')
	mark_as_pending.short_description = 'Marcar dispositivos como pendiente'
