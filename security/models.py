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


class UnauthorizedDeviceLoginAttempt(models.Model):
	"""Registro de intentos de inicio de sesión desde dispositivos no autorizados.

	Permite que los administradores revisen quién intentó entrar desde un device_id
	que no está aprobado para el usuario y en qué fecha/hora ocurrió.
	"""
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		null=True,
		blank=True,
		related_name='unauthorized_login_attempts',
	)
	username = models.CharField(max_length=150, blank=True)
	device_id = models.CharField(max_length=255)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	user_agent = models.CharField(max_length=255, blank=True)
	attempted_at = models.DateTimeField(auto_now_add=True)
	resolved = models.BooleanField(default=False)
	resolved_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ('-attempted_at',)
		verbose_name = 'Intento de login no autorizado'
		verbose_name_plural = 'Intentos de login no autorizados'

	def __str__(self) -> str:
		who = self.username or (self.user.username if self.user else 'Anon')
		return f"{who} @ {self.attempted_at:%Y-%m-%d %H:%M} ({self.device_id})"

