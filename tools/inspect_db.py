import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
try:
    django.setup()
except Exception as e:
    print('ERROR django.setup():', e)
    sys.exit(1)

from django.db import connection

def run(q):
    try:
        with connection.cursor() as c:
            c.execute(q)
            return c.fetchall()
    except Exception as e:
        return ('ERROR', str(e))

print('--- TABLES matching payment% or property_financial% ---')
print(run("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%payment%' OR TABLE_NAME LIKE '%property_financial%';"))

print('\n--- COLUMNS in payment_methods ---')
print(run("SELECT COLUMN_NAME, ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='payment_methods' ORDER BY ORDINAL_POSITION;"))

print('\n--- COLUMNS in property_financial_info ---')
print(run("SELECT COLUMN_NAME, ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='property_financial_info' ORDER BY ORDINAL_POSITION;"))

print('\n--- Top row from payment_methods (schema preview) ---')
print(run("SELECT TOP 1 * FROM payment_methods;"))
