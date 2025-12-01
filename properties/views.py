
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, CreateView
from django.db.models import Q
from .models import Property, PropertyType, PropertyStatus, PropertyOwner
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
        queryset = (
            Property.objects.filter(is_active=True)
            .select_related('property_type', 'status', 'owner', 'created_by', 'currency')
            .prefetch_related('images')
        )

        # Si el usuario es agente, mostrar solo sus propiedades y asignadas
        if self.request.user.role and self.request.user.role.code_name == 'agent':
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(assigned_agent=self.request.user)
            )

        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(code__icontains=search)
                | Q(owner__first_name__icontains=search)
                | Q(owner__last_name__icontains=search)
            )

        property_type = self.request.GET.get('property_type', '').strip()
        if property_type:
            queryset = queryset.filter(property_type_id=property_type)

        status = self.request.GET.get('status', '').strip()
        if status:
            queryset = queryset.filter(status_id=status)

        department = self.request.GET.get('department', '').strip()
        if department:
            queryset = queryset.filter(department__iexact=department)

        price_min = self.request.GET.get('price_min', '').strip()
        if price_min:
            try:
                queryset = queryset.filter(price__gte=Decimal(price_min))
            except (InvalidOperation, ValueError):
                pass

        price_max = self.request.GET.get('price_max', '').strip()
        if price_max:
            try:
                queryset = queryset.filter(price__lte=Decimal(price_max))
            except (InvalidOperation, ValueError):
                pass

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = context['properties']

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

            # ...existing code...


# ===================== VISTA FUNCIONAL PARA CREAR PROPIEDAD =====================
@login_required
def create_property_view(request):
    from .models import PropertyType, PropertyStatus, PropertyOwner
    from .forms import PropertyForm, PropertyOwnerForm, PropertyFinancialInfoForm
    # Listas para selects
    departments = PropertyOwner.objects.values('department').distinct()
    level_types = []  # Debes cargar desde tu modelo correspondiente
    room_types = []   # Debes cargar desde tu modelo correspondiente
    floor_types = []  # Debes cargar desde tu modelo correspondiente

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

    # Cargar listas para selects
    # Debes ajustar estas consultas según tus modelos
    departments = PropertyOwner.objects.values('department').distinct()
    # Ejemplo: level_types = LevelType.objects.all()
    # Ejemplo: room_types = RoomType.objects.all()
    # Ejemplo: floor_types = FloorType.objects.all()

    return render(request, 'properties/property_create.html', {
        'form': form,
        'owner_form': owner_form,
        'financial_form': financial_form,
        'departments': departments,
        'level_types': level_types,
        'room_types': room_types,
        'floor_types': floor_types,
    })
