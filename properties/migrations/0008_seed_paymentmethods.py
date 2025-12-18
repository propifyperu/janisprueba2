from django.db import migrations


def create_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('properties', 'PaymentMethod')
    defaults = [
        {'name': 'Transferencia', 'code': 'TRANSFER', 'order': 1},
        {'name': 'Efectivo', 'code': 'CASH', 'order': 2},
        {'name': 'Tarjeta', 'code': 'CARD', 'order': 3},
    ]
    for item in defaults:
        PaymentMethod.objects.update_or_create(code=item.get('code'), defaults=item)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0007_alter_paymentmethod_options'),
    ]

    operations = [
        migrations.RunPython(create_payment_methods, reverse_code=noop),
    ]
