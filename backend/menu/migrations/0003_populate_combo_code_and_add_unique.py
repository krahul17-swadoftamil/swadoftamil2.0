from django.db import migrations, models


def populate_codes(apps, schema_editor):
    Combo = apps.get_model('menu', 'Combo')
    from django.db.models import Q
    import re

    prefix = 'SOT-'

    # Find current max suffix among existing SOT- codes
    maxn = 0
    for code in Combo.objects.filter(code__startswith=prefix).values_list('code', flat=True):
        if not code:
            continue
        m = re.search(r"(\d+)$", code)
        if m:
            try:
                n = int(m.group(1))
                if n > maxn:
                    maxn = n
            except Exception:
                continue

    # Assign new codes to rows with empty or null code
    need_qs = Combo.objects.filter(Q(code__isnull=True) | Q(code=''))
    for combo in need_qs.order_by('name'):
        maxn += 1
        combo.code = f"{prefix}{maxn:02d}"
        combo.save()


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_combo_code_combo_serve_person_combo_total_protein'),
    ]

    operations = [
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='combo',
            name='code',
            field=models.CharField(blank=True, help_text='Unique code like SOT-01', max_length=16, unique=True),
        ),
    ]
