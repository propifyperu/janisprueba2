from django.conf import settings
from django.db import models


class DeviceStatus(models.TextChoices):
	PENDING = 'pending', 'Pendiente'
	APPROVED = 'approved', 'Aprobado'
	BLOCKED = 'blocked', 'Bloqueado'


class AuthorizedDevice(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='authorized_devices',
	)
	device_id = models.CharField(max_length=255)
	name = models.CharField(max_length=120, blank=True)
	platform = models.CharField(max_length=150, blank=True)
	user_agent = models.CharField(max_length=255, blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	status = models.CharField(
		max_length=20,
		choices=DeviceStatus.choices,
		default=DeviceStatus.PENDING,
	)
	is_trusted = models.BooleanField(default=False)
	last_seen_at = models.DateTimeField(null=True, blank=True)
	registered_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		db_table = 'security_authorizeddevice'
		ordering = ('-updated_at',)
		verbose_name = 'Dispositivo autorizado'
		verbose_name_plural = 'Dispositivos autorizados'
		indexes = [
			models.Index(fields=('device_id',)),
			models.Index(fields=('user', 'status')),
		]
		constraints = [
			models.UniqueConstraint(fields=('user', 'device_id'), name='security_device_user_device_unique'),
		]

	def __str__(self) -> str:
		base_name = self.name or self.platform or 'Dispositivo sin nombre'
		return f"{base_name} ({self.get_status_display()})"

