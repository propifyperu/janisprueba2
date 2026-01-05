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
                form.add_error(None, 'Tu cuenta no ha sido activada. Por favor contacta al administrador.')
                return render(request, 'users/login.html', {'form': form, 'next': next_url})
        except CustomUser.DoesNotExist:
            pass
        
        # Intentar autenticar (solo funciona si el usuario está activo)
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            import logging
            logger = logging.getLogger(__name__)
            
            # Generar identificador del dispositivo basado en user-agent + IP
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            client_ip = request.META.get('REMOTE_ADDR', '')
            device_id = hashlib.sha256(f"{user_agent}{client_ip}".encode()).hexdigest()[:32]
            
            logger.info(f"[LOGIN] user={user.username}, device_id={device_id[:16]}...")
            
            # PASO 1: Verificar si el dispositivo ACTUAL está aprobado para este usuario
            approved_device = AuthorizedDevice.objects.filter(
                user=user,
                device_id=device_id,
                status='approved'
            ).first()

            # Si el usuario tiene algún dispositivo aprobado distinto al actual,
            # registrar un intento no autorizado para que los admins lo revisen.
            try:
                from security.models import UnauthorizedDeviceLoginAttempt
            except Exception:
                UnauthorizedDeviceLoginAttempt = None

            any_approved_elsewhere = AuthorizedDevice.objects.filter(user=user, status='approved').exclude(device_id=device_id).exists()
            if any_approved_elsewhere and not approved_device and UnauthorizedDeviceLoginAttempt:
                UnauthorizedDeviceLoginAttempt.objects.create(
                    user=user,
                    username=user.username,
                    device_id=device_id,
                    ip_address=client_ip,
                    user_agent=user_agent[:255]
                )
            
            if approved_device:
                logger.info(f"[LOGIN] ✓ Usuario tiene dispositivo aprobado (ID={approved_device.id})")
                # El usuario ya tiene un dispositivo aprobado
                # Actualizar la IP y user-agent del dispositivo aprobado
                approved_device.ip_address = client_ip
                approved_device.user_agent = user_agent[:255]
                approved_device.platform = request.META.get('HTTP_USER_AGENT', '')[:150]
                approved_device.save(update_fields=['ip_address', 'user_agent', 'platform'])
                logger.info(f"[LOGIN] ✓ Actualizando IP/user-agent del dispositivo aprobado")
                login(request, user)
                return redirect(next_url)
            
            logger.info(f"[LOGIN] ✗ Usuario NO tiene dispositivo aprobado aún")
            
            # PASO 2: Para usuarios nuevos, reutilizar el último dispositivo pendiente si existe
            # Esto evita crear múltiples duplicados si el device_id cambia entre peticiones
            pending_device = AuthorizedDevice.objects.filter(
                user=user,
                status='pending'
            ).order_by('-id').first()
            
            if pending_device:
                logger.info(f"[LOGIN] Reutilizando dispositivo pendiente ID={pending_device.id}")
                # Actualizar el device_id y datos del dispositivo existente
                pending_device.device_id = device_id
                pending_device.ip_address = client_ip
                pending_device.user_agent = user_agent[:255]
                pending_device.platform = request.META.get('HTTP_USER_AGENT', '')[:150]
                pending_device.save()
                device = pending_device
            else:
                logger.info(f"[LOGIN] Creando nuevo dispositivo pendiente")
                # Crear nuevo dispositivo
                device = AuthorizedDevice.objects.create(
                    user=user,
                    device_id=device_id,
                    platform=request.META.get('HTTP_USER_AGENT', '')[:150],
                    user_agent=user_agent[:255],
                    ip_address=client_ip,
                    status='pending',
                )
            
            logger.info(f"[LOGIN] Device: ID={device.id}, status='{device.status}'")
            
            # Redirigir a verificación
            logger.info(f"[LOGIN] Redirigiendo a verificación")
            request.session['pending_device_id'] = device.id
            request.session.modified = True
            return redirect('security:verify_device_id', device_id=device.id)
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
    from django.contrib import messages

    # Permitir cambiar tema desde el perfil (POST desde el desplegable)
    if request.method == 'POST' and request.user.is_authenticated:
        theme = request.POST.get('theme')
        try:
            profile = request.user.profile
        except Exception:
            # Crear perfil si no existe
            from .models import UserProfile
            profile = UserProfile.objects.create(user=request.user)

        if theme in dict(profile.THEME_CHOICES):
            profile.theme = theme
            profile.save(update_fields=['theme'])
            messages.success(request, 'Apariencia actualizada.')
        else:
            messages.error(request, 'Opción de apariencia inválida.')
        return redirect('users:profile')

    # Asegurar que la plantilla reciba el objeto `profile` en el contexto
    profile = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except Exception:
            from .models import UserProfile
            profile = UserProfile.objects.create(user=request.user)

    return render(request, 'users/profile.html', {'profile': profile})


def profile_edit_view(request):
    return render(request, 'users/profile_edit.html')
