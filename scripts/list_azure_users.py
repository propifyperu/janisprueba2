from pathlib import Path
import os, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'janis_core3.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()

users = User.objects.all()[:50]
print('Total users (fetched up to 50):', users.count())
for u in users:
    try:
        username = getattr(u, 'username', None) or getattr(u, 'email', None) or str(u)
    except Exception:
        username = str(u)
    print(f'- username={username} | email={getattr(u, "email", None)} | is_active={getattr(u, "is_active", None)} | id={getattr(u, "id", None)}')
