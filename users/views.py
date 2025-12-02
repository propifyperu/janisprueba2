def profile_edit_view(request):
    return render(request, 'users/profile_edit.html')
from django.shortcuts import render

def profile_view(request):
    return render(request, 'users/profile.html')
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django import forms
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class LoginForm(forms.Form):
    username = forms.CharField(label='Usuario', max_length=150)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    first_name = forms.CharField(label='Nombre', max_length=150, required=True)
    last_name = forms.CharField(label='Apellido', max_length=150, required=True)
    email = forms.EmailField(label='Correo Electrónico', required=True)
    username = forms.CharField(label='Usuario', max_length=150, required=True)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput, required=True)
    password_confirm = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput, required=True)
    phone = forms.CharField(label='Teléfono', max_length=20, required=False)
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError('Este usuario ya está registrado.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Las contraseñas no coinciden.')
        
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e.messages)
        
        return cleaned_data


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

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = CustomUser.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=form.cleaned_data.get('phone', ''),
            is_active=False,  # Usuario inactivo hasta ser aprobado
        )
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        return redirect('users:register_success')
    
    return render(request, 'users/register.html', {'form': form})

def register_success_view(request):
    return render(request, 'users/register_success.html')
