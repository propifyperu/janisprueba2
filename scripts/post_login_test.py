import os, sys, traceback
sys.path.insert(0, os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'janis_core3.settings'
import django
django.setup()
from django.test import Client

c = Client()
try:
    # For Django test Client, set HTTP_HOST to match ALLOWED_HOSTS
    resp = c.post('/users/login/', {'username': 'sqladmin', 'password': 'wrongpassword'}, follow=True, HTTP_HOST='127.0.0.1')
    print('Response status:', resp.status_code)
    print('Final URL:', resp.request.get('PATH_INFO'))
    print('Content snippet:\n', resp.content.decode('utf-8')[:800])
except Exception:
    print('Exception raised during POST:')
    traceback.print_exc()
    sys.exit(1)
