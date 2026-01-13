import sys
import traceback
import os
sys.path.insert(0, os.getcwd())
try:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'janis_core3.settings'
    import django
    django.setup()
    from django.conf import settings
    opts = settings.DATABASES['default']['OPTIONS']
    driver = opts.get('driver')
    extra = opts.get('extra_params','')
    host = settings.DATABASES['default']['HOST']
    user = settings.DATABASES['default']['USER']
    pwd = settings.DATABASES['default']['PASSWORD']
    port = settings.DATABASES['default']['PORT']
    conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};UID={user};PWD={pwd};{extra}"
    print('Connection string:')
    print(conn_str)
    import pyodbc
    print('Attempting pyodbc.connect...')
    conn = pyodbc.connect(conn_str, timeout=10)
    print('Connection successful')
    conn.close()
except Exception as e:
    print('Exception while connecting:')
    traceback.print_exc()
    sys.exit(1)
