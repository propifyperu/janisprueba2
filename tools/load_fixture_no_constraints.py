from django.db import connection
from django.core import management


def exec_sql(sql: str):
    with connection.cursor() as cursor:
        cursor.execute(sql)


def disable_constraints():
    sql = """
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME) + ' NOCHECK CONSTRAINT ALL;'
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE';
EXEC sp_executesql @sql;
"""
    exec_sql(sql)


def enable_constraints():
    sql = """
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(TABLE_SCHEMA) + '.' + QUOTENAME(TABLE_NAME) + ' WITH CHECK CHECK CONSTRAINT ALL;'
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE='BASE TABLE';
EXEC sp_executesql @sql;
"""
    exec_sql(sql)


def main():
    print('Disabling constraints...')
    disable_constraints()
    try:
        print('Running loaddata...')
        management.call_command('loaddata', 'properties.utf8.json')
    finally:
        print('Re-enabling constraints...')
        enable_constraints()


if __name__ == '__main__':
    main()
