from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator
from django.urls import reverse
from .models import AuthorizedDevice

def verify_device(request, device_id=None):
	"""Vista para que usuarios verifiquen su dispositivo durante el registro"""
	from django.contrib.auth import login
	from .models import DeviceStatus
	import logging
	
	logger = logging.getLogger(__name__)
	
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
	paginator = Paginator(devices.order_by('-registered_at'), 10)
	page_number = request.GET.get('page')
	page_obj = paginator.get_page(page_number)
	context = {
		'devices': page_obj.object_list,
		'pending_count': pending_count,
		'approved_count': approved_count,
		'blocked_count': blocked_count,
		'is_paginated': page_obj.has_other_pages(),
		'page_obj': page_obj,
		'current_status': status,
		'request': request,
	}
	return render(request, 'security/decive_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def device_status_update(request, pk):
	import logging
	logger = logging.getLogger(__name__)
	
	logger.info(f"device_status_update called with pk={pk}, method={request.method}")
	logger.info(f"POST data: {request.POST}")
	
	device = get_object_or_404(AuthorizedDevice, pk=pk)
	if request.method == 'POST':
		action = request.POST.get('action')
		logger.info(f"Action received: {action}")
		
		# Mapear acciones a estados correctos
		status_map = {
			'approve': 'approved',  # La acción 'approve' debe guardarse como 'approved'
			'block': 'blocked',      # La acción 'block' debe guardarse como 'blocked'
			'pending': 'pending'     # La acción 'pending' se guarda igual
		}
		if action in status_map:
			old_status = device.status
			device.status = status_map[action]
			device.save()
			logger.info(f"Device {pk} status updated from {old_status} to {device.status}")
		else:
			logger.warning(f"Invalid action: {action}")
	
	return redirect(reverse('security:device_list'))
