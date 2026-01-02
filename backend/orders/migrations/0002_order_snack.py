"""Add OrderSnack snapshot model

Generated automatically by the assistant to match the model in orders.models
"""
from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderSnack",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("snack_id", models.BigIntegerField()),
                ("snack_name", models.CharField(max_length=120)),
                ("quantity", models.PositiveIntegerField(validators=[MinValueValidator(1)])),
                ("price", models.DecimalField(max_digits=10, decimal_places=2)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snacks",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "indexes": [models.Index(fields=["order"], name="orders_orde_order_sn_8d3f6b_idx")],
            },
        ),
    ]
