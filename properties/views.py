from .models import Property
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

# Vista ULTRA SIMPLE sin templates - SOLO HTML PURO
def simple_properties_view(request):
    """Vista que devuelve HTML puro con las propiedades."""
    try:
        properties = Property.objects.all().order_by('-created_at')
        count = properties.count()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Propiedades</title>
            <style>
                body {{ font-family: Arial; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #047d7d; color: white; }}
            </style>
        </head>
        <body>
            <h1>Propiedades en BD: {count}</h1>
            <table>
                <tr><th>ID</th><th>Código</th><th>Título</th><th>Precio</th><th>Activa</th></tr>
        """
        
        for p in properties:
            html += f"""
                <tr>
                    <td>{p.id}</td>
                    <td>{p.code}</td>
                    <td>{p.title or 'Sin título'}</td>
                    <td>{p.price if p.price else 'Sin precio'}</td>
                    <td>{'✓' if p.is_active else '✗'}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"<h1>Error:</h1><p>{str(e)}</p>", status=500)

# Vista simple para mostrar todas las propiedades activas en tarjetas básicas
class SimplePropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = 'properties/simple_property_list.html'
    context_object_name = 'properties'
    paginate_by = None

    def get_queryset(self):
        # Mostrar todas las propiedades, aunque tengan datos incompletos
        return Property.objects.all().order_by('-created_at')
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
        queryset = (
            Property.objects.filter(is_active=True)
            .select_related('property_type', 'status', 'owner', 'created_by', 'currency')
            .prefetch_related('images')
            .only('id', 'code', 'title', 'price', 'coordinates', 'exact_address', 'district', 
                  'real_address', 'is_active', 'created_at', 'property_type_id', 'status_id', 
                  'owner_id', 'created_by_id', 'currency_id')
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
        # Cachear las listas para evitar queries adicionales
        context['property_types'] = PropertyType.objects.filter(is_active=True).order_by('name')
        context['statuses'] = PropertyStatus.objects.filter(is_active=True).order_by('order')
        # Obtener departamentos de las propiedades ya cargadas en memoria
        context['departments_list'] = sorted(set(
            p.department for p in properties if p.department
        ))

        context['filters'] = {
            'search': self.request.GET.get('search', '').strip(),
            'property_type': self.request.GET.get('property_type', '').strip(),
            'status': self.request.GET.get('status', '').strip(),
            'department': self.request.GET.get('department', '').strip(),
            'price_min': self.request.GET.get('price_min', '').strip(),
            'price_max': self.request.GET.get('price_max', '').strip(),
        }

        markers = []
        for property_obj in properties[:50]:  # Limitar a 50 propiedades por página
            lat = lng = None
            if property_obj.coordinates:
                parts = [p.strip() for p in property_obj.coordinates.split(',') if p.strip()]
                if len(parts) == 2:
                    try:
                        lat = float(parts[0])
                        lng = float(parts[1])
                    except ValueError:
                        lat = lng = None

            first_image_url = ''
            images_qs = list(property_obj.images.all())
            if images_qs:
                first_image = images_qs[0]
                if first_image and first_image.image:
                    first_image_url = first_image.image.url

            markers.append({
                'id': property_obj.id,
                'title': property_obj.title,
                'code': property_obj.code,
                'property_type': property_obj.property_type.name if property_obj.property_type else '',
                'status': property_obj.status.name if property_obj.status else '',
                'price': f"{property_obj.currency.symbol if property_obj.currency else ''} {format(property_obj.price, ',.2f')}",
                'address': property_obj.exact_address or property_obj.district or 'Ubicación no disponible',
                'real_address': property_obj.real_address or '',
                'lat': lat,
                'lng': lng,
                'url': reverse('properties:detail', kwargs={'pk': property_obj.pk}),
                'owner': property_obj.owner.full_name() if hasattr(property_obj.owner, 'full_name') else str(property_obj.owner),
                'created': property_obj.created_at.strftime('%d/%m/%Y'),
                'thumbnail': first_image_url,
            })

        context['property_markers'] = markers

        marker_icon_url = getattr(settings, 'PROPERTY_MARKER_ICON_URL', '').strip()
        if not marker_icon_url:
            marker_icon_static_path = getattr(settings, 'PROPERTY_MARKER_ICON_STATIC_PATH', '').strip()
            if marker_icon_static_path:
                marker_icon_url = static(marker_icon_static_path)

        context['property_marker_icon_url'] = marker_icon_url
        context['property_count'] = len(properties)

        return context

    

# ===================== VISTA FUNCIONAL PARA CREAR PROPIEDAD =====================
@login_required
def create_property_view(request):
    from .models import (
        PropertyType, PropertyStatus, PropertyOwner,
        Department, LevelType, RoomType, FloorType,
        PropertyImage, PropertyVideo, PropertyDocument, PropertyRoom,
        ImageType, VideoType, DocumentType
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
        if form.is_valid() and owner_form.is_valid():
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

            # Solo guardar información financiera si el formulario es válido y tiene datos
            if financial_form.is_valid() and any(financial_form.cleaned_data.values()):
                financial_info = financial_form.save(commit=False)
                financial_info.property = property_obj
                financial_info.save()

            # ===================== PROCESAR IMÁGENES =====================
            images_files = request.FILES.getlist('images')
            image_types = request.POST.getlist('image_types')
            image_captions = request.POST.getlist('image_captions')
            image_orders = request.POST.getlist('image_orders')
            
            primary_image_set = False
            for idx, image_file in enumerate(images_files):
                if image_file:
                    try:
                        image_type_id = image_types[idx] if idx < len(image_types) and image_types[idx] else None
                        image_type = ImageType.objects.get(pk=image_type_id) if image_type_id else None
                    except (ImageType.DoesNotExist, ValueError):
                        image_type = None
                    
                    try:
                        order = int(image_orders[idx]) if idx < len(image_orders) and image_orders[idx] else idx + 1
                    except ValueError:
                        order = idx + 1
                    
                    caption = image_captions[idx] if idx < len(image_captions) else ''
                    is_primary = not primary_image_set
                    
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        image_type=image_type,
                        caption=caption,
                        order=order,
                        is_primary=is_primary,
                        uploaded_by=request.user
                    )
                    primary_image_set = True

            # ===================== PROCESAR VIDEOS =====================
            videos_files = request.FILES.getlist('videos')
            video_types = request.POST.getlist('video_types')
            video_titles = request.POST.getlist('video_titles')
            video_descriptions = request.POST.getlist('video_descriptions')
            
            for idx, video_file in enumerate(videos_files):
                if video_file:
                    try:
                        video_type_id = video_types[idx] if idx < len(video_types) and video_types[idx] else None
                        video_type = VideoType.objects.get(pk=video_type_id) if video_type_id else None
                    except (VideoType.DoesNotExist, ValueError):
                        video_type = None
                    
                    title = video_titles[idx] if idx < len(video_titles) else f'Video {idx + 1}'
                    description = video_descriptions[idx] if idx < len(video_descriptions) else ''
                    
                    PropertyVideo.objects.create(
                        property=property_obj,
                        video=video_file,
                        video_type=video_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )

            # ===================== PROCESAR DOCUMENTOS =====================
            documents_files = request.FILES.getlist('documents')
            document_types = request.POST.getlist('document_types')
            document_titles = request.POST.getlist('document_titles')
            document_descriptions = request.POST.getlist('document_descriptions')
            
            for idx, document_file in enumerate(documents_files):
                if document_file:
                    try:
                        doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                        doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                    except (DocumentType.DoesNotExist, ValueError):
                        doc_type = None
                    
                    title = document_titles[idx] if idx < len(document_titles) else f'Documento {idx + 1}'
                    description = document_descriptions[idx] if idx < len(document_descriptions) else ''
                    
                    PropertyDocument.objects.create(
                        property=property_obj,
                        file=document_file,
                        document_type=doc_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )

            # ===================== PROCESAR HABITACIONES =====================
            room_levels = request.POST.getlist('room_levels')
            room_types_list = request.POST.getlist('room_types')
            room_names = request.POST.getlist('room_names')
            room_widths = request.POST.getlist('room_widths')
            room_lengths = request.POST.getlist('room_lengths')
            room_areas = request.POST.getlist('room_areas')
            room_floor_types = request.POST.getlist('room_floor_types')
            room_descriptions = request.POST.getlist('room_descriptions')
            room_orders = request.POST.getlist('room_orders')
            
            for idx in range(len(room_types_list)):
                room_type_id = room_types_list[idx] if idx < len(room_types_list) and room_types_list[idx] else None
                if room_type_id:
                    try:
                        room_type = RoomType.objects.get(pk=room_type_id)
                    except RoomType.DoesNotExist:
                        continue
                    
                    try:
                        level_id = room_levels[idx] if idx < len(room_levels) and room_levels[idx] else None
                        level = LevelType.objects.get(pk=level_id) if level_id else None
                    except (LevelType.DoesNotExist, ValueError):
                        level = None
                    
                    try:
                        floor_type_id = room_floor_types[idx] if idx < len(room_floor_types) and room_floor_types[idx] else None
                        floor_type = FloorType.objects.get(pk=floor_type_id) if floor_type_id else None
                    except (FloorType.DoesNotExist, ValueError):
                        floor_type = None
                    
                    try:
                        width = float(room_widths[idx]) if idx < len(room_widths) and room_widths[idx] else 0
                    except ValueError:
                        width = 0
                    
                    try:
                        length = float(room_lengths[idx]) if idx < len(room_lengths) and room_lengths[idx] else 0
                    except ValueError:
                        length = 0
                    
                    try:
                        area = float(room_areas[idx]) if idx < len(room_areas) and room_areas[idx] else 0
                    except ValueError:
                        area = 0
                    
                    try:
                        order = int(room_orders[idx]) if idx < len(room_orders) and room_orders[idx] else idx
                    except ValueError:
                        order = idx
                    
                    name = room_names[idx] if idx < len(room_names) else ''
                    description = room_descriptions[idx] if idx < len(room_descriptions) else ''
                    
                    PropertyRoom.objects.create(
                        property=property_obj,
                        level=level,
                        room_type=room_type,
                        name=name,
                        width=width,
                        length=length,
                        area=area,
                        floor_type=floor_type,
                        description=description,
                        order=order
                    )

            from django.contrib import messages
            messages.success(request, 'Propiedad creada exitosamente con imágenes, videos, documentos y ambientes.')
            from django.urls import reverse
            return redirect(reverse('properties:list'))

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


@login_required
def edit_property_view(request, pk):
    """Vista para editar una propiedad existente con toda la estructura del create."""
    from .models import (
        PropertyType, PropertyStatus, PropertyOwner,
        Department, LevelType, RoomType, FloorType,
        PropertyImage, PropertyVideo, PropertyDocument, PropertyRoom,
        ImageType, VideoType, DocumentType, PropertyFinancialInfo
    )
    from .forms import PropertyForm, PropertyOwnerForm, PropertyFinancialInfoForm
    
    # Obtener la propiedad a editar
    property_obj = get_object_or_404(Property, pk=pk)
    
    # Listas para selects
    departments = Department.objects.filter(is_active=True).order_by('name')
    level_types = LevelType.objects.filter(is_active=True).order_by('name')
    room_types = RoomType.objects.filter(is_active=True).order_by('name')
    floor_types = FloorType.objects.filter(is_active=True).order_by('name')
    rooms = PropertyRoom.objects.filter(property=property_obj).order_by('order')
    existing_images = PropertyImage.objects.filter(property=property_obj).order_by('order')
    existing_videos = PropertyVideo.objects.filter(property=property_obj)
    existing_documents = PropertyDocument.objects.filter(property=property_obj)
    
    # Obtener información financiera si existe
    try:
        financial_info = PropertyFinancialInfo.objects.get(property=property_obj)
    except PropertyFinancialInfo.DoesNotExist:
        financial_info = None
    
    owner_form = PropertyOwnerForm(request.POST or None, instance=property_obj.owner if request.method == 'GET' else None)
    financial_form = PropertyFinancialInfoForm(request.POST or None, instance=financial_info)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=property_obj)
    
    if request.method == 'POST':
        if form.is_valid() and owner_form.is_valid():
            # Actualizar propietario (siempre el mismo, pero permitir cambios)
            owner = owner_form.save(commit=False)
            owner.created_by = request.user
            owner.save()
            owner_form.save_m2m()
            
            # Actualizar propiedad
            property_obj = form.save(commit=False)
            property_obj.owner = owner
            property_obj.save()
            form.save_m2m()
            
            # Actualizar información financiera si es válida
            if financial_form.is_valid() and any(financial_form.cleaned_data.values()):
                financial_info_obj = financial_form.save(commit=False)
                financial_info_obj.property = property_obj
                financial_info_obj.save()
            
            from django.contrib import messages
            messages.success(request, 'Propiedad actualizada exitosamente.')
            from django.urls import reverse
            return redirect(reverse('properties:detail', kwargs={'pk': property_obj.pk}))
    
    # Preparar datos de ubicación preseleccionados
    context = {
        'form': form,
        'owner_form': owner_form,
        'financial_form': financial_form,
        'departments': departments,
        'level_types': level_types,
        'room_types': room_types,
        'floor_types': floor_types,
        'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('-created_at'),
        'is_editing': True,
        'rooms': rooms,
        'existing_images': existing_images,
        'existing_videos': existing_videos,
        'existing_documents': existing_documents,
        'selected_department_id': property_obj.department or '',
        'selected_department_name': '',
        'selected_province_id': '',
        'selected_province_name': '',
        'selected_district_id': '',
        'selected_district_name': '',
        'selected_urbanization_id': '',
        'selected_urbanization_name': '',
    }
    
    return render(request, 'properties/property_edit.html', context)


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


from django.http import JsonResponse
from .models import DocumentType

@login_required
def api_document_types(request):
    """API que devuelve los tipos de documento en formato JSON."""
    tipos = DocumentType.objects.filter().values('id', 'name')
    return JsonResponse(list(tipos), safe=False)


from django.http import JsonResponse
from .models import ImageType

@login_required
def api_image_types(request):
    tipos = ImageType.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(tipos), safe=False)

from .models import RoomType

@login_required
def api_roomtypes(request):
    ambientes = RoomType.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(ambientes), safe=False)

from .models import VideoType

@login_required
def api_video_types(request):
    tipos = VideoType.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse(list(tipos), safe=False)
