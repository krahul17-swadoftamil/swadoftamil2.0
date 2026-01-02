from django.contrib.auth import get_user_model
User = get_user_model()
u, created = User.objects.get_or_create(username='swadadmin', defaults={'email': 'admin@swad.local'})
u.is_staff = True
u.is_superuser = True
u.set_password('SwadAdm1n!2026')
u.save()
print('CREATED' if created else 'UPDATED')
