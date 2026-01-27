"""
Script de comprobación rápida de conexión a Azure SQL.
Ejecuta: `python test_conn.py` desde la raíz del proyecto.
No imprime la contraseña; muestra UID y host y el error si falla.
"""
import os
import sys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv no instalado, usando variables de entorno del sistema.")

try:
    import pyodbc
except Exception as e:
    print("pyodbc no está instalado o no se puede importar:", e)
    sys.exit(2)

user = os.environ.get('DB_USER', 'sqladmin')
host = os.environ.get('DB_HOST', 'janisdevsql58636.database.windows.net')
password = os.environ.get('DB_PASS') or os.environ.get('DB_PASSWORD')
driver = os.environ.get('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
database = os.environ.get('DB_NAME', 'janis_main')
port = os.environ.get('DB_PORT', '1433')

if '@' not in user and host and 'database.windows.net' in host:
    # Ajuste automático para Azure SQL
    user = f"{user}@{host.split('.')[0]}"

# Determinar parámetros extra (simulando lógica de settings.py)
default_encrypt = 'yes' if 'database.windows.net' in host else 'no'
extra_params = os.environ.get('DB_EXTRA_PARAMS', f'Encrypt={default_encrypt};TrustServerCertificate=yes;Connection Timeout=10;')

conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={host},{port};"
    f"DATABASE={database};"
    f"UID={user};PWD={password};"
    f"{extra_params}"
)

print('Probando conexión con:')
print('  HOST=', host)
print('  DATABASE=', database)
print('  UID=', user)
print('  DRIVER=', driver)
print('  PARAMS=', extra_params)

try:
    cn = pyodbc.connect(conn_str, timeout=10)
    print('Conexión OK')
    cn.close()
    sys.exit(0)
except Exception as e:
    print('ERROR al conectar:')
    print(e)
    sys.exit(1)
