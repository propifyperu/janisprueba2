import pyodbc

server = 'propify.database.windows.net,1433'
database = 'propify_db'
username = 'adminpropify'
password = 'Propify12345@'
# Build connection string
conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

print('Connecting using:', conn_str)
try:
    cnxn = pyodbc.connect(conn_str)
except Exception as e:
    print('Connection error:', e)
    raise SystemExit(1)

cur = cnxn.cursor()

queries = [
    ("TABLES", "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE '%payment%' OR TABLE_NAME LIKE '%property_financial%';"),
    ("COLUMNS_payment_methods", "SELECT COLUMN_NAME, ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='payment_methods' ORDER BY ORDINAL_POSITION;"),
    ("COLUMNS_property_financial_info", "SELECT COLUMN_NAME, ORDINAL_POSITION FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='property_financial_info' ORDER BY ORDINAL_POSITION;"),
    ("TOP_payment_methods", "SELECT TOP 1 * FROM payment_methods;")
]

for name, q in queries:
    print('\n---', name, '---')
    try:
        cur.execute(q)
        rows = cur.fetchall()
        for r in rows[:20]:
            print(r)
        if not rows:
            print('(no rows)')
    except Exception as e:
        print('ERROR running query:', e)

cur.close()
cnxn.close()
