import os
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()
from menu.models import PreparedItem
names = ['Coconut Chutney', 'Peanut Chutney', 'Onion Tomato Chutney']
for name in names:
    try:
        p = PreparedItem.objects.get(name=name)
        p.serving_size = Decimal('35')
        p.save()
        print(f"Updated {name} id={p.id} serving_size={p.serving_size}")
    except PreparedItem.DoesNotExist:
        print(f"PreparedItem not found: {name}")
