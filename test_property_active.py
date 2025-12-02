#!/usr/bin/env python
"""
Script para verificar cambios en is_active de Property
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from properties.models import Property

# Obtener una propiedad existente
try:
    prop = Property.objects.first()
    if prop:
        print(f"Propiedad encontrada: {prop.code}")
        print(f"is_active actual: {prop.is_active}")
        
        # Intentar cambiar is_active
        original_value = prop.is_active
        prop.is_active = not original_value
        
        try:
            prop.save()
            print(f"✓ Cambio exitoso a: {prop.is_active}")
            
            # Revertir cambio
            prop.is_active = original_value
            prop.save()
            print(f"✓ Revertido a: {prop.is_active}")
        except Exception as e:
            print(f"✗ Error al guardar: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("No hay propiedades en la base de datos")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
