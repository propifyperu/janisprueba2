from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import JsonResponse
from .models import AuthorizedDevice
from .models import UnauthorizedDeviceLoginAttempt

def verify_device(request, device_id=None):
	"""Vista para que usuarios verifiquen su dispositivo durante el registro"""
	from django.contrib.auth import login
	from .models import DeviceStatus
	from .models import SecuritySettings  # Importar configuración
	import logging
	
	logger = logging.getLogger(__name__)

	# Verificar si la validación de seguridad está habilitada
	settings = SecuritySettings.get_settings()
	if not settings.device_verification_enabled:
		# Si está desactivada, redirigir al dashboard si está autenticado
		if request.user.is_authenticated:
			return redirect('/dashboard/')
		# Si no, redirigir al login
		return redirect('users:login')
	
	# Primero intentar obtener desde URL, luego desde sesión
	device = None
	
	if device_id:
		try:
			device = AuthorizedDevice.objects.get(id=device_id)
		except AuthorizedDevice.DoesNotExist:
			return redirect('users:login')
	
	if not device:
		# Intentar desde sesión (para usuarios autenticados)
		device_id_session = request.session.get('pending_device_id') or request.session.get('registration_device_id')
		if device_id_session:
			try:
				device = AuthorizedDevice.objects.get(id=device_id_session)
			except AuthorizedDevice.DoesNotExist:
				pass
	
	if not device:
		return redirect('users:login')
	
	# Actualizar los datos del dispositivo desde la base de datos (para verificar cambios recientes)
	device.refresh_from_db()
	
	# Log para debugging
	logger.info(f"Device {device.id} status: {repr(device.status)}")
	
	# Verificar si el dispositivo fue aprobado (comparar directamente con la cadena)
	if device.status == 'approved':
		logger.info(f"Device {device.id} approved! Redirecting to dashboard")
		# Limpiar la sesión
		if 'pending_device_id' in request.session:
			del request.session['pending_device_id']
		if 'registration_device_id' in request.session:
			del request.session['registration_device_id']
		request.session.modified = True
		
		# Si no hay usuario autenticado, hacer login
		if not request.user.is_authenticated:
			login(request, device.user)
		
		# Redirigir al dashboard
		return redirect('/dashboard/')
	
	logger.info(f"Device {device.id} is still {device.status}, showing verification page")
	
	context = {
		'device': device,
		'device_id': device.device_id,
		'device_name': device.name or device.platform,
		'ip_address': device.ip_address,
		'platform': device.platform,
	}
	
	response = render(request, 'security/verify_device.html', context)
	# No cachear la página de verificación
	response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
	response['Pragma'] = 'no-cache'
	response['Expires'] = '0'
	return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def device_list(request):
	q = request.GET.get('q', '')
	status = request.GET.get('status', '')
	devices = AuthorizedDevice.objects.all()
	if q:
		devices = devices.filter(device_id__icontains=q)
	if status:
		devices = devices.filter(status=status)
	pending_count = AuthorizedDevice.objects.filter(status='pending').count()
	approved_count = AuthorizedDevice.objects.filter(status='approved').count()
	blocked_count = AuthorizedDevice.objects.filter(status='blocked').count()
	
	from .models import SecuritySettings
	settings = SecuritySettings.get_settings()
	
	paginator = Paginator(devices.order_by('-registered_at'), 10)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'devices': page_obj.object_list,
		'pending_count': pending_count,
		'approved_count': approved_count,
		'blocked_count': blocked_count,
		'is_verification_enabled': settings.device_verification_enabled,
		'is_paginated': page_obj.has_other_pages(),
		'page_obj': page_obj,
		'current_status': status,
		'request': request,
	}
	return render(request, 'security/decive_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def unauthorized_attempts_list(request):
	"""Lista de intentos de inicio de sesión desde dispositivos no autorizados."""
	attempts = UnauthorizedDeviceLoginAttempt.objects.all()
	q = request.GET.get('q', '')
	if q:
		attempts = attempts.filter(username__icontains=q) | attempts.filter(device_id__icontains=q)
	paginator = Paginator(attempts, 20)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'attempts': page_obj.object_list,
		'page_obj': page_obj,
		'is_paginated': page_obj.has_other_pages(),
		'request': request,
	}
	return render(request, 'security/unauthorized_attempts.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_attempt(request, pk):
	"""Aprobar un intento creando (o actualizando) un AuthorizedDevice y marcando el intento como resuelto."""
	import logging
	from django.utils import timezone

	logger = logging.getLogger(__name__)
	attempt = get_object_or_404(UnauthorizedDeviceLoginAttempt, pk=pk)

	if request.method == 'POST':
		# Crear o actualizar AuthorizedDevice
		device, created = AuthorizedDevice.objects.get_or_create(
			user=attempt.user,
			device_id=attempt.device_id,
			defaults={
				'platform': attempt.user_agent[:150],
				'user_agent': attempt.user_agent[:255],
				'ip_address': attempt.ip_address,
				'status': 'approved',
				'name': 'Aprobado desde attempts'
			}
		)
		if not created:
			device.status = 'approved'
			device.ip_address = attempt.ip_address
			device.user_agent = attempt.user_agent[:255]
			device.save(update_fields=['status', 'ip_address', 'user_agent'])

		attempt.resolved = True
		attempt.resolved_at = timezone.now()
		attempt.save(update_fields=['resolved', 'resolved_at'])
		logger.info(f"[ATTEMPT_APPROVE] Approved device {device.id} for user {attempt.user}")

	return redirect(reverse('security:unauthorized_attempts'))

@login_required
@user_passes_test(lambda u: u.is_superuser)
def device_status_update(request, pk):
	import logging
	logger = logging.getLogger(__name__)
	
	logger.info(f"[DEVICE_UPDATE] Iniciado: pk={pk}, method={request.method}")
	
	device = get_object_or_404(AuthorizedDevice, pk=pk)
	logger.info(f"[DEVICE_UPDATE] Device encontrado: id={device.id}, user={device.user.username}, status_actual='{device.status}'")
	
	if request.method == 'POST':
		action = request.POST.get('action')
		logger.info(f"[DEVICE_UPDATE] Action recibido: '{action}'")
		
		# Mapear acciones a estados correctos (siempre usar strings)
		status_map = {
			'approve': 'approved',
			'block': 'blocked',
			'pending': 'pending'
		}
		
		if action in status_map:
			old_status = device.status
			new_status = status_map[action]
			device.status = new_status
			device.save(update_fields=['status'])  # Guardar solo el campo status
			device.refresh_from_db()
			logger.info(f"[DEVICE_UPDATE] ✓ Guardado: {old_status} → {new_status}")
			logger.info(f"[DEVICE_UPDATE] ✓ Verificación en DB: status='{device.status}'")
		else:
			logger.warning(f"[DEVICE_UPDATE] ✗ Action inválida: '{action}'")
	else:
		logger.info(f"[DEVICE_UPDATE] No es POST, ignorando")
	
	logger.info(f"[DEVICE_UPDATE] Redirigiendo a device_list")
	return redirect(reverse('security:device_list'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def role_field_permissions_view(request):
	"""Vista para gestionar permisos de campos por rol (solo superuser)"""
	from users.models import Role, RoleFieldPermission
	from django.db.models import Q
	import json
	
	roles = Role.objects.filter(is_active=True).order_by('name')
	
	# Obtener todos los campos disponibles
	available_fields = dict(RoleFieldPermission.VISIBLE_FIELDS)
	
	# Preparar datos para el template
	roles_data = []
	for role in roles:
		permissions = RoleFieldPermission.objects.filter(role=role).values(
			'field_name', 'can_view', 'can_edit'
		)
		permissions_dict = {p['field_name']: p for p in permissions}
		
		fields_with_perms = []
		for field_name, field_display in RoleFieldPermission.VISIBLE_FIELDS:
			if field_name in permissions_dict:
				perm = permissions_dict[field_name]
			else:
				# Si no existe permiso, crear valores por defecto
				perm = {
					'field_name': field_name,
					'can_view': True,
					'can_edit': False
				}
			perm['display_name'] = field_display
			fields_with_perms.append(perm)
		
		roles_data.append({
			'role': {
				'id': role.id,
				'name': role.name,
				'code_name': role.code_name
			},
			'fields': fields_with_perms
		})
	
	# Convertir roles_data a JSON para que sea fácil de usar en JavaScript
	roles_data_json = json.dumps(roles_data)
	
	context = {
		'roles_data': roles_data,
		'roles_data_json': roles_data_json,
		'available_fields': available_fields,
	}
	
	return render(request, 'security/role_field_permissions.html', context)


@login_required
def save_role_field_permission(request):
	"""API para guardar permisos de campos por rol"""
	if not request.user.is_superuser:
		return JsonResponse({'success': False, 'error': 'No tienes permiso'}, status=403)
	
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=400)
	
	import json
	from users.models import Role, RoleFieldPermission
	
	try:
		data = json.loads(request.body)
		role_id = data.get('role_id')
		field_name = data.get('field_name')
		permission_type = data.get('permission')  # 'can_view' o 'can_edit'
		value = data.get('value', False)
		
		role = Role.objects.get(id=role_id)
		
		# Obtener o crear el permiso
		perm, created = RoleFieldPermission.objects.get_or_create(
			role=role,
			field_name=field_name
		)
		
		# Actualizar el permiso
		if permission_type == 'can_view':
			perm.can_view = value
		elif permission_type == 'can_edit':
			perm.can_edit = value
		
		perm.save()
		
		return JsonResponse({'success': True, 'message': 'Permiso actualizado'})
	
	except Role.DoesNotExist:
		return JsonResponse({'success': False, 'error': 'Rol no encontrado'}, status=404)
	except json.JSONDecodeError:
		return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_device_verification(request):
	if request.method != 'POST':
		return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
	
	import json
	try:
		data = json.loads(request.body)
		enabled = data.get('enabled', True)
		
		from .models import SecuritySettings
		settings = SecuritySettings.get_settings()
		settings.device_verification_enabled = enabled
		settings.save()
		
		return JsonResponse({'success': True, 'enabled': enabled})
	except Exception as e:
		return JsonResponse({'success': False, 'error': str(e)}, status=500)
