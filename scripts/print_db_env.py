import os
import pprint
import sys
# Asegurar que el directorio actual esté en sys.path para importar settings
sys.path.insert(0, os.getcwd())
keys=['DB_HOST','DB_USER','DB_EXTRA_PARAMS','DB_DRIVER','DB_PASS','DB_PASSWORD','DB_CONN_TIMEOUT']
print('Environment DB vars:')
for k in keys:
    print(f"{k} = {repr(os.environ.get(k))}")
print('\nSettings-derived DATABASES[default][OPTIONS]:')
try:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'janis_core3.settings'
    import django
    django.setup()
    from django.conf import settings
    pprint.pprint(settings.DATABASES.get('default'))
except Exception as e:
    print('Error importing settings:', e)
