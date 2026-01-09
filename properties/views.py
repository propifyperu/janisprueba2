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
        # Asegurarse de borrar solo objetos marcados explícitamente como Borrador
        draft = Property.objects.get(pk=pk, created_by=request.user, is_active=False, is_draft=True)
        draft.delete()
        from django.contrib import messages
        messages.success(request, 'Borrador eliminado correctamente.')
    except Property.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'No se encontró el borrador o no tienes permiso para borrarlo.')
    return HttpResponseRedirect(reverse('properties:drafts'))
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required

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
from .models import Property, PropertyType, PropertyStatus, PropertyOwner, PropertySubtype, Requirement
from .forms import PropertyOwnerForm, RequirementForm
from .models import MatchingWeight
from . import matching as matching_module
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(["GET", "POST"])
def matching_weights_view(request):
    """Vista para listar y editar los pesos de matching (solo usuarios con permiso)."""
    if not request.user.is_superuser:
        return HttpResponse('Forbidden', status=403)

    if request.method == 'POST':
        # actualizar pesos desde el formulario
        for key, value in request.POST.items():
            if key.startswith('weight_'):
                k = key.replace('weight_', '')
                try:
                    mw = MatchingWeight.objects.get(key=k)
                    mw.weight = float(value)
                    mw.save()
                except MatchingWeight.DoesNotExist:
                    MatchingWeight.objects.create(key=k, weight=float(value or 1.0))
                except Exception:
                    pass
        # crear nuevo criterio si se envió
        new_key = request.POST.get('new_key', '').strip()
        new_weight = request.POST.get('new_weight', '').strip()
        if new_key:
            try:
                # validar formato básico
                if len(new_key) > 100 or not new_key.replace('_', '').isalnum():
                    from django.contrib import messages
                    messages.error(request, 'Clave inválida para el nuevo criterio.')
                else:
                    if MatchingWeight.objects.filter(key=new_key).exists():
                        from django.contrib import messages
                        messages.warning(request, f'El criterio "{new_key}" ya existe.')
                    else:
                        wval = float(new_weight) if new_weight else 1.0
                        MatchingWeight.objects.create(key=new_key, weight=wval)
                        from django.contrib import messages
                        messages.success(request, f'Nuevo criterio "{new_key}" creado con peso {wval}.')
            except Exception:
                from django.contrib import messages
                messages.error(request, 'No fue posible crear el nuevo criterio.')
        return redirect('properties:matching_weights')
        return redirect('properties:matching_weights')

    weights = MatchingWeight.objects.all().order_by('key')
    # Etiquetas en español para mostrar en el UI del selector (definidas antes de usarlas)
    MATCHING_KEY_LABELS = {
        'property_type': 'Tipo de propiedad',
        'property_subtype': 'Subtipo',
        'district': 'Distrito',
        'province': 'Provincia',
        'department': 'Departamento',
        'urbanization': 'Urbanización',
        'currency': 'Moneda',
        'price': 'Precio',
        'area': 'Área',
        'land_area': 'Área de terreno',
        'built_area': 'Área construida',
        'front_measure': 'Frontera',
        'depth_measure': 'Profundidad',
        'bedrooms': 'Dormitorios',
        'bathrooms': 'Baños',
        'half_bathrooms': 'Medios baños',
        'garage_spaces': 'Cochera (espacios)',
        'garage_type': 'Tipo de garaje',
        'parking_cost_included': 'Estacionamiento incluido',
        'parking_cost': 'Costo de estacionamiento',
        'amenities': 'Servicios / Amenidades',
        'tags': 'Etiquetas',
        'water_service': 'Servicio de agua',
        'energy_service': 'Servicio de energía',
        'drainage_service': 'Servicio de drenaje',
        'gas_service': 'Servicio de gas',
        'is_project': 'Proyecto (sí/no)',
        'project_name': 'Nombre de proyecto',
        'unit_location': 'Ubicación en unidad',
        'ascensor': 'Ascensor (sí/no)',
        'floors': 'Cantidad de pisos'
    }
    # Convertir a lista simple con etiqueta legible para facilitar el render en la plantilla
    weights_list = []
    for w in weights:
        weights_list.append({
            'key': w.key,
            'weight': w.weight,
            'label': MATCHING_KEY_LABELS.get(w.key, w.key)
        })
    # claves por defecto reconocidas por el motor de matching
    DEFAULT_MATCHING_KEYS = [
        'property_type', 'property_subtype', 'district', 'province', 'department', 'urbanization',
        'currency', 'price', 'area', 'land_area', 'built_area', 'front_measure', 'depth_measure',
        'bedrooms', 'bathrooms', 'half_bathrooms',
        'garage_spaces', 'garage_type', 'parking_cost_included', 'parking_cost',
        'amenities', 'tags',
        'water_service', 'energy_service', 'drainage_service', 'gas_service',
        'is_project', 'project_name', 'unit_location', 'ascensor', 'floors'
    ]
    
    existing = set(weights.values_list('key', flat=True))
    # Calcular solo las claves que existen en ambos modelos (Property y Requirement)
    try:
        prop_field_names = {f.name for f in Property._meta.get_fields()}
    except Exception:
        prop_field_names = set()
    try:
        req_field_names = {f.name for f in Requirement._meta.get_fields()}
    except Exception:
        req_field_names = set()

    # Construir lista de tuplas (key, label) con solo campos compartidos
    available_keys = []
    for k in DEFAULT_MATCHING_KEYS:
        if k in existing:
            continue
        if k in prop_field_names and k in req_field_names:
            label = MATCHING_KEY_LABELS.get(k, k)
            available_keys.append((k, label))
    return render(request, 'properties/matching_weights.html', {
        'weights': weights_list,
        'available_keys': available_keys,
    })


@login_required
def matching_matches_view(request, pk: int):
    """Mostrar coincidencias calculadas para un `Requirement` concreto."""
    req = get_object_or_404(Requirement, pk=pk)
    # manejar flags: only_matches (mostrar solo criterios que coinciden) y export=csv
    only_matches = bool(request.GET.get('only_matches'))
    export = request.GET.get('export')

    # calcular coincidencias
    results = matching_module.get_matches_for_requirement(req, limit=50)
    # cargar pesos por criterio para mostrar el valor máximo posible por criterio
    weights = matching_module._load_weights()

    # Añadir representación legible del valor de la propiedad para cada criterio
    for r in results:
        prop = r.get('property')
        details = r.get('details') or {}
        for k, v in details.items():
            try:
                if k == 'property_type':
                    pv = prop.property_type.name if getattr(prop, 'property_type', None) else '—'
                elif k == 'property_subtype':
                    pv = prop.property_subtype.name if getattr(prop, 'property_subtype', None) else '—'
                elif k == 'district':
                    pd = getattr(prop, 'district', None)
                    if not pd:
                        pv = '—'
                    else:
                        pd_str = str(pd).strip()
                        # si es número, intentar resolver a District por id
                        if pd_str.isdigit():
                            try:
                                from .models import District
                                dobj = District.objects.filter(id=int(pd_str)).first()
                                pv = dobj.name if dobj else pd_str
                            except Exception:
                                pv = pd_str
                        else:
                            pv = pd_str
                elif k == 'price':
                    symbol = prop.currency.symbol if getattr(prop, 'currency', None) else '$'
                    pv = f"{symbol} {prop.price}" if getattr(prop, 'price', None) is not None else '—'
                elif k == 'currency':
                    pv = prop.currency.code if getattr(prop, 'currency', None) else '—'
                elif k == 'payment_method':
                    pm = getattr(prop, 'forma_de_pago', None)
                    try:
                        pv = pm.name if pm is not None else '—'
                    except Exception:
                        pv = str(pm) if pm is not None else '—'
                elif k == 'bedrooms':
                    pv = str(getattr(prop, 'bedrooms', '—') or '—')
                elif k == 'land_area':
                    pv = str(getattr(prop, 'land_area', '—') or '—')
                else:
                    val = getattr(prop, k, None)
                    if val is None:
                        pv = '—'
                    else:
                        # intentar tomar .name para FKs o convertir a string
                        pv = getattr(val, 'name', None) or str(val)
            except Exception:
                pv = '—'

            # asegurar que `v` sea dict y almacenar la representación
            if isinstance(v, dict):
                v['prop_value'] = pv
                # añadir el peso máximo (valor completo) para este criterio
                v['max'] = weights.get(k, 0)
            else:
                # si v no es dict, convertir a dict para mantener compatibilidad
                details[k] = {'contrib': 0, 'matched': False, 'info': '', 'prop_value': pv, 'max': weights.get(k, 0)}

        # Resolver nombre legible de distrito para la fila resumen (evita mostrar ids numéricos)
        pd = getattr(prop, 'district', None)
        if not pd:
            district_display = ''
        else:
            try:
                pd_str = str(pd).strip()
                if pd_str.isdigit():
                    from .models import District
                    dobj = District.objects.filter(id=int(pd_str)).first()
                    district_display = dobj.name if dobj else pd_str
                else:
                    district_display = pd_str
            except Exception:
                district_display = str(pd)

        # Adjuntar display al resultado para uso en templates
        r['district_display'] = district_display
        # Asegurar que exista entrada para método de pago en detalles (es filtro excluyente pero útil mostrarlo)
        try:
            if 'payment_method' not in details:
                req_pm = getattr(req, 'payment_method', None)
                prop_pm = getattr(prop, 'forma_de_pago', None)
                matched_pm = False
                if req_pm and prop_pm:
                    try:
                        matched_pm = req_pm.id == prop_pm.id
                    except Exception:
                        matched_pm = str(req_pm) == str(prop_pm)
                details['payment_method'] = {
                    'contrib': 0.0,
                    'matched': matched_pm,
                    'info': 'match' if matched_pm else 'no_match',
                    'prop_value': (prop_pm.name if prop_pm else (str(prop_pm) if prop_pm is not None else '—'))
                }
        except Exception:
            pass

    # si piden exportar a CSV, generar respuesta
    if export == 'csv':
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        # cabecera
        writer.writerow(['score', 'property_code', 'title', 'price', 'currency', 'district', 'details'])

        for r in results:
            prop = r['property']
            details = []
            for k, v in r['details'].items():
                # v may be dict with contrib/matched/info
                if isinstance(v, dict):
                    if only_matches and not v.get('matched'):
                        continue
                    details.append(f"{k}:{v.get('contrib',0):.2f}|m:{int(bool(v.get('matched')))}|{v.get('info','')}")
                else:
                    details.append(f"{k}:{v}")

            # resolver nombre de distrito para CSV
            pd = getattr(prop, 'district', None)
            if not pd:
                district_display = ''
            else:
                pd_str = str(pd).strip()
                if pd_str.isdigit():
                    try:
                        from .models import District
                        dobj = District.objects.filter(id=int(pd_str)).first()
                        district_display = dobj.name if dobj else pd_str
                    except Exception:
                        district_display = pd_str
                else:
                    district_display = pd_str

            writer.writerow([
                r['score'],
                getattr(prop, 'code', ''),
                getattr(prop, 'title', ''),
                getattr(prop, 'price', ''),
                getattr(prop, 'currency').symbol if getattr(prop, 'currency', None) else '',
                district_display,
                ';'.join(details)
            ])

        resp = HttpResponse(output.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="matches_requirement_{req.id}.csv"'
        return resp

    return render(request, 'properties/matching_matches.html', {'requirement': req, 'results': results, 'only_matches': only_matches})

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


@login_required
def image_blob_view(request, pk):
    """Servir el contenido binario de `PropertyImage.image_blob` cuando exista.

    Si no existe `image_blob`, redirige a `image.url` si está disponible.
    """
    from .models import PropertyImage
    pi = get_object_or_404(PropertyImage, pk=pk)

    # Si hay blob en la base de datos lo servimos directamente
    if getattr(pi, 'image_blob', None):
        content_type = pi.image_content_type or 'image/jpeg'
        resp = HttpResponse(pi.image_blob, content_type=content_type)
        # permitir caché por defecto (puedes ajustar headers aquí)
        return resp

    # Si no hay blob pero hay un archivo en storage, redirigimos a su URL
    if getattr(pi, 'image', None) and getattr(pi.image, 'url', None):
        return redirect(pi.image.url)

    return HttpResponseNotFound('Image not found')
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


class MyPropertiesView(LoginRequiredMixin, ListView):
    """Lista de propiedades creadas por el usuario actualmente logueado (activas)."""
    model = Property
    template_name = 'properties/my_properties.html'
    context_object_name = 'properties'
    paginate_by = 12

    def get_queryset(self):
        return Property.objects.filter(created_by=self.request.user, is_active=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['property_count'] = context['properties'].count()
        return context


class RequirementListView(LoginRequiredMixin, ListView):
    model = Requirement
    template_name = 'properties/requirements_list.html'
    context_object_name = 'requirements'
    paginate_by = 12

    def get_queryset(self):
        # Mostrar los requerimientos activos de todos los usuarios (no filtrar por created_by)
        qs = Requirement.objects.filter(is_active=True).order_by('-created_at')
        from django.db import OperationalError
        try:
            q = self.request.GET.get('search', '').strip()
            if q:
                qs = qs.filter(
                    Q(property_type__name__icontains=q) |
                    Q(property_subtype__name__icontains=q) |
                    Q(district__name__icontains=q) |
                    Q(urbanization__name__icontains=q)
                )
            return qs
        except OperationalError:
            return Requirement.objects.none()

    def get_context_data(self, **kwargs):
        """Añadir puntuaciones de matching para cada requerimiento mostrado en la página.

        Calculamos la mejor coincidencia (limit=1) usando `matching.get_matches_for_requirement`
        y exponemos un diccionario `matches_scores` en el contexto con {requirement_id: score}.
        """
        context = super().get_context_data(**kwargs)
        reqs = context.get('requirements', [])
        scores = {}
        try:
            for r in reqs:
                try:
                    res = matching_module.get_matches_for_requirement(r, limit=1)
                    if res:
                        scores[r.id] = res[0]['score']
                        # attach to object for easy template access
                        setattr(r, 'match_score', res[0]['score'])
                    else:
                        scores[r.id] = None
                        setattr(r, 'match_score', None)
                except Exception:
                    scores[r.id] = None
                    setattr(r, 'match_score', None)
        except Exception:
            # en caso de errores en DB/logic, no romper la página
            scores = {}

        context['matches_scores'] = scores
        return context


@login_required
def requirement_create_view(request):
    from .forms import RequirementSimpleForm, PropertyOwnerForm
    from .models import PropertyOwner, Requirement
    from django.contrib import messages

    if request.method == 'POST':
        form = RequirementSimpleForm(request.POST)
        owner_form = PropertyOwnerForm(request.POST, request.FILES)
        
        # Determinar si se seleccionó un contacto existente o se crea uno nuevo
        existing_owner_id = request.POST.get('existing_owner', '').strip()
        
        contact_instance = None
        
        if existing_owner_id:
            # Usar contacto existente
            try:
                contact_instance = PropertyOwner.objects.get(id=existing_owner_id)
            except PropertyOwner.DoesNotExist:
                messages.error(request, 'El contacto seleccionado no existe.')
                return render(request, 'properties/requirement_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })
        else:
            # Crear nuevo contacto solo si el formulario contiene cambios reales
            if owner_form.is_valid() and owner_form.has_changed():
                contact_instance = owner_form.save(commit=False)
                contact_instance.created_by = request.user
                contact_instance.save()
                owner_form.save_m2m()  # Para tags
            else:
                messages.error(request, 'Por favor selecciona un contacto existente o completa los datos del contacto.')
                return render(request, 'properties/requirement_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })
        
        if form.is_valid():
            data = form.cleaned_data
            req = Requirement()
            req.created_by = request.user
            req.contact = contact_instance  # Asignar el contacto
            
            req.property_type = data.get('property_type')
            req.property_subtype = data.get('property_subtype')
            bt = data.get('budget_type')
            req.budget_type = bt or 'approx'
            if bt == 'approx':
                req.budget_approx = data.get('budget_approx')
                req.budget_min = None
                req.budget_max = None
            else:
                req.budget_min = data.get('budget_min')
                req.budget_max = data.get('budget_max')
                req.budget_approx = None
            # Área de terreno
            at = data.get('area_type')
            req.area_type = at or 'approx'
            if at == 'approx':
                req.land_area_approx = data.get('land_area_approx')
                req.land_area_min = None
                req.land_area_max = None
            else:
                req.land_area_min = data.get('land_area_min')
                req.land_area_max = data.get('land_area_max')
                req.land_area_approx = None
            # FRENTERA
            fm = data.get('frontera_mode')
            req.frontera_type = fm or 'approx'
            if fm == 'approx':
                req.frontera_approx = data.get('frontera_approx')
                req.frontera_min = None
                req.frontera_max = None
            else:
                req.frontera_min = data.get('frontera_min')
                req.frontera_max = data.get('frontera_max')
                req.frontera_approx = None
            # Moneda
            req.currency = data.get('currency')
            req.payment_method = data.get('payment_method')
            req.status = data.get('status')
            req.department = data.get('department')
            req.province = data.get('province')
            
            req.bedrooms = data.get('bedrooms')
            req.bathrooms = data.get('bathrooms')
            req.half_bathrooms = data.get('half_bathrooms')
            req.floors = data.get('floors')
            # Número de pisos (solo aplicable para tipo Casa). Guardar único valor entero si viene.
            nof = data.get('number_of_floors')
            try:
                req.number_of_floors = int(nof) if nof not in (None, '') else None
            except (ValueError, TypeError):
                req.number_of_floors = None
            # Ascensor (solo aplicable para departamentos). Esperamos 'yes'/'no' o vacío.
            asc = data.get('ascensor') if isinstance(data, dict) else None
            if asc in ('yes', 'no'):
                req.ascensor = asc
            else:
                # como fallback, leer directamente del POST (caso plantilla custom)
                asc_post = request.POST.get('ascensor')
                req.ascensor = asc_post if asc_post in ('yes', 'no') else None
            req.garage_spaces = data.get('garage_spaces')
            req.notes = data.get('notes')
            # Guardar requerimiento primero para luego asignar M2M
            try:
                req.save()
            except Exception:
                messages.error(request, 'No se puede guardar el requerimiento: error inesperado al guardar.')
                return render(request, 'properties/requirement_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })

            # Asignar distritos múltiples si vienen
            districts_sel = data.get('district') or []
            try:
                req.districts.set(districts_sel)
            except Exception:
                pass

            # Asignar preferencias de pisos (M2M)
            floors_sel = data.get('preferred_floors') or []
            try:
                req.preferred_floors.set(floors_sel)
            except Exception:
                pass

            # Asignar zonificaciones (M2M) si vienen
            zon_sel = data.get('zonificacion') or []
            try:
                req.zonificaciones.set(zon_sel)
            except Exception:
                pass

            # Para compatibilidad, si sólo hay una selección, asignarla al FK `district`
            try:
                if hasattr(districts_sel, '__len__') and len(districts_sel) == 1:
                    req.district = list(districts_sel)[0]
                else:
                    req.district = None
            except Exception:
                req.district = None
            from django.db import OperationalError
            try:
                req.save()
            except OperationalError:
                messages.error(request, 'No se puede guardar el requerimiento: base de datos no preparada. Contacte al administrador.')
                return render(request, 'properties/requirement_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })
            messages.success(request, 'Requerimiento guardado correctamente.')
            return redirect('properties:requirements_my')
    else:
        form = RequirementSimpleForm()
        owner_form = PropertyOwnerForm()

    return render(request, 'properties/requirement_create.html', {
        'form': form,
        'owner_form': owner_form,
        'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
    })


class MyRequirementsView(LoginRequiredMixin, ListView):
    model = Requirement
    template_name = 'properties/my_requirements.html'
    context_object_name = 'requirements'
    paginate_by = 12

    def get_queryset(self):
        from django.db import OperationalError
        try:
            return Requirement.objects.filter(created_by=self.request.user).order_by('-created_at')
        except OperationalError:
            return Requirement.objects.none()


class RequirementDetailView(LoginRequiredMixin, DetailView):
    model = Requirement
    template_name = 'properties/requirement_detail.html'
    context_object_name = 'requirement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req = self.get_object()
        user = self.request.user
        # Solo puede ver PII el superuser o el creador del requerimiento
        can_view_pii = user.is_superuser or (req.created_by and req.created_by.id == user.id)
        context['can_view_pii'] = can_view_pii
        return context


from django.views.generic.edit import UpdateView
from django.contrib import messages


class RequirementUpdateView(LoginRequiredMixin, UpdateView):
    model = Requirement
    template_name = 'properties/requirement_edit.html'
    form_class = None  # set in get_form_class to avoid import cycles

    def get_form_class(self):
        from .forms import RequirementEditForm
        return RequirementEditForm

    def form_valid(self, form):
        req = form.save(commit=False)
        # sólo el creador o superuser puede editar
        if not (self.request.user.is_superuser or (req.created_by and req.created_by.id == self.request.user.id)):
            messages.error(self.request, 'No tienes permiso para editar este requerimiento.')
            return redirect('properties:requirements_my')
        req.modified_by = self.request.user
        req.save()
        # guardar M2M `districts`
        try:
            form.save_m2m()
        except Exception:
            pass
        messages.success(self.request, 'Requerimiento actualizado correctamente.')
        return redirect('properties:requirements_detail', pk=req.pk)


@login_required
@require_POST
def requirement_delete_view(request, pk):
    """Elimina un Requirement si el usuario es su creador o superuser."""
    try:
        req = Requirement.objects.get(pk=pk)
    except Requirement.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Requerimiento no encontrado.')
        return redirect('properties:requirements_my')

    if not (request.user.is_superuser or (req.created_by and req.created_by.id == request.user.id)):
        from django.contrib import messages
        messages.error(request, 'No tienes permiso para borrar este requerimiento.')
        return redirect('properties:requirements_my')

    req.delete()
    from django.contrib import messages
    messages.success(request, 'Requerimiento eliminado correctamente.')
    return redirect('properties:requirements_my')


# =============================================================================
# VISTAS PARA AGENDA Y EVENTOS
# =============================================================================

@login_required
def agenda_calendar_view(request):
    """Vista principal del calendario de eventos"""
    from .models import EventType
    event_types = EventType.objects.filter(is_active=True).order_by('name')
    return render(request, 'properties/agenda_calendar.html', {
        'event_types': event_types
    })


@login_required
@login_required
def event_create_view(request):
    """Vista para crear un nuevo evento"""
    from .forms import EventForm, PropertyOwnerForm
    from .models import Event, PropertyOwner
    from django.contrib import messages
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        owner_form = PropertyOwnerForm(request.POST, request.FILES)
        
        # Determinar si se seleccionó un contacto existente o se crea uno nuevo
        existing_owner_id = request.POST.get('existing_owner', '').strip()
        
        contact_instance = None
        
        if existing_owner_id:
            # Usar contacto existente
            try:
                contact_instance = PropertyOwner.objects.get(id=existing_owner_id)
            except PropertyOwner.DoesNotExist:
                messages.error(request, 'El contacto seleccionado no existe.')
                return render(request, 'properties/event_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })
        else:
            # Crear nuevo contacto solo si el formulario contiene cambios reales
            if owner_form.is_valid() and owner_form.has_changed():
                contact_instance = owner_form.save(commit=False)
                contact_instance.created_by = request.user
                contact_instance.save()
                owner_form.save_m2m()  # Para tags
            else:
                messages.error(request, 'Por favor selecciona un contacto existente o completa los datos del contacto.')
                return render(request, 'properties/event_create.html', {
                    'form': form,
                    'owner_form': owner_form,
                    'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
                })
        
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.contact = contact_instance  # Asignar el contacto
            event.save()
            messages.success(request, f'Evento "{event.titulo}" creado exitosamente.')
            return redirect('properties:agenda_calendar')
    else:
        form = EventForm()
        owner_form = PropertyOwnerForm()
    
    return render(request, 'properties/event_create.html', {
        'form': form,
        'owner_form': owner_form,
        'contactos_existentes': PropertyOwner.objects.filter(is_active=True).order_by('first_name')
    })


@login_required
def event_edit_view(request, pk):
    """Vista para editar un evento existente"""
    from .models import Event
    from .forms import EventForm
    
    event = get_object_or_404(Event, pk=pk)
    
    # Solo el creador o superusuario puede editar
    if not (request.user.is_superuser or event.created_by == request.user):
        from django.contrib import messages
        messages.error(request, 'No tienes permiso para editar este evento.')
        return redirect('properties:agenda_calendar')
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, f'Evento "{event.titulo}" actualizado exitosamente.')
            return redirect('properties:agenda_calendar')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'properties/event_edit.html', {'form': form, 'event': event})


@login_required
def event_delete_view(request, pk):
    """Vista para eliminar un evento"""
    from .models import Event
    
    event = get_object_or_404(Event, pk=pk)
    
    # Solo el creador o superusuario puede eliminar
    if not (request.user.is_superuser or event.created_by == request.user):
        from django.contrib import messages
        messages.error(request, 'No tienes permiso para eliminar este evento.')
        return redirect('properties:agenda_calendar')
    
    event.delete()
    from django.contrib import messages
    messages.success(request, 'Evento eliminado correctamente.')
    return redirect('properties:agenda_calendar')


@login_required
def api_events_json(request):
    """API para obtener eventos en formato JSON para el calendario"""
    from .models import Event
    from django.http import JsonResponse
    
    # Si es superusuario, ve todos los eventos, sino solo los suyos
    if request.user.is_superuser:
        events = Event.objects.filter(is_active=True).select_related('event_type', 'property', 'created_by')
    else:
        events = Event.objects.filter(is_active=True, created_by=request.user).select_related('event_type', 'property', 'created_by')
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.titulo,
            'start': f"{event.fecha_evento}T{event.hora_inicio}",
            'end': f"{event.fecha_evento}T{event.hora_fin}",
            'backgroundColor': event.event_type.color,
            'borderColor': event.event_type.color,
            'extendedProps': {
                'code': event.code,
                'event_type': event.event_type.name,
                'detalle': event.detalle,
                'interesado': event.interesado,
                'property': event.property.exact_address if event.property else '',
                'property_code': event.property.code if event.property else '',
                'created_by': event.created_by.get_full_name() if event.created_by else '',
            }
        })
    
    print(f"API Events: Retornando {len(events_data)} eventos para el usuario {request.user.username}")
    return JsonResponse(events_data, safe=False)


# =============================================================================
# VISTAS PARA APIs Y OTROS ENDPOINTS
# =============================================================================

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
        # Si el objeto es un borrador (`is_draft=True`), sólo el creador o superuser pueden verlo
        if getattr(property_obj, 'is_draft', False) and property_obj.created_by and property_obj.created_by != self.request.user and not self.request.user.is_superuser:
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
    # Filtrar por `is_draft=True` y `is_active=False` para listar solo borradores reales
    drafts = Property.objects.filter(created_by=request.user, is_active=False, is_draft=True).order_by('-created_at')
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

        # Filtrar solo por: distrito, tipo de propiedad, forma de pago y rango de precio
        property_type = self.request.GET.get('property_type', '').strip()
        if property_type:
            queryset = queryset.filter(property_type_id=property_type)

        district = self.request.GET.get('district', '').strip()
        if district:
            queryset = queryset.filter(district__iexact=district)

        payment_method = self.request.GET.get('payment_method', '').strip()
        if payment_method:
            try:
                pm_id = int(payment_method)
                queryset = queryset.filter(forma_de_pago_id=pm_id)
            except ValueError:
                pass

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

        # --- Advanced filters ---
        # Urbanización (puede ser id numérico o texto)
        urbanization = self.request.GET.get('urbanization', '').strip()
        if urbanization:
            if urbanization.isdigit():
                queryset = queryset.filter(urbanization=urbanization)
            else:
                queryset = queryset.filter(urbanization__icontains=urbanization)

        # Habitaciones (bedrooms): modo 'range' o 'approx'
        bedrooms_mode = self.request.GET.get('bedrooms_mode', '').strip()
        if bedrooms_mode == 'range':
            bmin = self.request.GET.get('bedrooms_min', '').strip()
            bmax = self.request.GET.get('bedrooms_max', '').strip()
            try:
                if bmin:
                    queryset = queryset.filter(bedrooms__gte=int(bmin))
                if bmax:
                    queryset = queryset.filter(bedrooms__lte=int(bmax))
            except ValueError:
                pass
        elif bedrooms_mode == 'approx':
            approx = self.request.GET.get('bedrooms_approx', '').strip()
            try:
                a = int(approx)
                queryset = queryset.filter(bedrooms__gte=max(0, a-1), bedrooms__lte=a+1)
            except ValueError:
                pass

        # Baños (bathrooms)
        bathrooms_mode = self.request.GET.get('bathrooms_mode', '').strip()
        if bathrooms_mode == 'range':
            bmin = self.request.GET.get('bathrooms_min', '').strip()
            bmax = self.request.GET.get('bathrooms_max', '').strip()
            try:
                if bmin:
                    queryset = queryset.filter(bathrooms__gte=int(bmin))
                if bmax:
                    queryset = queryset.filter(bathrooms__lte=int(bmax))
            except ValueError:
                pass
        elif bathrooms_mode == 'approx':
            approx = self.request.GET.get('bathrooms_approx', '').strip()
            try:
                a = int(approx)
                queryset = queryset.filter(bathrooms__gte=max(0, a-1), bathrooms__lte=a+1)
            except ValueError:
                pass

        # Estacionamientos (garage_spaces)
        garage_mode = self.request.GET.get('garage_mode', '').strip()
        if garage_mode == 'range':
            gmin = self.request.GET.get('garage_min', '').strip()
            gmax = self.request.GET.get('garage_max', '').strip()
            try:
                if gmin:
                    queryset = queryset.filter(garage_spaces__gte=int(gmin))
                if gmax:
                    queryset = queryset.filter(garage_spaces__lte=int(gmax))
            except ValueError:
                pass
        elif garage_mode == 'approx':
            approx = self.request.GET.get('garage_approx', '').strip()
            try:
                a = int(approx)
                queryset = queryset.filter(garage_spaces__gte=max(0, a-1), garage_spaces__lte=a+1)
            except ValueError:
                pass

        # Área (land_area o built_area)
        area_field = self.request.GET.get('area_field', 'land').strip()
        area_mode = self.request.GET.get('area_mode', '').strip()
        area_min = self.request.GET.get('area_min', '').strip()
        area_max = self.request.GET.get('area_max', '').strip()
        area_approx = self.request.GET.get('area_approx', '').strip()
        area_field_name = 'land_area' if area_field == 'land' else 'built_area'
        try:
            if area_mode == 'range':
                if area_min:
                    queryset = queryset.filter(**{f"{area_field_name}__gte": float(area_min)})
                if area_max:
                    queryset = queryset.filter(**{f"{area_field_name}__lte": float(area_max)})
            elif area_mode == 'approx' and area_approx:
                # approximate: +/-10% range
                a = float(area_approx)
                low = max(0.0, a * 0.9)
                high = a * 1.1
                queryset = queryset.filter(**{f"{area_field_name}__gte": low, f"{area_field_name}__lte": high})
        except (ValueError, TypeError):
            pass

        # Estado (status) por id, o filtro especial 'antiguedad' (edad de la propiedad en años)
        status = self.request.GET.get('status', '').strip()
        if status:
            if status == 'antiguedad':
                # Filtrar por antiguedad usando created_at (años) con cálculo por años reales
                from django.utils import timezone
                from datetime import timedelta
                now = timezone.now()

                def years_ago(dt, years):
                    # Intenta restar años preservando mes/día; maneja 29-feb ajustando a 28-feb
                    try:
                        return dt.replace(year=dt.year - years)
                    except ValueError:
                        try:
                            # Fallback para 29-feb -> 28-feb
                            return dt.replace(month=2, day=28, year=dt.year - years)
                        except Exception:
                            return dt - timedelta(days=365 * years)

                age_mode = self.request.GET.get('age_mode', '').strip()
                if age_mode == 'range':
                    age_min = self.request.GET.get('age_min', '').strip()
                    age_max = self.request.GET.get('age_max', '').strip()
                    try:
                        if age_min:
                            years = int(age_min)
                            cutoff = years_ago(now, years)
                            # propiedades con edad >= age_min -> created_at <= cutoff
                            queryset = queryset.filter(created_at__lte=cutoff)
                        if age_max:
                            years = int(age_max)
                            cutoff = years_ago(now, years)
                            # propiedades con edad <= age_max -> created_at >= cutoff
                            queryset = queryset.filter(created_at__gte=cutoff)
                    except ValueError:
                        pass
                elif age_mode == 'approx':
                    approx = self.request.GET.get('age_approx', '').strip()
                    try:
                        a = int(approx)
                        low = years_ago(now, a + 1)
                        high = years_ago(now, max(0, a - 1))
                        queryset = queryset.filter(created_at__gte=low, created_at__lte=high)
                    except ValueError:
                        pass
            else:
                if status.isdigit():
                    queryset = queryset.filter(status_id=int(status))
                else:
                    queryset = queryset.filter(status__name__icontains=status)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        properties = context['properties']
        context['user_role'] = self.request.user.role.name if self.request.user.role else 'Sin rol'
        # Listas para selects reducidas según requerimiento
        context['property_types'] = PropertyType.objects.filter(is_active=True).order_by('name')
        from .models import PaymentMethod
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True).order_by('order')
        # Obtener distritos de las propiedades ya cargadas en memoria
        # Resolver posibles valores numéricos a nombres usando el modelo District
        try:
            from .models import District

            def _resolve_district_obj(value):
                if not value:
                    return None
                try:
                    if str(value).isdigit():
                        obj = District.objects.filter(pk=int(value)).first()
                        if obj:
                            return {'id': obj.id, 'name': getattr(obj, 'name', str(value))}
                        else:
                            return {'id': int(value), 'name': str(value)}
                    return {'id': '', 'name': str(value)}
                except Exception:
                    return {'id': '', 'name': str(value)}

            # Mantener el orden y eliminar duplicados por (id,name)
            seen = set()
            districts = []
            for p in properties:
                if not p.district:
                    continue
                resolved = _resolve_district_obj(p.district)
                key = (str(resolved.get('id')), resolved.get('name'))
                if key not in seen:
                    seen.add(key)
                    districts.append(resolved)

            # ordenar por nombre para mostrar
            context['districts_list'] = sorted(districts, key=lambda x: (x.get('name') or ''))
        except Exception:
            # En caso de error, caer al valor bruto como lista de nombres
            names = sorted({p.district for p in properties if p.district})
            context['districts_list'] = [{'id': '', 'name': n} for n in names]

        context['filters'] = {
            'property_type': self.request.GET.get('property_type', '').strip(),
            'district': self.request.GET.get('district', '').strip(),
            'payment_method': self.request.GET.get('payment_method', '').strip(),
            'price_min': self.request.GET.get('price_min', '').strip(),
            'price_max': self.request.GET.get('price_max', '').strip(),
        }
        # Añadir filtros avanzados actuales para persistir la UI
        context['filters'].update({
            'urbanization': self.request.GET.get('urbanization', '').strip(),
            'bedrooms_mode': self.request.GET.get('bedrooms_mode', '').strip(),
            'bedrooms_min': self.request.GET.get('bedrooms_min', '').strip(),
            'bedrooms_max': self.request.GET.get('bedrooms_max', '').strip(),
            'bedrooms_approx': self.request.GET.get('bedrooms_approx', '').strip(),
            'bathrooms_mode': self.request.GET.get('bathrooms_mode', '').strip(),
            'bathrooms_min': self.request.GET.get('bathrooms_min', '').strip(),
            'bathrooms_max': self.request.GET.get('bathrooms_max', '').strip(),
            'bathrooms_approx': self.request.GET.get('bathrooms_approx', '').strip(),
            'garage_mode': self.request.GET.get('garage_mode', '').strip(),
            'garage_min': self.request.GET.get('garage_min', '').strip(),
            'garage_max': self.request.GET.get('garage_max', '').strip(),
            'garage_approx': self.request.GET.get('garage_approx', '').strip(),
            'area_field': self.request.GET.get('area_field', 'land').strip(),
            'area_mode': self.request.GET.get('area_mode', '').strip(),
            'area_min': self.request.GET.get('area_min', '').strip(),
            'area_max': self.request.GET.get('area_max', '').strip(),
            'area_approx': self.request.GET.get('area_approx', '').strip(),
            'status': self.request.GET.get('status', '').strip(),
        })

        # Preparar mensaje de advertencia para 'antiguedad' que indique el rango o valor buscado
        age_warning = ''
        try:
            if context['filters'].get('status') == 'antiguedad':
                age_mode = self.request.GET.get('age_mode', '').strip()
                if age_mode == 'range':
                    age_min = self.request.GET.get('age_min', '').strip()
                    age_max = self.request.GET.get('age_max', '').strip()
                    if age_min and age_max:
                        age_warning = f"Buscando propiedades entre {age_min} y {age_max} años."
                    elif age_min:
                        age_warning = f"Buscando propiedades desde {age_min} años."
                    elif age_max:
                        age_warning = f"Buscando propiedades de hasta {age_max} años."
                elif age_mode == 'approx':
                    approx = self.request.GET.get('age_approx', '').strip()
                    if approx:
                        age_warning = f"Buscando propiedades con antigüedad ≈ {approx} años (±1 año)."
        except Exception:
            age_warning = ''

        context['age_warning'] = age_warning

        # Listas para selects avanzados
        context['statuses'] = PropertyStatus.objects.filter(is_active=True).order_by('order')
        try:
            context['urbanizations_list'] = list(Urbanization.objects.filter(is_active=True).order_by('name').values('id', 'name'))
        except Exception:
            context['urbanizations_list'] = []

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
                if first_image:
                    # Preferir la URL del ImageField cuando exista. Usar URL absoluta
                    if getattr(first_image, 'image', None) and getattr(first_image.image, 'url', None):
                        try:
                            first_image_url = self.request.build_absolute_uri(first_image.image.url)
                        except Exception:
                            first_image_url = first_image.image.url
                    # Si la imagen se almacenó como blob en la tabla, usar la vista que la sirve (URL absoluta)
                    elif getattr(first_image, 'image_blob', None):
                        try:
                            first_image_url = self.request.build_absolute_uri(reverse('properties:image_blob', kwargs={'pk': first_image.pk}))
                        except Exception:
                            try:
                                first_image_url = reverse('properties:image_blob', kwargs={'pk': first_image.pk})
                            except Exception:
                                first_image_url = ''

            # Preparar nombre seguro del propietario: puede ser método o atributo string
            try:
                _owner = getattr(property_obj, 'owner', None)
                _full = getattr(_owner, 'full_name', None)
                if callable(_full):
                    owner_display = _full()
                elif isinstance(_full, str):
                    owner_display = _full
                else:
                    owner_display = str(_owner) if _owner is not None else ''
            except Exception:
                owner_display = str(getattr(property_obj, 'owner', ''))

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
                'owner': owner_display,
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
                    # Asegurarse de obtener sólo borradores explícitos (is_draft=True)
                    draft = Property.objects.get(pk=int(draft_id), created_by=request.user, is_active=False, is_draft=True)
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
                    'is_draft': True,
                }
                # intentar setear algunos campos opcionales desde POST
                for fld in ['title', 'description', 'exact_address', 'real_address', 'coordinates', 'department', 'province', 'district', 'urbanization']:
                    val = request.POST.get(fld)
                    if val:
                        draft_kwargs[fld] = val

                try:
                    draft = Property.objects.create(**draft_kwargs)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception('Error creando borrador de propiedad: %s', e)
                    draft = None

            # Si tenemos un borrador (nuevo o existente), guardar archivos subidos en él
            if draft is not None:
                # imágenes
                images_files = request.FILES.getlist('images')
                image_types = request.POST.getlist('image_types')
                image_captions = request.POST.getlist('image_captions')
                image_orders = request.POST.getlist('image_orders')
                image_sensibles = request.POST.getlist('image_sensibles')
                for idx, image_file in enumerate(images_files):
                    # Ignorar inputs vacíos (campo presente pero sin fichero)
                    if not image_file or getattr(image_file, 'size', 0) == 0:
                        continue

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
                        sensible_val = False
                        try:
                            v = image_sensibles[idx] if idx < len(image_sensibles) else None
                            sensible_val = str(v) in ('1', 'true', 'on')
                        except Exception:
                            sensible_val = False
                        PropertyImage.objects.create(
                            property=draft,
                            image=image_file,
                            image_type=image_type,
                            caption=caption,
                            order=order,
                            sensible=sensible_val,
                            uploaded_by=request.user
                        )
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.exception('Error guardando imagen en borrador: %s', e)
                        from django.contrib import messages
                        messages.error(request, 'Error al guardar imagen (borrador). Revisa los logs.')

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
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.exception('Error guardando video en borrador: %s', e)
                            from django.contrib import messages
                            messages.error(request, 'Error al guardar video (borrador). Revisa los logs.')

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
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.exception('Error guardando documento en borrador: %s', e)
                            from django.contrib import messages
                            messages.error(request, 'Error al guardar documento (borrador). Revisa los logs.')

            # preparar contexto para re-renderizar el formulario con los recursos ya subidos
            contactos_existentes = PropertyOwner.objects.filter(is_active=True).order_by('-created_at')
            existing_images = list(PropertyImage.objects.filter(property=draft).order_by('order')) if draft else []
            existing_videos = list(PropertyVideo.objects.filter(property=draft)) if draft else []
            existing_documents = list(PropertyDocument.objects.filter(property=draft)) if draft else []
            draft_id_to_pass = draft.pk if draft else ''
            from django.contrib import messages
            messages.success(request, 'Borrador guardado. Puedes gestionarlo desde Borradores.')
            # Redirigir a la lista de borradores para que el usuario confirme el guardado
            return redirect('properties:drafts')
        # Validar form y owner_form según el caso
        existing_owner_id = request.POST.get('existing_owner')
        owner_form_valid = True

        if existing_owner_id:
            # Si hay propietario existente, no necesitamos validar owner_form
            owner_form_valid = True
        else:
            # Si se crea nuevo propietario, validar owner_form y asegurarnos de que tenga cambios
            owner_form_valid = owner_form.is_valid() and owner_form.has_changed()
        
        if form.is_valid() and owner_form_valid:
            if existing_owner_id:
                owner = PropertyOwner.objects.get(pk=existing_owner_id)
            else:
                # Guardar nuevo owner sólo si el formulario contenía cambios (owner_form_valid asegura esto)
                owner = owner_form.save(commit=False)
                owner.created_by = request.user
                owner.save()
                owner_form.save_m2m()

            property_obj = form.save(commit=False)
            property_obj.owner = owner
            property_obj.created_by = request.user
            # Determinar estado según la acción del formulario: solo marcar como activa
            # si se solicitó expresamente guardar la propiedad activa.
            property_obj.is_active = True if action == 'save_property' else False
            # Ajustar flag explícito de borrador
            property_obj.is_draft = False if action == 'save_property' else True
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
            image_sensibles = request.POST.getlist('image_sensibles')
            
            primary_image_set = False
            # Limitar número de imágenes por subida para evitar OOM/timeout
            # No limitar la cantidad de imágenes aquí; procesarlas todas
            for idx, image_file in enumerate(images_files):
                # Ignorar inputs vacíos (campo presente pero sin fichero)
                if not image_file or getattr(image_file, 'size', 0) == 0:
                    continue

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
                
                try:
                    sensible_val = False
                    try:
                        v = image_sensibles[idx] if idx < len(image_sensibles) else None
                        sensible_val = str(v) in ('1', 'true', 'on')
                    except Exception:
                        sensible_val = False
                    img = PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        image_type=image_type,
                        caption=caption,
                        order=order,
                        sensible=sensible_val,
                        is_primary=is_primary,
                        uploaded_by=request.user
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception('Error guardando imagen: %s', e)
                    from django.contrib import messages
                    messages.error(request, 'Error guardando una imagen. Revisa los logs.')
                    continue
                # Registrar evento de imagen subida
                try:
                    PropertyChange.objects.create(
                        property=property_obj,
                        field_name='image',
                        old_value=None,
                        new_value=f"Imagen subida: {img.caption or img.image.name}",
                        changed_by=request.user
                    )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception('Error registrando cambio de imagen para la propiedad %s: %s', property_obj.pk, e)
                    from django.contrib import messages
                    messages.error(request, 'Error al registrar evento de imagen. Revisa los logs.')
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
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.exception('Error registrando cambio de video para la propiedad %s: %s', property_obj.pk, e)
                        from django.contrib import messages
                        messages.error(request, 'Error al registrar evento de video. Revisa los logs.')

            # ===================== PROCESAR DOCUMENTOS =====================
            documents_files = request.FILES.getlist('documents')
            document_types = request.POST.getlist('document_types')
            document_titles = request.POST.getlist('document_titles')
            document_descriptions = request.POST.getlist('document_descriptions') or request.POST.getlist('document_descripciones')
            
            for idx, document_file in enumerate(documents_files):
                if document_file:
                    try:
                        doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                        doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                    except (DocumentType.DoesNotExist, ValueError):
                        doc_type = None
                    
                    title = document_titles[idx] if idx < len(document_titles) else f'Documento {idx + 1}'
                    description = document_descriptions[idx] if idx < len(document_descriptions) else ''
                    
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
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.exception('Error registrando cambio de documento para la propiedad %s: %s', property_obj.pk, e)
                        from django.contrib import messages
                        messages.error(request, 'Error al registrar evento de documento. Revisa los logs.')

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

            # Helper para normalizar orden de imágenes a 1..N
            from django.db.models import Max
            def _normalize_image_orders(prop):
                imgs = list(PropertyImage.objects.filter(property=prop).order_by('order', 'uploaded_at', 'id'))
                for idx2, im in enumerate(imgs, start=1):
                    if im.order != idx2:
                        PropertyImage.objects.filter(pk=im.pk).update(order=idx2)

            # calcular orden base según las imágenes existentes
            max_order = PropertyImage.objects.filter(property=property_obj).aggregate(m=Max('order'))['m'] or 0
            for idx, image_file in enumerate(images_files):
                # Ignorar inputs vacíos (campo presente pero sin fichero)
                if not image_file or getattr(image_file, 'size', 0) == 0:
                    continue

                try:
                    image_type_id = image_types[idx] if idx < len(image_types) and image_types[idx] else None
                    image_type = ImageType.objects.get(pk=image_type_id) if image_type_id else None
                except (ImageType.DoesNotExist, ValueError):
                    image_type = None
                # Si el formulario proporcionó un order concreto, usarlo; si no, anexar al final
                try:
                    provided = image_orders[idx] if idx < len(image_orders) and image_orders[idx] else None
                    order = int(provided) if provided else (max_order + 1)
                except ValueError:
                    order = max_order + 1
                caption = image_captions[idx] if idx < len(image_captions) else ''
                is_primary = not primary_image_set
                try:
                    # try to read sensible value if provided (select ensures alignment)
                    sensible_val = False
                    try:
                        image_sensibles = request.POST.getlist('image_sensibles')
                        v = image_sensibles[idx] if idx < len(image_sensibles) else None
                        sensible_val = str(v) in ('1', 'true', 'on')
                    except Exception:
                        sensible_val = False

                    img = PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        image_type=image_type,
                        caption=caption,
                        order=order,
                        sensible=sensible_val,
                        is_primary=is_primary,
                        uploaded_by=request.user
                    )
                    primary_image_set = True
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.exception('Error guardando imagen en edición: %s', e)
                    from django.contrib import messages
                    messages.error(request, 'Error guardando una imagen. Revisa los logs.')
                    continue
                # aumentar el max_order para siguientes imágenes sin orden
                if order >= max_order:
                    max_order = order
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

            # Normalizar secuencia de orders tras posibles adiciones
            _normalize_image_orders(property_obj)

            # Actualizar flag `sensible` para imágenes existentes si se enviaron controles separados
            try:
                imgs = PropertyImage.objects.filter(property=property_obj)
                for im in imgs:
                    try:
                        key = f'existing_image_sensible_{im.id}'
                        v = request.POST.get(key)
                        sensible_val = str(v) in ('1', 'true', 'on')
                        if im.sensible != sensible_val:
                            PropertyImage.objects.filter(pk=im.pk).update(sensible=sensible_val)
                    except Exception:
                        continue
            except Exception:
                pass

            # Videos
            videos_files = request.FILES.getlist('videos')
            video_types = request.POST.getlist('video_types')
            video_titles = request.POST.getlist('video_titles')
            video_descriptions = request.POST.getlist('video_descriptions') or request.POST.getlist('video_descripciones')
            for idx, video_file in enumerate(videos_files):
                if video_file:
                    try:
                        video_type_id = video_types[idx] if idx < len(video_types) and video_types[idx] else None
                        video_type = VideoType.objects.get(pk=video_type_id) if video_type_id else None
                    except (VideoType.DoesNotExist, ValueError):
                        video_type = None
                    
                    title = video_titles[idx] if idx < len(video_titles) else f'Video {idx + 1}'
                    description = video_descriptions[idx] if idx < len(video_descriptions) else ''
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
            document_descriptions = request.POST.getlist('document_descriptions') or request.POST.getlist('document_descripciones')
            for idx, document_file in enumerate(documents_files):
                if document_file:
                    try:
                        doc_type_id = document_types[idx] if idx < len(document_types) and document_types[idx] else None
                        doc_type = DocumentType.objects.get(pk=doc_type_id) if doc_type_id else None
                    except (DocumentType.DoesNotExist, ValueError):
                        doc_type = None
                    
                    title = document_titles[idx] if idx < len(document_titles) else f'Documento {idx + 1}'
                    description = document_descriptions[idx] if idx < len(document_descriptions) else ''
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
    from django.db.models import Count, Q
    properties = (
        Property.objects.filter(is_active=True)
        .select_related('currency')
        .annotate(
            utm_total=Count('whatsapp_links', distinct=True),
            utm_active=Count('whatsapp_links', filter=Q(whatsapp_links__is_active=True), distinct=True),
        )
        .order_by('-created_at')
    )
    
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
