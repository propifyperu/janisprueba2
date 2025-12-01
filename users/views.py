def profile_edit_view(request):
    return render(request, 'users/profile_edit.html')
from django.shortcuts import render

def profile_view(request):
    return render(request, 'users/profile.html')
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


def login_view(request):
    next_url = request.GET.get('next')
    if not next_url:
        next_url = '/dashboard/'
    if request.user.is_authenticated:
        return redirect(next_url)

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user is not None:
            from security.models import AuthorizedDevice
            device_id = request.META.get('HTTP_USER_AGENT', '')[:128]
            ip_address = request.META.get('REMOTE_ADDR')
            platform = request.META.get('HTTP_SEC_CH_UA_PLATFORM', '')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_obj = AuthorizedDevice.objects.filter(user=user, device_id=device_id).first()
            if not device_obj:
                device_obj = AuthorizedDevice.objects.create(
                    user=user,
                    device_id=device_id,
                    name=platform,
                    platform=platform,
                    user_agent=user_agent,
                    ip_address=ip_address,
                    status='pending',
                )
            if device_obj.status == 'pending':
                return render(request, 'users/login.html', {
                    'form': form,
                    'next': next_url,
                    'device_pending': True
                })
            login(request, user)
            return redirect(next_url)
        else:
            form.add_error(None, 'Usuario o contraseña incorrectos.')
    return render(request, 'users/login.html', {'form': form, 'next': next_url})

def logout_view(request):
    logout(request)
    return redirect('users:login')
