from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator
from django.urls import reverse
from .models import AuthorizedDevice

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
	device = get_object_or_404(AuthorizedDevice, pk=pk)
	if request.method == 'POST':
		action = request.POST.get('action')
		if action in ['approve', 'block', 'pending']:
			device.status = action
			device.save()
	return redirect(reverse('security:device_list'))
