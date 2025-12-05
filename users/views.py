from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django import forms
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from security.models import AuthorizedDevice, DeviceStatus
import uuid

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
    from security.models import AuthorizedDevice, DeviceStatus
    import hashlib
    
    next_url = request.GET.get('next')
    if not next_url:
        next_url = '/dashboard/'
    # Verificar que el usuario esté autenticado Y activo
    if request.user.is_authenticated and request.user.is_active:
        return redirect(next_url)

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        # Intentar obtener el usuario para verificar su estado
        try:
            user = CustomUser.objects.get(username=username)
            # Si el usuario existe pero no está activo, mostrar mensaje de espera
            if not user.is_active:
                form.add_error(None, 'Tu cuenta está en proceso de verificación. Por favor espera la aprobación del administrador.')
                return render(request, 'users/login.html', {'form': form, 'next': next_url})
        except CustomUser.DoesNotExist:
            pass
        
        # Intentar autenticar (solo funciona si el usuario está activo)
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            # Generar identificador del dispositivo basado en user-agent + IP
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            client_ip = request.META.get('REMOTE_ADDR', '')
            device_id = hashlib.sha256(f"{user_agent}{client_ip}".encode()).hexdigest()[:32]
            
            # Buscar si el dispositivo existe y está autorizado
            try:
                device = AuthorizedDevice.objects.get(user=user, device_id=device_id)
                
                # Si el dispositivo existe pero NO está aprobado, redirigir a verificación
                if device.status != DeviceStatus.APPROVED:
                    request.session['pending_device_id'] = device.id
                    request.session.modified = True
                    return redirect('security:verify_device_id', device_id=device.id)
                
            except AuthorizedDevice.DoesNotExist:
                # Crear nuevo dispositivo pendiente de autorización
                device = AuthorizedDevice.objects.create(
                    user=user,
                    device_id=device_id,
                    platform=request.META.get('HTTP_USER_AGENT', '')[:150],
                    user_agent=user_agent[:255],
                    ip_address=client_ip,
                    status=DeviceStatus.PENDING,
                )
                request.session['pending_device_id'] = device.id
                request.session.modified = True
                return redirect('security:verify_device_id', device_id=device.id)
            
            # Si el dispositivo está aprobado, proceder con el login
            login(request, user)
            return redirect(next_url)
        else:
            form.add_error(None, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'users/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('users:login')


def register_view(request):
    if request.user.is_authenticated and request.user.is_active:
        return redirect('/dashboard/')
    
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        # Crear usuario inactivo
        user = CustomUser.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=form.cleaned_data.get('phone', ''),
            password=form.cleaned_data['password'],  # create_user() ya hashea la contraseña
            is_active=False,  # Usuario inactivo hasta ser aprobado
        )
        
        # Crear dispositivo inicial
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_agent))
        ip_address = request.META.get('REMOTE_ADDR', '')
        
        device = AuthorizedDevice.objects.create(
            user=user,
            device_id=device_id,
            user_agent=user_agent,
            ip_address=ip_address,
            platform=request.META.get('HTTP_SEC_CH_UA_PLATFORM', 'Desconocida'),
            status=DeviceStatus.PENDING,
            name=f"Dispositivo de registro"
        )
        
        # Limpiar la sesión anterior (si existe) y guardar solo los IDs de dispositivo
        for key in list(request.session.keys()):
            if key not in ['_session_expiry']:
                del request.session[key]
        
        request.session['registration_device_id'] = device.id
        request.session['registration_user_id'] = user.id
        request.session.modified = True
        
        return redirect('security:verify_device_id', device_id=device.id)
    
    return render(request, 'users/register.html', {'form': form})


def register_success_view(request):
    device_id = request.session.get('registration_device_id')
    device = None
    if device_id:
        try:
            device = AuthorizedDevice.objects.get(id=device_id)
        except AuthorizedDevice.DoesNotExist:
            pass
    
    context = {'device': device}
    return render(request, 'users/register_success.html', context)


def profile_view(request):
    return render(request, 'users/profile.html')


def profile_edit_view(request):
    return render(request, 'users/profile_edit.html')
