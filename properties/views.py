from .models import Property
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
# Vista para borrar borrador
from django.views.decorators.http import require_POST


def get_visible_fields_for_user(user):
    """
    Obtiene los campos visibles para un usuario basado en su rol y los permisos configurados.
    Retorna un diccionario con {field_name: {'can_view': bool, 'can_edit': bool}}
    """
    from users.models import RoleFieldPermission
    
    visible_fields = {}
    
    if user.role:
        # Obtener permisos configurados para este rol
        permissions = RoleFieldPermission.objects.filter(role=user.role).values(
            'field_name', 'can_view', 'can_edit'
        )
        
        for perm in permissions:
            visible_fields[perm['field_name']] = {
                'can_view': perm['can_view'],
                'can_edit': perm['can_edit']
            }
    
    # Si no hay permisos específicos, todos los campos son visibles por defecto
    return visible_fields


@login_required
@require_POST
def delete_draft_view(request, pk):
    from .models import Property
    try:
        draft = Property.objects.get(pk=pk, created_by=request.user, is_active=False)
        draft.delete()
        from django.contrib import messages
        messages.success(request, 'Borrador eliminado correctamente.')
    except Property.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'No se encontró el borrador o no tienes permiso para borrarlo.')
    return HttpResponseRedirect(reverse('properties:drafts'))
from django.http import HttpResponse

# Vista ULTRA SIMPLE sin templates - SOLO HTML PURO
def simple_properties_view(request):
    """Vista que devuelve HTML puro con las propiedades."""
    try:
        properties = Property.objects.filter(is_active=True).order_by('-created_at')
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
        # Mostrar solo propiedades activas (no borradores)
        return Property.objects.filter(is_active=True).order_by('-created_at')
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

# ...existing code...

def track_whatsapp_click(request, link_id):
    """Registra un clic UTM y redirige al chat de WhatsApp."""
    from .models import PropertyWhatsAppLink, UTMClick
    link = get_object_or_404(PropertyWhatsAppLink, id=link_id, is_active=True)

    # Extraer posibles UTM desde el link
    utm_source = link.utm_source or ''
    utm_medium = link.utm_medium or ''
    utm_campaign = link.utm_campaign or ''
    utm_content = link.utm_content or ''

    # Datos de request
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    referer = request.META.get('HTTP_REFERER', '')
    ip_address = request.META.get('REMOTE_ADDR', '')

    # phone_number no se conoce aún en clic, se llena en webhook; se deja vacío
    UTMClick.objects.create(
        whatsapp_link=link,
        tracking_id=link.unique_identifier,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        utm_content=utm_content,
        user_agent=user_agent,
        referer=referer,
        ip_address=ip_address,
    )

    # Redirigir a WhatsApp
    return redirect(link.get_whatsapp_url())
from .forms import PropertyOwnerForm
from .models import PropertyOwner
from django.views.generic import ListView, CreateView, DetailView
from django.db.models import Q

# Vista para detalle de contacto
class ContactDetailView(LoginRequiredMixin, DetailView):
    model = PropertyOwner
    template_name = 'properties/contact_detail.html'
    context_object_name = 'contact'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.get_object()
        context['created_by_user'] = contact.created_by
        context['created_at'] = contact.created_at
        return context

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
        # Añadir videos, documentos y datos financieros al contexto para la plantilla
        property_obj = self.get_object()
        # Si el objeto es un borrador, sólo el creador o superuser pueden verlo
        if property_obj.is_active is False and property_obj.created_by and property_obj.created_by != self.request.user and not self.request.user.is_superuser:
            raise Http404()
        # videos relacionados
        try:
            context['property_videos'] = list(property_obj.videos.all())
        except Exception:
            context['property_videos'] = []

        # documentos relacionados
        try:
            context['property_documents'] = list(property_obj.documents.all())
        except Exception:
            context['property_documents'] = []

        # información financiera (si existe) y items simplificados para la plantilla
        try:
            financial_info = getattr(property_obj, 'financial_info', None)
            context['financial_info'] = financial_info
            # preparar una lista simple de pares etiqueta/valor para la plantilla
            financial_items = []
            if financial_info:
                if financial_info.initial_commission_percentage is not None:
                    financial_items.append({'label': 'Comisión inicial', 'value': f"{financial_info.initial_commission_percentage}%"})
                if financial_info.final_commission_percentage is not None:
                    financial_items.append({'label': 'Comisión final', 'value': f"{financial_info.final_commission_percentage}%"})
                if financial_info.final_amount is not None:
                    financial_items.append({'label': 'Monto final', 'value': f"{financial_info.final_amount:,}"})
            context['financial_items'] = financial_items
        except Exception:
            context['financial_info'] = None
            context['financial_items'] = []

        # Agregar permisos de campos basados en el rol del usuario
        context['field_permissions'] = get_visible_fields_for_user(self.request.user)

        return context


@login_required
def property_timeline_view(request, pk):
    """Muestra la línea de tiempo de cambios de una propiedad."""
    property_obj = get_object_or_404(Property, pk=pk)
    # Obtener cambios relacionados
    changes = property_obj.changes.select_related('changed_by').all().order_by('-changed_at')
    return render(request, 'properties/property_timeline.html', {
        'property': property_obj,
        'changes': changes,
    })


@login_required
def drafts_list_view(request):
    """Listar borradores (propiedades creadas por el usuario con is_active=False)."""
    drafts = Property.objects.filter(created_by=request.user, is_active=False).order_by('-created_at')
    return render(request, 'properties/property_drafts.html', {
        'drafts': drafts,
    })


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
                'price': f"{property_obj.currency.symbol if property_obj.currency else ''} {format(round(property_obj.price), ',.0f')}",
                'address': property_obj.real_address or property_obj.exact_address or property_obj.district or 'Ubicación no disponible',
                'real_address': property_obj.real_address or '',
                'lat': lat,
                'lng': lng,
                'url': reverse('properties:detail', kwargs={'pk': property_obj.pk}),
                'owner': property_obj.owner.full_name() if hasattr(property_obj.owner, 'full_name') else str(property_obj.owner),
                'created': property_obj.created_at.strftime('%d/%m/%Y'),
                'thumbnail': first_image_url,
            })

            # Resolve textual names for location fields in case the Property stores numeric IDs
            def resolve_location_name(value, model_cls):
                if not value:
                    return ''
                try:
                    # if value looks like an integer id, try to resolve
                    if str(value).isdigit():
                        obj = model_cls.objects.filter(pk=int(value)).first()
                        if obj:
                            return getattr(obj, 'name', str(value))
                    # otherwise assume value already a name
                    return str(value)
                except Exception:
                    return str(value)

            # attach resolved display attributes to the property object for template use
            try:
                from .models import Province, District, Urbanization, Department
                property_obj.display_department = resolve_location_name(property_obj.department, Department)
                property_obj.display_province = resolve_location_name(property_obj.province, Province)
                property_obj.display_district = resolve_location_name(property_obj.district, District)
                property_obj.display_urbanization = resolve_location_name(property_obj.urbanization, Urbanization)
            except Exception:
                property_obj.display_department = property_obj.department or ''
                property_obj.display_province = property_obj.province or ''
                property_obj.display_district = property_obj.district or ''
                property_obj.display_urbanization = property_obj.urbanization or ''

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
        ImageType, VideoType, DocumentType, PropertyChange, PropertySubtype, Currency
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
        action = request.POST.get('action')
        # Si se solicita explícitamente guardar como borrador, NO validar los formularios
        if action == 'save_draft':
            draft = None
            draft_id = request.POST.get('draft_id')
            if draft_id:
                try:
                    draft = Property.objects.get(pk=int(draft_id), created_by=request.user, is_active=False)
                except Exception:
                    draft = None

            if draft is None:
                # obtener o crear objetos placeholder necesarios para campos obligatorios
                try:
                    prop_type = PropertyType.objects.filter(is_active=True).first()
                    if not prop_type:
                        prop_type = PropertyType.objects.create(name='(Borrador)')
                except Exception:
                    prop_type = None

                try:
                    prop_subtype = PropertySubtype.objects.filter(property_type=prop_type).first() if prop_type else None
                    if not prop_subtype and prop_type:
                        prop_subtype = PropertySubtype.objects.create(property_type=prop_type, name='(Borrador)')
                except Exception:
                    prop_subtype = None

                status = PropertyStatus.objects.filter(code='DRAFT').first()
                if not status:
                    try:
                        status = PropertyStatus.objects.create(name='Borrador', code='DRAFT')
                    except Exception:
                        status = PropertyStatus.objects.first()

                currency = Currency.objects.first()
                if not currency:
                    try:
                        currency = Currency.objects.create(code='PEN', name='Soles', symbol='S/')
                    except Exception:
                        currency = None

                # owner: prefer existing_owner if provided, else create placeholder (NO validación)
                owner = None
                existing_owner_id = request.POST.get('existing_owner')
                if existing_owner_id:
                    try:
                        owner = PropertyOwner.objects.get(pk=existing_owner_id)
                    except Exception:
                        owner = None
                if owner is None:
                    try:
                        owner = PropertyOwner.objects.create(created_by=request.user)
                    except Exception:
                        owner = None

                # generar código único temporal para el borrador
                import time
                code = f"DRAFT{request.user.id}{int(time.time())}"
                # crear borrador con valores mínimos
                draft_kwargs = {
                    'code': code,
                    'property_type': prop_type,
                    'property_subtype': prop_subtype,
                    'status': status,
                    'price': 0,
                    'currency': currency,
                    'owner': owner,
                    'created_by': request.user,
                    'is_active': False,
                }
                # intentar setear algunos campos opcionales desde POST
                for fld in ['title', 'description', 'exact_address', 'real_address', 'coordinates', 'department', 'province', 'district', 'urbanization']:
                    val = request.POST.get(fld)
                    if val:
                        draft_kwargs[fld] = val

                try:
                    draft = Property.objects.create(**draft_kwargs)
                except Exception:
                    draft = None

            # Si tenemos un borrador (nuevo o existente), guardar archivos subidos en él
            if draft is not None:
                # imágenes
                images_files = request.FILES.getlist('images')
                image_types = request.POST.getlist('image_types')
                image_captions = request.POST.getlist('image_captions')
                image_orders = request.POST.getlist('image_orders')
                for idx, image_file in enumerate(images_files):
                    if image_file:
                        try:
                            image_type_id = image_types[idx] if idx < len(image_types) and image_types[idx] else None
                            image_type = ImageType.objects.get(pk=image_type_id) if image_type_id else None
                        except Exception:
                            image_type = None
                        try:
                            order = int(image_orders[idx]) if idx < len(image_orders) and image_orders[idx] else idx + 1
                        except Exception:
                            order = idx + 1
                        caption = image_captions[idx] if idx < len(image_captions) else ''
                        try:
                            PropertyImage.objects.create(
                                property=draft,
                                image=image_file,
                                image_type=image_type,
                                caption=caption,
                                order=order,
                                uploaded_by=request.user
                            )
                        except Exception:
                            pass

                # videos
                videos_files = request.FILES.getlist('videos')
                video_types = request.POST.getlist('video_types')
                video_titles = request.POST.getlist('video_titles')
                video_descriptions = request.POST.getlist('video_descriptions')
                for idx, video_file in enumerate(videos_files):
                    if video_file:
                        try:
                            video_type_id = video_types[idx] if idx < len(video_types) and video_types[idx] else None
                            video_type = VideoType.objects.get(pk=video_type_id) if video_type_id else None
                        except Exception:
                            video_type = None
                        title = video_titles[idx] if idx < len(video_titles) else ''
                        description = video_descriptions[idx] if idx < len(video_descriptions) else ''
                        try:
                            PropertyVideo.objects.create(
                                property=draft,
                                video=video_file,
                                video_type=video_type,
                                title=title,
                                description=description,
                                uploaded_by=request.user
                            )
                        except Exception:
                            pass

                # documentos
                documents_files = request.FILES.getlist('documents')
                document_types = request.POST.getlist('document_types')
                document_titles = request.POST.getlist('document_titles')
                document_descriptions = request.POST.getlist('document_descriptions')
                for idx, document_file in enumerate(documents_files):
                    if document_file:
                        try:
                            doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                            doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                        except Exception:
                            doc_type = None
                        title = document_titles[idx] if idx < len(document_titles) else ''
                        description = document_descriptions[idx] if idx < len(document_descriptions) else ''
                        try:
                            PropertyDocument.objects.create(
                                property=draft,
                                file=document_file,
                                document_type=doc_type,
                                title=title,
                                description=description,
                                uploaded_by=request.user
                            )
                        except Exception:
                            pass

            # preparar contexto para re-renderizar el formulario con los recursos ya subidos
            contactos_existentes = PropertyOwner.objects.filter(is_active=True).order_by('-created_at')
            existing_images = list(PropertyImage.objects.filter(property=draft).order_by('order')) if draft else []
            existing_videos = list(PropertyVideo.objects.filter(property=draft)) if draft else []
            existing_documents = list(PropertyDocument.objects.filter(property=draft)) if draft else []
            draft_id_to_pass = draft.pk if draft else ''
            from django.contrib import messages
            messages.warning(request, 'Borrador guardado. Puedes continuar editando más tarde.')
            # Mostrar formulario vacío tras guardar borrador para evitar errores de validación
            return render(request, 'properties/property_create.html', {
                'form': PropertyForm(),
                'owner_form': PropertyOwnerForm(),
                'financial_form': PropertyFinancialInfoForm(),
                'departments': departments,
                'level_types': level_types,
                'room_types': room_types,
                'floor_types': floor_types,
                'contactos_existentes': contactos_existentes,
                'draft_id': draft_id_to_pass,
                'existing_images': existing_images,
                'existing_videos': existing_videos,
                'existing_documents': existing_documents,
            })
        # Validar form y owner_form según el caso
        existing_owner_id = request.POST.get('existing_owner')
        owner_form_valid = True
        
        if existing_owner_id:
            # Si hay propietario existente, no necesitamos validar owner_form
            owner_form_valid = True
        else:
            # Si se crea nuevo propietario, validar owner_form
            owner_form_valid = owner_form.is_valid()
        
        if form.is_valid() and owner_form_valid:
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
            property_obj.is_active = True  # Guardar como propiedad ACTIVA, no como borrador
            property_obj.save()
            form.save_m2m()

            # Registrar cambios iniciales al crear la propiedad (campos con valor)
            try:
                tracked_fields = ['title', 'price', 'coordinates', 'department', 'province', 'district', 'urbanization', 'exact_address', 'real_address']
                for field in tracked_fields:
                    val = getattr(property_obj, field, None)
                    if val not in (None, '', []):
                        PropertyChange.objects.create(
                            property=property_obj,
                            field=field,
                            old_value=None,
                            new_value=str(val),
                            changed_by=request.user
                        )
            except Exception:
                pass

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
                    
                    img = PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        image_type=image_type,
                        caption=caption,
                        order=order,
                        is_primary=is_primary,
                        uploaded_by=request.user
                    )
                    # Registrar evento de imagen subida
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field_name='image',
                            old_value=None,
                            new_value=f"Imagen subida: {img.caption or img.image.name}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass
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
                    description = video_descriptions[idx] if idx < len(video_descripciones) else ''
                    
                    vid = PropertyVideo.objects.create(
                        property=property_obj,
                        video=video_file,
                        video_type=video_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field='video',
                            old_value=None,
                            new_value=f"Video subido: {vid.title}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass

            # ===================== PROCESAR DOCUMENTOS =====================
            documents_files = request.FILES.getlist('documents')
            document_types = request.POST.getlist('document_types')
            document_titles = request.POST.getlist('document_titles')
            document_descriptions = request.POST.getlist('document_descripciones')
            
            for idx, document_file in enumerate(documents_files):
                if document_file:
                    try:
                        doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                        doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                    except (DocumentType.DoesNotExist, ValueError):
                        doc_type = None
                    
                    title = document_titles[idx] if idx < len(document_titles) else f'Documento {idx + 1}'
                    description = document_descriptions[idx] if idx < len(document_descripciones) else ''
                    
                    doc = PropertyDocument.objects.create(
                        property=property_obj,
                        file=document_file,
                        document_type=doc_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field='document',
                            old_value=None,
                            new_value=f"Documento subido: {doc.title}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass

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
                    description = room_descriptions[idx] if idx < len(room_descripciones) else ''
                    
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
        else:
            # Si la validación falla, simplemente re-renderizar el formulario con los errores, sin intentar crear borrador
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
        ImageType, VideoType, DocumentType, PropertyFinancialInfo, PropertyChange
    )
    from .forms import PropertyForm, PropertyOwnerForm, PropertyFinancialInfoForm
    
    # Obtener la propiedad a editar
    property_obj = get_object_or_404(Property, pk=pk)
    # Si es un borrador, sólo el creador (o superuser) puede acceder
    if property_obj.is_active is False and property_obj.created_by and property_obj.created_by != request.user and not request.user.is_superuser:
        raise Http404()
    
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
    
    # Always bind the owner form to the existing property owner instance
    owner_form = PropertyOwnerForm(request.POST or None, instance=property_obj.owner)
    financial_form = PropertyFinancialInfoForm(request.POST or None, instance=financial_info)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=property_obj)
    
    if request.method == 'POST':
        # Si el formulario viene indicando un propietario existente (hidden field),
        # preferimos usar ese propietario y no requerir la validación del owner_form.
        existing_owner_id = request.POST.get('existing_owner')
        owner_obj = None
        if existing_owner_id:
            try:
                owner_obj = PropertyOwner.objects.get(pk=existing_owner_id)
            except (PropertyOwner.DoesNotExist, ValueError):
                owner_obj = None

        # Validación condicional: si no hay owner_obj (p. ej. se enviaron campos de propietario),
        # entonces requerimos que owner_form sea válido. Si sí hay owner_obj, omitimos la validación
        # del owner_form y usamos el owner existente.
        owner_form_valid = True
        if owner_obj is None:
            owner_form_valid = owner_form.is_valid()

        if form.is_valid() and owner_form_valid:
            # Actualizar o usar propietario según corresponda
            if owner_obj is None:
                owner = owner_form.save(commit=False)
                # conservar created_by si existe, asignar sólo si es nuevo
                if not owner.pk:
                    owner.created_by = request.user
                owner.save()
                owner_form.save_m2m()
            else:
                owner = owner_obj

            # Actualizar propiedad
            # capturar estado previo para comparar
            try:
                previous = Property.objects.get(pk=property_obj.pk)
            except Exception:
                previous = None

            property_obj = form.save(commit=False)
            # Preservar is_active del valor anterior para evitar que se setee a False
            if previous:
                property_obj.is_active = previous.is_active
            property_obj.owner = owner
            property_obj.save()
            form.save_m2m()

            # Comparar campos rastreados y crear registros de cambio
            try:
                tracked_fields = ['title', 'price', 'coordinates', 'department', 'province', 'district', 'urbanization', 'exact_address', 'real_address', 
                                'bedrooms', 'bathrooms', 'built_area', 'land_area', 'property_type', 'status', 'description']
                if previous:
                    for field in tracked_fields:
                        old_val = getattr(previous, field, None)
                        new_val = getattr(property_obj, field, None)
                        if (old_val is None and new_val) or (old_val and str(old_val) != str(new_val)):
                            try:
                                PropertyChange.objects.create(
                                    property=property_obj,
                                    field=field,
                                    old_value=str(old_val) if old_val is not None else None,
                                    new_value=str(new_val) if new_val is not None else None,
                                    changed_by=request.user
                                )
                            except Exception:
                                pass
            except Exception:
                pass

            # Procesar posibles archivos subidos desde el formulario de edición (imágenes/videos/documentos)
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
                    img = PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        image_type=image_type,
                        caption=caption,
                        order=order,
                        is_primary=is_primary,
                        uploaded_by=request.user
                    )
                    primary_image_set = True
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field_name='image',
                            old_value=None,
                            new_value=f"Imagen subida: {img.caption or img.image.name}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass

            # Videos
            videos_files = request.FILES.getlist('videos')
            video_types = request.POST.getlist('video_types')
            video_titles = request.POST.getlist('video_titles')
            video_descriptions = request.POST.getlist('video_descripciones')
            for idx, video_file in enumerate(videos_files):
                if video_file:
                    try:
                        video_type_id = video_types[idx] if idx < len(video_types) and video_types[idx] else None
                        video_type = VideoType.objects.get(pk=video_type_id) if video_type_id else None
                    except (VideoType.DoesNotExist, ValueError):
                        video_type = None
                    
                    title = video_titles[idx] if idx < len(video_titles) else f'Video {idx + 1}'
                    description = video_descriptions[idx] if idx < len(video_descripciones) else ''
                    vid = PropertyVideo.objects.create(
                        property=property_obj,
                        video=video_file,
                        video_type=video_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field='video',
                            old_value=None,
                            new_value=f"Video subido: {vid.title}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass

            # Documentos
            documents_files = request.FILES.getlist('documents')
            document_types = request.POST.getlist('document_types')
            document_titles = request.POST.getlist('document_titles')
            document_descriptions = request.POST.getlist('document_descripciones')
            for idx, document_file in enumerate(documents_files):
                if document_file:
                    try:
                        doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                        doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                    except (DocumentType.DoesNotExist, ValueError):
                        doc_type = None
                    
                    title = document_titles[idx] if idx < len(document_titles) else f'Documento {idx + 1}'
                    description = document_descriptions[idx] if idx < len(document_descripciones) else ''
                    doc = PropertyDocument.objects.create(
                        property=property_obj,
                        file=document_file,
                        document_type=doc_type,
                        title=title,
                        description=description,
                        uploaded_by=request.user
                    )
                    try:
                        PropertyChange.objects.create(
                            property=property_obj,
                            field='document',
                            old_value=None,
                            new_value=f"Documento subido: {doc.title}",
                            changed_by=request.user
                        )
                    except Exception:
                        pass

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
        # Note: Property stores department/province/district/urbanization as text fields.
        # Provide both id and name placeholders to the template. Prefer passing the saved
        # names so the client-side selects show the stored location when IDs are not available.
        # If the stored value is numeric (an id), pass it as _id; otherwise pass it as _name
        'selected_department_id': property_obj.department if (property_obj.department and str(property_obj.department).isdigit()) else '',
        'selected_department_name': '' if (property_obj.department and str(property_obj.department).isdigit()) else (property_obj.department or ''),
        'selected_province_id': property_obj.province if (property_obj.province and str(property_obj.province).isdigit()) else '',
        'selected_province_name': '' if (property_obj.province and str(property_obj.province).isdigit()) else (property_obj.province or ''),
        'selected_district_id': property_obj.district if (property_obj.district and str(property_obj.district).isdigit()) else '',
        'selected_district_name': '' if (property_obj.district and str(property_obj.district).isdigit()) else (property_obj.district or ''),
        'selected_urbanization_id': property_obj.urbanization if (property_obj.urbanization and str(property_obj.urbanization).isdigit()) else '',
        'selected_urbanization_name': '' if (property_obj.urbanization and str(property_obj.urbanization).isdigit()) else (property_obj.urbanization or ''),
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


# ============================================================================
# VISTAS PARA INTEGRACIÓN CON WHATSAPP
# ============================================================================

@login_required
def marketing_properties_list(request):
    """Lista propiedades para gestión de Marketing/UTMs"""
    properties = Property.objects.filter(is_active=True).select_related(
        'currency'
    ).prefetch_related('whatsapp_links').order_by('-created_at')
    
    return render(request, 'properties/marketing_properties_list.html', {
        'properties': properties
    })


@login_required
def whatsapp_links_list(request, property_id):
    """Lista los enlaces de WhatsApp para una propiedad"""
    from django.views.generic.detail import SingleObjectMixin
    
    property_obj = get_object_or_404(Property, id=property_id)
    links = property_obj.whatsapp_links.all()
    
    return render(request, 'properties/whatsapp_links_list.html', {
        'property': property_obj,
        'links': links,
    })


@login_required
def whatsapp_link_create(request, property_id):
    """Crea un nuevo enlace de WhatsApp para una propiedad"""
    import secrets
    import string
    
    property_obj = get_object_or_404(Property, id=property_id)
    
    if request.method == 'POST':
        from .models import PropertyWhatsAppLink
        
        # Generar identificador único si no existe
        from .models import SocialNetwork
        social_network_id = request.POST.get('social_network')
        social_network = SocialNetwork.objects.get(pk=social_network_id)
        link_name = request.POST.get('link_name')
        whatsapp_number_value = request.POST.get('whatsapp_phone_id')
        from .models import WhatsAppNumber
        # Buscar o crear el número de WhatsApp
        whatsapp_number, _ = WhatsAppNumber.objects.get_or_create(number=whatsapp_number_value, defaults={
            'display_name': whatsapp_number_value,
            'is_active': True
        })

        # Generar ID único
        while True:
            unique_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            if not PropertyWhatsAppLink.objects.filter(unique_identifier=unique_id).exists():
                break

        link = PropertyWhatsAppLink.objects.create(
            property=property_obj,
            social_network=social_network,
            link_name=link_name,
            whatsapp_number=whatsapp_number,
            unique_identifier=unique_id,
            utm_source=social_network.name if hasattr(social_network, 'name') else '',
            utm_campaign=link_name,
            created_by=request.user
        )
        
        return redirect('properties:whatsapp_links', property_id=property_id)
    
    from .models import SocialNetwork
    social_networks = SocialNetwork.objects.filter(is_active=True)
    
    return render(request, 'properties/whatsapp_link_form.html', {
        'property': property_obj,
        'social_networks': social_networks,
    })


@login_required
def whatsapp_link_delete(request, link_id):
    """Elimina un enlace de WhatsApp"""
    from .models import PropertyWhatsAppLink
    
    link = get_object_or_404(PropertyWhatsAppLink, id=link_id)
    property_id = link.property.id
    
    if request.method == 'POST':
        link.delete()
        return redirect('properties:whatsapp_links', property_id=property_id)
    
    return render(request, 'properties/whatsapp_link_confirm_delete.html', {
        'link': link,
    })


@login_required
def leads_list(request, property_id=None):
    """Lista los leads de WhatsApp"""
    from .models import Lead, LeadStatus
    
    leads = Lead.objects.select_related('property', 'whatsapp_link', 'assigned_to', 'status')
    
    if property_id:
        leads = leads.filter(property_id=property_id)
    
    # Filtros
    status = request.GET.get('status')
    if status:
        leads = leads.filter(status_id=status)
    
    social_network = request.GET.get('social_network')
    if social_network:
        leads = leads.filter(social_network=social_network)
    
    # Obtener estados para el filtro (de todas las propiedades o de la propiedad específica)
    if property_id:
        status_choices = LeadStatus.objects.filter(property_id=property_id, is_active=True).order_by('order')
    else:
        status_choices = LeadStatus.objects.filter(is_active=True).order_by('property', 'order')
    
    return render(request, 'properties/leads_list.html', {
        'leads': leads,
        'status_choices': status_choices,
    })


@login_required
def lead_detail(request, lead_id):
    """Detalle de un lead con conversaciones"""
    from .models import Lead, WhatsAppConversation
    
    lead = get_object_or_404(Lead, id=lead_id)
    conversations = WhatsAppConversation.objects.filter(lead=lead).order_by('created_at')
    
    if request.method == 'POST':
        # Actualizar estado o asignar
        from .models import LeadStatus
        status_id = request.POST.get('status')
        assigned_to = request.POST.get('assigned_to')
        
        if status_id:
            try:
                lead.status = LeadStatus.objects.get(id=status_id, property=lead.property)
            except LeadStatus.DoesNotExist:
                pass
        
        if assigned_to:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            lead.assigned_to = User.objects.get(id=assigned_to) if assigned_to else None
        
        lead.save()
        return redirect('properties:lead_detail', lead_id=lead_id)
    
    # Obtener los estados personalizados de la propiedad
    status_choices = lead.property.lead_statuses.filter(is_active=True).order_by('order')
    
    return render(request, 'properties/lead_detail.html', {
        'lead': lead,
        'conversations': conversations,
        'status_choices': status_choices,
    })


@login_required
def crm_dashboard(request):
    """Dashboard CRM con estadísticas de leads y propiedades"""
    from .models import Lead, Property, PropertyWhatsAppLink
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    # Estadísticas generales
    total_properties = Property.objects.filter(is_active=True).count()
    total_links = PropertyWhatsAppLink.objects.filter(is_active=True).count()
    total_leads = Lead.objects.count()
    
    # Leads recientes (últimas 24 horas)
    last_24h = timezone.now() - timedelta(hours=24)
    recent_leads = Lead.objects.filter(first_message_at__gte=last_24h).count()
    
    # Leads por estado
    leads_by_status = Lead.objects.values('status').annotate(count=Count('id'))
    
    # Leads por red social
    leads_by_social = Lead.objects.values('social_network').annotate(count=Count('id'))
    
    # Leads sin asignar
    unassigned_leads = Lead.objects.filter(assigned_to__isnull=True)
    
    # Propiedades más activas (con más leads)
    top_properties = Property.objects.filter(whatsapp_leads__isnull=False).annotate(
        lead_count=Count('whatsapp_leads')
    ).order_by('-lead_count')[:5]
    
    # Últimos leads
    latest_leads = Lead.objects.select_related('property', 'assigned_to').order_by('-created_at')[:10]
    
    context = {
        'total_properties': total_properties,
        'total_links': total_links,
        'total_leads': total_leads,
        'recent_leads': recent_leads,
        'leads_by_status': leads_by_status,
        'leads_by_social': leads_by_social,
        'unassigned_leads': unassigned_leads,
        'unassigned_count': unassigned_leads.count(),
        'top_properties': top_properties,
        'latest_leads': latest_leads,
    }
    
    return render(request, 'properties/crm_dashboard.html', context)


@login_required
def crm_dashboard(request):
    """Dashboard principal del CRM"""
    from .models import Lead
    from django.utils import timezone
    from datetime import timedelta
    
    # Stats generales
    total_leads = Lead.objects.count()
    
    # Leads nuevos hoy
    today = timezone.now().date()
    new_today = Lead.objects.filter(created_at__date=today).count()
    
    # Leads en negociación
    negotiating_count = Lead.objects.filter(status__name='negotiating').count()
    
    # Leads sin asignar
    unassigned_count = Lead.objects.filter(assigned_to__isnull=True).count()
    
    # Leads recientes (últimos 10)
    recent_leads = Lead.objects.select_related(
        'property', 'assigned_to'
    ).order_by('-first_message_at')[:10]
    
    # Datos para gráficos
    from collections import Counter
    
    # Por red social
    social_networks = Lead.objects.values_list('social_network', flat=True)
    social_counter = Counter(social_networks)
    social_network_labels = [
        dict(Lead.SOCIAL_NETWORKS).get(key, key) 
        for key in social_counter.keys()
    ]
    social_network_data = list(social_counter.values())
    
    # Por estado
    statuses = Lead.objects.values_list('status', flat=True)
    status_counter = Counter(statuses)
    status_labels = [
        dict(Lead.STATUS_CHOICES).get(key, key) 
        for key in status_counter.keys()
    ]
    status_data = list(status_counter.values())
    
    import json
    context = {
        'total_leads': total_leads,
        'new_today': new_today,
        'negotiating_count': negotiating_count,
        'unassigned_count': unassigned_count,
        'recent_leads': recent_leads,
        'social_network_labels': json.dumps(social_network_labels),
        'social_network_data': json.dumps(social_network_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
    }
    
    return render(request, 'properties/crm_dashboard.html', context)

@login_required
def marketing_whatsapp_links_list(request):
    """Vista global para gestionar todos los enlaces UTM (PropertyWhatsAppLink)"""
    from .models import PropertyWhatsAppLink
    links = PropertyWhatsAppLink.objects.select_related('property').order_by('-created_at', 'property__code', 'social_network')
    return render(request, 'properties/marketing_whatsapp_links_list.html', {'links': links})

from django.db.models import Count
from .models import PropertyWhatsAppLink, Lead, SocialNetwork
from datetime import datetime, timedelta
import json

@login_required
def marketing_utm_dashboard(request):
    # Filtros
    start = request.GET.get('start')
    end = request.GET.get('end')
    social_network_id = request.GET.get('social_network')
    property_id = request.GET.get('property')
    utm_source = request.GET.get('utm_source')
    utm_campaign = request.GET.get('utm_campaign')
    today = datetime.now().date()
    if not start:
        start = today - timedelta(days=30)
    else:
        start = datetime.strptime(start, '%Y-%m-%d').date()
    if not end:
        end = today
    else:
        end = datetime.strptime(end, '%Y-%m-%d').date()

    # Usar UTMClick para estadísticas de clics UTM (tracking de campañas)
    from .models import UTMClick, Property
    # Limpiar cualquier ordenación por defecto del modelo para evitar errores en GROUP BY
    clicks = UTMClick.objects.filter(created_at__date__gte=start, created_at__date__lte=end).order_by()

    # Si se desea filtrar por red social, derivar por el whatsapp_link.social_network
    if social_network_id:
        clicks = clicks.filter(whatsapp_link__social_network_id=social_network_id)
    if property_id:
        clicks = clicks.filter(whatsapp_link__property_id=property_id)

    # Filtros por UTM
    if utm_source:
        clicks = clicks.filter(utm_source=utm_source)
    if utm_campaign:
        clicks = clicks.filter(utm_campaign=utm_campaign)

    # Estadísticas por día (SQL Server compatible)
    # Ajuste de zona horaria (America/Lima UTC-5) para agrupar por día local
    # Convertir de UTC a hora local de Lima usando AT TIME ZONE (SQL Server)
    # 'SA Pacific Standard Time' corresponde a America/Lima sin DST
    table_name = UTMClick._meta.db_table
    clicks_by_day = clicks.extra({'day': f"CAST(({table_name}.[created_at] AT TIME ZONE 'UTC' AT TIME ZONE 'SA Pacific Standard Time') AS DATE)"}).values('day').annotate(count=Count('id')).order_by('day')
    leads_by_day_labels = [str(row['day']) for row in clicks_by_day]
    leads_by_day_data = [row['count'] for row in clicks_by_day]

    # Estadísticas por hora
    # Ajuste de zona horaria para hora local
    clicks_by_hour = clicks.extra({'hour': f"DATEPART(hour, ({table_name}.[created_at] AT TIME ZONE 'UTC' AT TIME ZONE 'SA Pacific Standard Time'))"}).values('hour').annotate(count=Count('id')).order_by('hour')
    leads_by_hour_labels = [str(row['hour']) for row in clicks_by_hour]
    leads_by_hour_data = [row['count'] for row in clicks_by_hour]

    # Horas punta (top 5 horas con más clics)
    peak_hours = sorted([
        {'hour': int(row['hour']), 'count': int(row['count'])}
        for row in clicks_by_hour
    ], key=lambda x: x['count'], reverse=True)[:5]

    # Estadísticas por semana
    # Ajuste de zona horaria para semana local
    clicks_by_week = clicks.extra({'week': f"DATEPART(week, ({table_name}.[created_at] AT TIME ZONE 'UTC' AT TIME ZONE 'SA Pacific Standard Time'))"}).values('week').annotate(count=Count('id')).order_by('week')
    leads_by_week_labels = [str(row['week']) for row in clicks_by_week]
    leads_by_week_data = [row['count'] for row in clicks_by_week]

    # Heatmap Día/Hora (local): matriz de 7x24 con conteos
    clicks_day_hour = clicks.extra({
        'dow': f"DATEPART(weekday, ({table_name}.[created_at] AT TIME ZONE 'UTC' AT TIME ZONE 'SA Pacific Standard Time'))",
        'hour': f"DATEPART(hour, ({table_name}.[created_at] AT TIME ZONE 'UTC' AT TIME ZONE 'SA Pacific Standard Time'))",
    }).values('dow', 'hour').annotate(count=Count('id'))

    # Normalizar a índices 0-6 (Lunes=0) y 0-23
    # En SQL Server, por defecto DATEPART(weekday) depende de SET DATEFIRST; asumimos Domingo=1.
    # Convertimos: 1->6 (Domingo), 2->0 (Lunes), ..., 7->5 (Sábado)
    def map_weekday(d):
        # Domingo=1 -> 6; Lunes=2 -> 0; Martes=3 -> 1; ...; Sábado=7 -> 5
        return (d + 5) % 7

    heatmap_matrix = [[0 for _ in range(24)] for _ in range(7)]
    for row in clicks_day_hour:
        dow = map_weekday(int(row['dow']))
        hour = int(row['hour'])
        heatmap_matrix[dow][hour] = int(row['count'])

    heatmap_days = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    social_networks = SocialNetwork.objects.filter(is_active=True)
    # Lista de propiedades con publicidad (al menos un WhatsApp link asociado), orden alfabético por dirección
    try:
        properties_list = (
            Property.objects.filter(is_active=True, whatsapp_links__isnull=False)
            .distinct()
            .order_by('real_address')
        )
    except Exception:
        properties_list = (
            Property.objects.filter(whatsapp_links__isnull=False)
            .distinct()
            .order_by('real_address')
        )

    # Totales y desglose por fuente
    total_clicks = clicks.count()
    source_counts_qs = clicks.values('utm_source').annotate(count=Count('id')).order_by('-count')
    source_counts = [{'utm_source': row['utm_source'] or 'N/A', 'count': row['count']} for row in source_counts_qs]

    # Estadísticas por propiedad (usando real_address) y desglose por red social
    property_clicks_qs = clicks.values(
        'whatsapp_link__property__real_address'
    ).annotate(total=Count('id')).order_by('-total')

    # Desglose por red: counts por (property, social_network)
    property_network_qs = clicks.values(
        'whatsapp_link__property__real_address',
        'whatsapp_link__social_network__name'
    ).annotate(count=Count('id'))

    # Construir mapa: {address: {network_name: count, ..., total: N}}
    property_stats = {}
    for row in property_clicks_qs:
        addr = row['whatsapp_link__property__real_address'] or 'Sin dirección'
        property_stats[addr] = {'total': row['total']}
    for row in property_network_qs:
        addr = row['whatsapp_link__property__real_address'] or 'Sin dirección'
        net = row['whatsapp_link__social_network__name'] or 'N/A'
        property_stats.setdefault(addr, {'total': 0})
        property_stats[addr][net] = row['count']

    # KPI: ratio de clics por propiedad vs total global
    for addr, stats in property_stats.items():
        stats['ratio'] = (stats['total'] / total_clicks) if total_clicks else 0

    # Obtener listado único de redes para cabeceras
    network_names = list(
        clicks.values_list('whatsapp_link__social_network__name', flat=True)
        .distinct().order_by('whatsapp_link__social_network__name')
    )

    # Top 10 propiedades por clics
    top_properties = list(property_clicks_qs[:10])

    # Top 10 campañas (utm_campaign) por clics
    top_campaigns_qs = clicks.values('utm_campaign').annotate(total=Count('id')).order_by('-total')[:10]
    top_campaigns = [{'utm_campaign': row['utm_campaign'] or 'N/A', 'total': row['total']} for row in top_campaigns_qs]

    # Distribución por red (para pie chart)
    network_dist_qs = clicks.values('utm_source').annotate(total=Count('id')).order_by('-total')
    network_dist_labels = [row['utm_source'] or 'N/A' for row in network_dist_qs]
    network_dist_data = [row['total'] for row in network_dist_qs]

    context = {
        'start': start,
        'end': end,
        'social_networks': social_networks,
        'social_network_id': social_network_id or '',
        'properties_list': properties_list,
        'property_id': property_id or '',
        'utm_source': utm_source or '',
        'utm_campaign': utm_campaign or '',
        'leads_by_day_labels': json.dumps(leads_by_day_labels),
        'leads_by_day_data': json.dumps(leads_by_day_data),
        'leads_by_hour_labels': json.dumps(leads_by_hour_labels),
        'leads_by_hour_data': json.dumps(leads_by_hour_data),
        'leads_by_week_labels': json.dumps(leads_by_week_labels),
        'leads_by_week_data': json.dumps(leads_by_week_data),
        'total_clicks': total_clicks,
        'source_counts': source_counts,
        'property_stats': property_stats,
        'network_names': network_names,
        'peak_hours': peak_hours,
        'heatmap_matrix': heatmap_matrix,
        'heatmap_days': heatmap_days,
        'top_properties': top_properties,
        'top_campaigns': top_campaigns,
        'network_dist_labels': json.dumps(network_dist_labels),
        'network_dist_data': json.dumps(network_dist_data),
    }
    return render(request, 'properties/marketing_utm_dashboard.html', context)
