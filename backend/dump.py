import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()
from django.core.management import call_command
with open('data.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', stdout=f)