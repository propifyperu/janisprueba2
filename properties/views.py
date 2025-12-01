
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, CreateView
from django.db.models import Q
from .models import Property, PropertyType, PropertyStatus, PropertyOwner, PropertySubtype
from .forms import PropertyOwnerForm

# ...existing code...

# Vista para editar contacto
class ContactEditView(LoginRequiredMixin, UpdateView):
    model = PropertyOwner
    form_class = PropertyOwnerForm
    template_name = 'properties/contact_edit.html'

    def form_valid(self, form):
        contact = form.save(commit=False)
        contact.modified_by = self.request.user
        contact.save()
        form.save_m2m()
        from django.contrib import messages
        messages.success(self.request, 'Contacto actualizado exitosamente.')
        return redirect('properties:contact_detail', pk=contact.pk)

# Importaciones necesarias antes de las clases
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from .models import Property, PropertyType, PropertyStatus, PropertyOwner
from .forms import PropertyOwnerForm
from .models import PropertyOwner
from django.views.generic import ListView, CreateView, DetailView
from django.db.models import Q

# Vista para detalle de contacto
class ContactDetailView(LoginRequiredMixin, DetailView):
    model = PropertyOwner
    template_name = 'properties/contact_detail.html'
    context_object_name = 'contact'

class ContactListView(LoginRequiredMixin, ListView):
    model = PropertyOwner
    template_name = 'properties/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 12

    def get_queryset(self):
        queryset = PropertyOwner.objects.filter(is_active=True)
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(maternal_last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset.order_by('-created_at')

class ContactCreateView(LoginRequiredMixin, CreateView):
    model = PropertyOwner
    form_class = PropertyOwnerForm
    template_name = 'properties/contact_create.html'

    def form_valid(self, form):
        contact = form.save(commit=False)
        contact.created_by = self.request.user
        contact.save()
        form.save_m2m()
        from django.contrib import messages
        messages.success(self.request, 'Contacto creado exitosamente.')
        return redirect('properties:contact_list')



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django import forms
from decimal import Decimal, InvalidOperation
from django.urls import reverse
from django.conf import settings
from django.templatetags.static import static

# Vista para el detalle de propiedad
class PropertyDetailView(LoginRequiredMixin, DetailView):
    model = Property
    template_name = 'properties/property_detail.html'
    context_object_name = 'property'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Puedes agregar más datos al contexto si lo necesitas
        return context


class PropertyDashboardView(LoginRequiredMixin, ListView):
    model = Property
    template_name = 'properties/dashboard.html'
    context_object_name = 'properties'
    paginate_by = None

    def get_queryset(self):
        queryset = Property.objects.filter(is_active=True)

        # Mostrar todas las propiedades activas, sin filtrar por usuario o agente



        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = context.get('properties', [])
        context['property_count'] = len(properties) if hasattr(properties, '__len__') else properties.count()

        context['user_role'] = self.request.user.role.name if self.request.user.role else 'Sin rol'
        context['property_types'] = PropertyType.objects.filter(is_active=True).order_by('name')
        context['statuses'] = PropertyStatus.objects.filter(is_active=True).order_by('order')
        context['departments_list'] = (
            Property.objects.filter(is_active=True)
            .exclude(department='')
            .values_list('department', flat=True)
            .distinct()
            .order_by('department')
        )

        context['filters'] = {
            'search': self.request.GET.get('search', '').strip(),
            'property_type': self.request.GET.get('property_type', '').strip(),
            'status': self.request.GET.get('status', '').strip(),
            'department': self.request.GET.get('department', '').strip(),
            'price_min': self.request.GET.get('price_min', '').strip(),
            'price_max': self.request.GET.get('price_max', '').strip(),
        }

        markers = []
        for property_obj in properties:
            lat = lng = None
            if property_obj.coordinates:
                parts = [p.strip() for p in property_obj.coordinates.split(',') if p.strip()]
                if len(parts) == 2:
                    try:
                        lat = float(parts[0])
                        lng = float(parts[1])
                    except ValueError:
                        lat = lng = None
        # ...existing code...


# ===================== VISTA FUNCIONAL PARA CREAR PROPIEDAD =====================
@login_required
def create_property_view(request):
    from .models import (
        PropertyType, PropertyStatus, PropertyOwner,
        Department, LevelType, RoomType, FloorType
    )
    from .forms import PropertyForm, PropertyOwnerForm, PropertyFinancialInfoForm
    # Listas para selects
    departments = Department.objects.filter(is_active=True).order_by('name')
    level_types = LevelType.objects.filter(is_active=True).order_by('name')
    room_types = RoomType.objects.filter(is_active=True).order_by('name')
    floor_types = FloorType.objects.filter(is_active=True).order_by('name')

    owner_form = PropertyOwnerForm(request.POST or None)
    financial_form = PropertyFinancialInfoForm(request.POST or None)
    form = PropertyForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if form.is_valid() and owner_form.is_valid() and financial_form.is_valid():
            existing_owner_id = request.POST.get('existing_owner')
            if existing_owner_id:
                owner = PropertyOwner.objects.get(pk=existing_owner_id)
            else:
                owner = owner_form.save(commit=False)
                owner.created_by = request.user
                owner.save()
                owner_form.save_m2m()

            property_obj = form.save(commit=False)
            property_obj.owner = owner
            property_obj.created_by = request.user
            property_obj.save()
            form.save_m2m()

            financial_info = financial_form.save(commit=False)
            financial_info.property = property_obj
            financial_info.save()

            from django.contrib import messages
            messages.success(request, 'Propiedad creada exitosamente.')
            from django.urls import reverse
            return redirect(reverse('properties:list'))

    # (Las listas ya fueron cargadas arriba)

    contactos_existentes = PropertyOwner.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'properties/property_create.html', {
        'form': form,
        'owner_form': owner_form,
        'financial_form': financial_form,
        'departments': departments,
        'level_types': level_types,
        'room_types': room_types,
        'floor_types': floor_types,
        'contactos_existentes': contactos_existentes,
    })


def api_property_subtypes(request):
    """API simple que devuelve subtipos por tipo de propiedad (GET param: property_type_id)."""
    from django.http import JsonResponse

    property_type_id = request.GET.get('property_type_id')
    if not property_type_id:
        return JsonResponse({'subtypes': []})

    subtypes = PropertySubtype.objects.filter(property_type_id=property_type_id, is_active=True).values('id', 'name')
    return JsonResponse({'subtypes': list(subtypes)})


def api_provinces(request):
    """Devuelve una lista de provincias para un departamento dado (GET param: department_id).
    Retorna un array JSON de objetos {id, name} para consumo directo por el JS.
    """
    from django.http import JsonResponse
    from .models import Province

    department_id = request.GET.get('department_id')
    if not department_id:
        return JsonResponse([], safe=False)

    provinces = Province.objects.filter(department_id=department_id, is_active=True).values('id', 'name')
    return JsonResponse(list(provinces), safe=False)


def api_districts(request):
    """Devuelve una lista de distritos para una provincia dada (GET param: province_id)."""
    from django.http import JsonResponse
    from .models import District

    province_id = request.GET.get('province_id')
    if not province_id:
        return JsonResponse([], safe=False)

    districts = District.objects.filter(province_id=province_id, is_active=True).values('id', 'name')
    return JsonResponse(list(districts), safe=False)


def api_urbanizations(request):
    """Devuelve una lista de urbanizaciones para un distrito dado (GET param: district_id)."""
    from django.http import JsonResponse
    from .models import Urbanization

    district_id = request.GET.get('district_id')
    if not district_id:
        return JsonResponse([], safe=False)

    urbanizations = Urbanization.objects.filter(district_id=district_id, is_active=True).values('id', 'name')
    return JsonResponse(list(urbanizations), safe=False)
