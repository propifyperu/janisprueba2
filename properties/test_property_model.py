from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db import IntegrityError, transaction

from .models import (
    Property,
    PropertyOwner,
    PropertyType,
    PropertySubtype,
    PropertyStatus,
    Currency,
    District,
    Province,
    Department,
    Urbanization,
    PropertyImage,
    ImageType,
    RoomType,
)


class PropertyModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', email='t@example.com', password='pass')

        # Minimal taxonomy/config
        self.dept = Department.objects.create(name='Lima', code='LIM')
        self.prov = Province.objects.create(name='Lima', code='LIM', department=self.dept)
        self.dist = District.objects.create(name='Miraflores', code='MIR', province=self.prov)
        self.urb = Urbanization.objects.create(name='Urb Centro', code='UC', district=self.dist)

        self.ptype = PropertyType.objects.create(name='Casa')
        self.psub = PropertySubtype.objects.create(property_type=self.ptype, name='Casa de playa')
        self.status = PropertyStatus.objects.create(name='Activo', code='active')
        self.currency = Currency.objects.create(code='USD', name='Dolar', symbol='$')

        self.owner = PropertyOwner.objects.create(created_by=self.user)

    def _create_property(self, **overrides):
        base = dict(
            owner=self.owner,
            property_type=self.ptype,
            property_subtype=self.psub,
            status=self.status,
            price=Decimal('1000.00'),
            currency=self.currency,
            created_by=self.user,
            department=str(self.dept.name),
            province=str(self.prov.name),
            district=str(self.dist.name),
            urbanization=str(self.urb.name),
            exact_address='Av. 123',
            title='Casa Bonita',
        )
        base.update(overrides)
        return Property.objects.create(**base)

    def test_is_active_syncs_with_availability_status(self):
        # Initial available -> is_active True
        p = self._create_property(availability_status='available')
        p.refresh_from_db()
        self.assertTrue(p.is_active)

        # Change to paused -> should become inactive via post_save signal
        p.availability_status = 'paused'
        p.save()
        p.refresh_from_db()
        self.assertFalse(p.is_active)

        # Back to available -> becomes active again
        p.availability_status = 'available'
        p.save()
        p.refresh_from_db()
        self.assertTrue(p.is_active)

    def test_unique_code_enforced(self):
        p1 = self._create_property()
        # Force duplicate code into second property to check DB constraint
        p2 = self._create_property()
        p2.code = p1.code
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                p2.save()

    def test_codigo_unico_propiedad_is_generated_and_unique(self):
        p1 = self._create_property()
        p2 = self._create_property(title='Otra Casa')
        self.assertTrue(p1.codigo_unico_propiedad)
        self.assertTrue(p2.codigo_unico_propiedad)
        self.assertNotEqual(p1.codigo_unico_propiedad, p2.codigo_unico_propiedad)

    def test_title_case_applied_on_save(self):
        p = self._create_property(title='  caSa BONITA   ')
        self.assertEqual(p.title, 'Casa Bonita')

    def test_related_media_cascades_on_delete(self):
        # Create property and related image -> on_delete=models.CASCADE should remove image with property
        p = self._create_property()
        img_type = ImageType.objects.create(name='Foto')
        room_type = RoomType.objects.create(name='Sala')
        prop_img = PropertyImage.objects.create(
            property=p,
            image='properties/images/fake.jpg',
            image_type=img_type,
            image_ambiente=room_type,
            caption='Principal',
            order=1,
            is_primary=True,
            uploaded_by=self.user,
        )
        self.assertEqual(PropertyImage.objects.filter(property=p).count(), 1)
        p.delete()
        self.assertEqual(PropertyImage.objects.filter(id=prop_img.id).count(), 0)
