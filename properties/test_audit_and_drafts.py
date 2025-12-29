from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import (
    Property, PropertyOwner, PropertyType, PropertySubtype,
    PropertyStatus, Currency, PropertyChange
)


class AuditAndDraftsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(username='user1', email='u1@example.com', password='pass')
        self.user2 = User.objects.create_user(username='user2', email='u2@example.com', password='pass')
        self.client = Client()

        # Crear datos requeridos mínimos
        self.pt = PropertyType.objects.create(name='Tipo A')
        self.psub = PropertySubtype.objects.create(property_type=self.pt, name='Sub A')
        self.status = PropertyStatus.objects.create(name='Activo', code='active')
        self.currency = Currency.objects.create(code='USD', name='Dolar', symbol='$')
        self.owner = PropertyOwner.objects.create(created_by=self.user1)

        # Crear propiedad válida
        self.prop = Property.objects.create(
            owner=self.owner,
            property_type=self.pt,
            property_subtype=self.psub,
            status=self.status,
            price=Decimal('1000.00'),
            currency=self.currency,
            created_by=self.user1,
            department='Dept',
            province='Prov',
            district='Dist',
            urbanization='Urban',
            exact_address='Exact Address',
            coordinates='-12.046374,-77.042793',
            title='Old Title',
        )

    def test_edit_creates_propertychange(self):
        self.client.force_login(self.user1)
        url = f'/dashboard/{self.prop.pk}/editar/'

        post_data = {
            'existing_owner': str(self.owner.pk),
            'title': 'New Title',
            'price': str(self.prop.price),
            'currency': str(self.currency.pk),
            'property_type': str(self.pt.pk),
            'property_subtype': str(self.psub.pk),
            'status': str(self.status.pk),
            'responsible': '',
            'description': '',
            'antiquity_years': '',
            'delivery_date': '',
            'maintenance_fee': '',
            # 'has_maintenance': '',
            'floors': str(self.prop.floors),
            'bedrooms': str(self.prop.bedrooms),
            'bathrooms': str(self.prop.bathrooms),
            'half_bathrooms': str(self.prop.half_bathrooms),
            'garage_spaces': str(self.prop.garage_spaces),
            'garage_type': '',
            'land_area': '',
            'land_area_unit': '',
            'built_area': '',
            'built_area_unit': '',
            'front_measure': '',
            'depth_measure': '',
            'real_address': self.prop.real_address or '',
            'exact_address': self.prop.exact_address or '',
            'coordinates': self.prop.coordinates or '',
            'department': self.prop.department,
            'province': self.prop.province,
            'district': self.prop.district,
            'urbanization': self.prop.urbanization or '',
            'water_service': '',
            'energy_service': '',
            'drainage_service': '',
            'gas_service': '',
            'amenities': '',
            'zoning': '',
            # tags field can be omitted or empty list
        }

        response = self.client.post(url, post_data, follow=True)
        # Debe redirigir a detalle y terminar con 200
        self.assertEqual(response.status_code, 200)

        # Refrescar instancia
        self.prop.refresh_from_db()
        changes = PropertyChange.objects.filter(property=self.prop, field='title')
        self.assertTrue(changes.exists(), "No se creó un registro de cambio para 'title'.")
        first = changes.first()
        self.assertEqual(first.new_value, 'New Title')
        self.assertEqual(first.changed_by, self.user1)

    def test_draft_privacy(self):
        # Crear un borrador (is_active=False)
        draft = Property.objects.create(
            owner=self.owner,
            property_type=self.pt,
            property_subtype=self.psub,
            status=self.status,
            price=Decimal('10.00'),
            currency=self.currency,
            created_by=self.user1,
            department='D', province='P', district='D', urbanization='',
            exact_address='Borrador', coordinates='', title='Draft',
                is_active=False,
                is_draft=True,
        )

        # Acceder como otro usuario debe 404
        self.client.force_login(self.user2)
        resp = self.client.get(f'/dashboard/{draft.pk}/')
        self.assertEqual(resp.status_code, 404)

        # Acceder como creador debe 200
        self.client.force_login(self.user1)
        resp2 = self.client.get(f'/dashboard/{draft.pk}/')
        self.assertEqual(resp2.status_code, 200)
