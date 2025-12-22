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
    # Get columns and detect problematic types
    cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='payment_methods' ORDER BY ORDINAL_POSITION;")
    cols_info = cur.fetchall()
    cols = [c[0] for c in cols_info]
    select_parts = []
    problematic = ('datetimeoffset',)
    for name, dtype in cols_info:
        if dtype in problematic:
            select_parts.append(f"CAST([{name}] AS VARCHAR(50)) AS [{name}]")
        else:
            select_parts.append(f"[{name}]")
    select_sql = 'SELECT ' + ', '.join(select_parts) + ' FROM payment_methods'
    cur.execute(select_sql)
    rows = cur.fetchall()
    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        for row in rows:
            writer.writerow([str(x) if x is not None else '' for x in row])
    print('Exported', out_file, 'rows:', len(rows))
    cur.close()
    cnxn.close()
except Exception as e:
    print('Error exporting payment_methods:', e)
