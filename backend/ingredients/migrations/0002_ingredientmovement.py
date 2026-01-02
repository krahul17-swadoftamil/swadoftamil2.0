from django.db import migrations, models
import uuid
import django.utils.timezone
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('ingredients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngredientMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('change_qty', models.DecimalField(decimal_places=3, max_digits=12)),
                ('reason', models.CharField(choices=[('purchase', 'Purchase'), ('consumption', 'Consumption'), ('adjustment', 'Adjustment')], default='adjustment', max_length=32)),
                ('note', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, db_index=True)),
                ('resulting_qty', models.DecimalField(decimal_places=3, max_digits=12)),
                ('ingredient', models.ForeignKey(on_delete=models.deletion.CASCADE, to='ingredients.ingredient')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
