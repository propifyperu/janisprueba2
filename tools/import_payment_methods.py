from django.utils.dateparse import parse_datetime
from properties.models import PaymentMethod
import csv
import os


def parse_bool(val: str) -> bool:
    return str(val).strip().lower() in ('1', 'true', 't', 'yes', 'y')


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    csv_path = os.path.join(repo_root, 'payment_methods.csv')
    if not os.path.exists(csv_path):
        print('payment_methods.csv not found at', csv_path)
        return

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            name = (row.get('name') or '').strip()
            if not name:
                continue
            code = (row.get('code') or '').strip() or None
            description = (row.get('description') or '').strip() or ''
            order_val = row.get('order') or '0'
            try:
                order = int(order_val)
            except Exception:
                order = 0
            is_active = parse_bool(row.get('is_active', 'True'))
            created_at_raw = (row.get('created_at') or '').strip()

            pm, created = PaymentMethod.objects.update_or_create(
                name=name,
                defaults={
                    'code': code,
                    'description': description,
                    'order': order,
                    'is_active': is_active,
                }
            )

            if created and created_at_raw:
                dt = parse_datetime(created_at_raw)
                if dt:
                    pm.created_at = dt
                    pm.save(update_fields=['created_at'])

            print(('Created' if created else 'Updated'), name)
            count += 1

    print('Processed', count, 'rows')


if __name__ == '__main__':
    main()
