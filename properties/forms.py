from django import forms
import unicodedata
from .models import (
    Property,
    PropertyOwner,
    PropertyImage,
    PropertyDocument,
    PropertyVideo,
    PropertyRoom,
    PropertyFinancialInfo,
)


class PropertyOwnerForm(forms.ModelForm):
    class Meta:
        model = PropertyOwner
        fields = [
            'first_name', 'last_name', 'maternal_last_name',
            'document_type', 'document_number', 'birth_date', 'gender',
            'photo', 'phone', 'secondary_phone', 'email', 'profession',
            'company', 'department', 'province', 'district', 'urbanization',
            'address_exact', 'address_coordinates', 'observations', 'tags'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres completos'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido paterno'}),
            'maternal_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido materno'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono principal'}),
            'secondary_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono secundario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'profession': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'department': forms.Select(attrs={'class': 'form-select', 'id': 'id_department'}),
            'province': forms.Select(attrs={'class': 'form-select', 'id': 'id_province'}),
            'district': forms.Select(attrs={'class': 'form-select', 'id': 'id_district'}),
            'urbanization': forms.Select(attrs={'class': 'form-select', 'id': 'id_urbanization'}),
            'address_exact': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección exacta...'}),
            'address_coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Latitud, Longitud'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Observaciones adicionales...'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
        }


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'code', 'codigo_unico_propiedad', 'title', 'description',
            'owner', 'property_type', 'property_subtype', 'condition', 'status', 'responsible',
            'antiquity_years', 'delivery_date',
            'price', 'currency', 'forma_de_pago', 'maintenance_fee', 'has_maintenance',
            'floors', 'bedrooms', 'bathrooms', 'half_bathrooms',
            'garage_spaces', 'garage_type',
            'parking_cost_included', 'parking_cost',
            'land_area', 'land_area_unit', 'built_area', 'built_area_unit',
            'front_measure', 'depth_measure',
            'unit_location',
            'is_project', 'project_name',
            'real_address', 'exact_address', 'coordinates', 'department', 'province', 'district', 'urbanization',
            'water_service', 'energy_service', 'drainage_service', 'gas_service',
            'amenities', 'zoning', 'tags',
            'assigned_agent', 'is_active', 'is_ready_for_sale'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción detallada de la propiedad'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título para campañas o publicaciones'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'property_subtype': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'responsible': forms.Select(attrs={'class': 'form-select'}),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'forma_de_pago': forms.Select(attrs={'class': 'form-select'}),
            'garage_type': forms.Select(attrs={'class': 'form-select'}),
            'unit_location': forms.Select(attrs={'class': 'form-select', 'id': 'id_unit_location'}),
            'parking_cost_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parking_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 120.00'
            }),
            'land_area_unit': forms.Select(attrs={'class': 'form-select'}),
            'built_area_unit': forms.Select(attrs={'class': 'form-select'}),
            'water_service': forms.Select(attrs={'class': 'form-select'}),
            'energy_service': forms.Select(attrs={'class': 'form-select'}),
            'drainage_service': forms.Select(attrs={'class': 'form-select'}),
            'gas_service': forms.Select(attrs={'class': 'form-select'}),
            'zoning': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zonificación'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'assigned_agent': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_ready_for_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
                'is_project': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_project'}),
                'project_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_project_name', 'placeholder': 'Nombre del proyecto (si aplica)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos opcionales
        for field_name in self.fields:
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        antiquity_years = cleaned_data.get('antiquity_years')
        delivery_date = cleaned_data.get('delivery_date')

        def normalize_value(value):
            if not value:
                return ''
            normalized = unicodedata.normalize('NFKD', value)
            ascii_value = normalized.encode('ascii', 'ignore').decode('ascii')
            return ascii_value.lower().replace('-', '_').replace(' ', '_')

        status_keys = set()
        if status:
            status_keys.add(normalize_value(getattr(status, 'code', '')))
            status_keys.add(normalize_value(getattr(status, 'name', '')))

        antiquity_markers = {'antiguedad', 'antiquity'}
        construction_markers = {'en_construccion', 'en_construction', 'under_construction'}

        status_keys.discard('')

        is_antiquity = bool(antiquity_markers & status_keys)
        is_under_construction = bool(construction_markers & status_keys)

        if is_antiquity:
            if antiquity_years in (None, ''):
                self.add_error('antiquity_years', 'Este campo es obligatorio cuando el estado es Antigüedad.')
        else:
            cleaned_data['antiquity_years'] = None

        if is_under_construction:
            if not delivery_date:
                self.add_error('delivery_date', 'Este campo es obligatorio cuando el estado es En construcción.')
        else:
            cleaned_data['delivery_date'] = None

        return cleaned_data


class PropertyFinancialInfoForm(forms.ModelForm):
    class Meta:
        model = PropertyFinancialInfo
        fields = [
            'initial_commission_percentage',
            'final_commission_percentage',
            'final_amount',
            'negotiation_status',
        ]
        widgets = {
            'initial_commission_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 3.50',
            }),
            'final_commission_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ej: 4.00',
            }),
            'final_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monto final negociado',
            }),
            'negotiation_status': forms.Select(attrs={'class': 'form-select'}),
        }


class PropertyImageForm(forms.ModelForm):
    class Meta:
        model = PropertyImage
        fields = ['image', 'image_type', 'caption', 'is_primary', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'image_type': forms.Select(attrs={'class': 'form-select'}),
            'caption': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Descripción de la imagen'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0'
            }),
        }


class PropertyVideoForm(forms.ModelForm):
    class Meta:
        model = PropertyVideo
        fields = ['video', 'video_type', 'title', 'description']
        widgets = {
            'video': forms.FileInput(attrs={'class': 'form-control'}),
            'video_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Título del video'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descripción del video'
            }),
        }


class PropertyDocumentForm(forms.ModelForm):
    class Meta:
        model = PropertyDocument
        fields = ['file', 'document_type', 'title', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Título del documento'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descripción del documento'
            }),
        }


class PropertyRoomForm(forms.ModelForm):
    class Meta:
        model = PropertyRoom
        fields = ['level', 'room_type', 'name', 'width', 'length', 'area', 'floor_type', 'description', 'order'
        ]
        widgets = {
            'level': forms.Select(attrs={'class': 'form-select'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre del ambiente (opcional)'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'placeholder': 'Ancho en metros'
            }),
            'length': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'placeholder': 'Largo en metros'
            }),
            'area': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0', 
                'placeholder': 'Área en m²'
            }),
            'floor_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Descripción del ambiente'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'placeholder': 'Orden de visualización'
            }),
        }


class RequirementForm(forms.ModelForm):
    class Meta:
        model = None  # se reemplaza en runtime para evitar import circular
        fields = [
            'client_name', 'phone', 'property_type', 'property_subtype',
            'budget_type', 'budget_approx', 'budget_min', 'budget_max', 'currency',
            'payment_method', 'status',
            'department', 'province', 'district', 'urbanization',
            'bedrooms', 'bathrooms', 'half_bathrooms', 'floors', 'garage_spaces',
            'notes'
        ]

    def __init__(self, *args, **kwargs):
        # Importar aquí para evitar ciclos
        from .models import Requirement
        # Asignar el modelo antes de inicializar para que ModelForm construya los campos
        self._meta.model = Requirement
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales por defecto
        for field_name in self.fields:
            self.fields[field_name].required = False
        # Widgets básicos
        self.fields['client_name'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['phone'].widget = forms.TextInput(attrs={'class': 'form-control'})
        self.fields['notes'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})


class RequirementSimpleForm(forms.Form):
    client_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    property_type = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    property_subtype = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    budget_type = forms.ChoiceField(choices=(('approx','Aproximado'),('range','Rango')), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    budget_approx = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    budget_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    budget_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    # Área de terreno
    area_type = forms.ChoiceField(choices=(('approx','Aproximado'),('range','Rango')), required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    land_area_approx = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
    land_area_min = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
    land_area_max = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class':'form-control','step':'0.01'}))
    currency = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    payment_method = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    department = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    province = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    # Permitir selección múltiple para búsquedas en varios distritos/urbanizaciones
    district = forms.ModelMultipleChoiceField(queryset=None, required=False, widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size':6}))
    urbanization = forms.ModelMultipleChoiceField(queryset=None, required=False, widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size':6}))
    bedrooms = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    bathrooms = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    half_bathrooms = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    floors = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    garage_spaces = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importar modelos aquí para evitar ciclos y establecer querysets dinámicamente
        from .models import PropertyType, PropertySubtype, PaymentMethod, PropertyStatus, Department, Province, District, Urbanization
        from django.db import OperationalError
        try:
            self.fields['property_type'].queryset = PropertyType.objects.filter(is_active=True).order_by('name')
            self.fields['property_subtype'].queryset = PropertySubtype.objects.filter(is_active=True).order_by('name')
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(is_active=True).order_by('order')
            self.fields['status'].queryset = PropertyStatus.objects.filter(is_active=True).order_by('order')
            # Monedas
            from .models import Currency
            self.fields['currency'].queryset = Currency.objects.filter(is_active=True).order_by('name')
            self.fields['department'].queryset = Department.objects.filter(is_active=True).order_by('name')
            self.fields['province'].queryset = Province.objects.filter(is_active=True).order_by('name')
            self.fields['district'].queryset = District.objects.filter(is_active=True).order_by('name')
            self.fields['urbanization'].queryset = Urbanization.objects.filter(is_active=True).order_by('name')
        except OperationalError:
            # Si las tablas no existen (deploy sin migraciones), devolver querysets vacíos para no fallar la carga
            self.fields['property_type'].queryset = PropertyType.objects.none()
            self.fields['property_subtype'].queryset = PropertySubtype.objects.none()
            self.fields['payment_method'].queryset = PaymentMethod.objects.none()
            self.fields['status'].queryset = PropertyStatus.objects.none()
            # Monedas
            try:
                self.fields['currency'].queryset = Currency.objects.none()
            except Exception:
                pass
            self.fields['department'].queryset = Department.objects.none()
            self.fields['province'].queryset = Province.objects.none()
            self.fields['district'].queryset = District.objects.none()
            self.fields['urbanization'].queryset = Urbanization.objects.none()