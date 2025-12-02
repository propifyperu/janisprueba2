#!/usr/bin/env python
"""
Script para verificar que los modelos están registrados en el admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
django.setup()

from django.contrib.admin.sites import site

print("Admin Models Registrados:")
print("="*50)
for model, admin_class in site._registry.items():
    app_label = model._meta.app_label
    model_name = model.__name__
    print(f"✓ {app_label.upper():15} - {model_name}")

print("\n" + "="*50)
print(f"Total: {len(site._registry)} modelos registrados")
