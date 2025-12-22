# Ensure project root is on sys.path so Django settings import works
import os
import sys
from pathlib import Path
import django

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
# Django settings will read DB_* env vars
django.setup()
from django.db import connection

print('Using Django DB settings:')
from django.conf import settings
print('ENGINE =', settings.DATABASES['default'].get('ENGINE'))
print('NAME   =', settings.DATABASES['default'].get('NAME'))
print('HOST   =', settings.DATABASES['default'].get('HOST'))
print('USER   =', settings.DATABASES['default'].get('USER'))

try:
    cur = connection.cursor()
    cur.execute('SELECT DB_NAME()')
    print('DB_NAME() =', cur.fetchone())
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_TYPE='BASE TABLE'")
    rows = cur.fetchall()
    print('Tables count =', len(rows))
    for r in rows:
        print('-', r[0])
    # check django_migrations
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='django_migrations'")
    dm_exists = cur.fetchone()[0]
    print('django_migrations exists? ->', bool(dm_exists))
    if dm_exists:
        cur.execute('SELECT COUNT(*) FROM dbo.django_migrations')
        print('Applied migrations rows =', cur.fetchone()[0])
except Exception as e:
    print('Error querying DB:', e)
    import traceback
    traceback.print_exc()
