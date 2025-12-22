import csv
import pyodbc

server = 'propify.database.windows.net,1433'
database = 'propify_db'
username = 'adminpropify'
password = 'Propify12345@'

conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'UID={username};'
    f'PWD={password};'
    'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)

out_file = 'payment_methods.csv'

try:
    cnxn = pyodbc.connect(conn_str)
    cur = cnxn.cursor()
    cur.execute('SELECT * FROM payment_methods')
    cols = [c[0] for c in cur.description]
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        for row in cur:
            writer.writerow(row)
    print('Exported', out_file)
    cur.close()
    cnxn.close()
except Exception as e:
    print('Error exporting payment_methods:', e)
