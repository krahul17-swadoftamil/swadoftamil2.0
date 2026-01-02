from django.db import models
from decimal import Decimal
import uuid
from django.utils import timezone


class IngredientMovement(models.Model):
    """Record stock movements for ingredients.

    Positive `change_qty` = stock added (purchase, transfer-in)
    Negative `change_qty` = stock removed (consumption, transfer-out)
    """
    REASON_PURCHASE = 'purchase'
    REASON_CONSUMPTION = 'consumption'
    REASON_ADJUSTMENT = 'adjustment'
    REASON_CHOICES = [
        (REASON_PURCHASE, 'Purchase'),
        (REASON_CONSUMPTION, 'Consumption'),
        (REASON_ADJUSTMENT, 'Adjustment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ingredient = models.ForeignKey('ingredients.Ingredient', on_delete=models.CASCADE)
    change_qty = models.DecimalField(max_digits=12, decimal_places=3)
    reason = models.CharField(max_length=32, choices=REASON_CHOICES, default=REASON_ADJUSTMENT)
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    resulting_qty = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ingredient.name}: {self.change_qty} @ {self.timestamp:%Y-%m-%d %H:%M}"
