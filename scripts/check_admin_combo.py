import os
import sys
from urllib.parse import quote

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
# ensure project root is on sys.path so `backend` package imports work
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

COMBO_ID = '9d354a3b-b633-4930-8fca-578c77720de4'
URL = f'/admin/menu/combo/{quote(COMBO_ID)}/change/'

User = get_user_model()
# find or create a superuser for the check
admin = User.objects.filter(is_superuser=True).first()
if not admin:
    username_field = getattr(User, 'USERNAME_FIELD', 'username')
    kwargs = {username_field: 'admin', 'email': 'admin@example.com'}
    try:
        admin = User.objects.create_superuser(**{**kwargs, 'password': 'pass'})
    except TypeError:
        # fallback signature
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')

client = Client()
client.force_login(admin)

print('Requesting URL:', URL)
try:
    resp = client.get(URL)
    print('Status code:', resp.status_code)
    content = resp.content.decode('utf-8', errors='replace')
    # Print a trimmed snippet for inspection
    print('Content snippet (first 800 chars):')
    print(content[:800])
except Exception as e:
    print('Exception while requesting admin page:')
    import traceback
    traceback.print_exc()
    sys.exit(2)

sys.exit(0)
