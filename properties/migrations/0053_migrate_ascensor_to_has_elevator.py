from django.db import migrations

def forwards(apps, schema_editor):
    Property = apps.get_model("properties", "Property")

    # yes -> True
    Property.objects.filter(ascensor__iexact="yes").update(has_elevator=True)

    # no -> False (igual ya es default, pero lo dejamos explícito)
    Property.objects.filter(ascensor__iexact="no").update(has_elevator=False)

def backwards(apps, schema_editor):
    Property = apps.get_model("properties", "Property")

    # reconstrucción simple
    Property.objects.filter(has_elevator=True).update(ascensor="yes")
    Property.objects.filter(has_elevator=False).update(ascensor=None)

class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0052_property_has_elevator"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]