from django.contrib import admin
from .models import AuthorizedDevice

@admin.register(AuthorizedDevice)
class AuthorizedDeviceAdmin(admin.ModelAdmin):
	list_display = ('device_id', 'name', 'user', 'status', 'is_trusted', 'registered_at', 'last_seen_at')
	list_filter = ('status', 'is_trusted', 'platform')
	search_fields = ('device_id', 'name', 'user__username', 'user__email', 'ip_address')
