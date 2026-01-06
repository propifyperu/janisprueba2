# Script para crear tipos de eventos iniciales
# Ejecutar con: python manage.py shell < seed_event_types.py

from properties.models import EventType

event_types_data = [
    {'name': 'Visita', 'color': '#047D7D'},
    {'name': 'Reunión', 'color': '#2196F3'},
    {'name': 'Llamada', 'color': '#FF9800'},
    {'name': 'Firma de Contrato', 'color': '#4CAF50'},
    {'name': 'Entrega de Llaves', 'color': '#9C27B0'},
    {'name': 'Seguimiento', 'color': '#607D8B'},
    {'name': 'Otro', 'color': '#757575'},
]

for data in event_types_data:
    EventType.objects.get_or_create(
        name=data['name'],
        defaults={'color': data['color']}
    )

print("Tipos de eventos creados exitosamente!")
