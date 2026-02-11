from django.db import migrations
from django.db.models import F


def forwards(apps, schema_editor):
    Event = apps.get_model("properties", "Event")

    # Rellenar assigned_agent con created_by donde esté NULL
    Event.objects.filter(
        assigned_agent_id__isnull=True,
        created_by_id__isnull=False,
    ).update(assigned_agent_id=F("created_by_id"))


def backwards(apps, schema_editor):
    # No revertimos para no borrar datos reales si alguien ya lo editó
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0036_event_assigned_agent"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]