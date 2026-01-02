from decimal import Decimal

from django.test import TestCase

from ingredients.models import Ingredient
from menu.models import PreparedItem, PreparedItemRecipe, Combo, ComboItem


class SignalsCostUpdateTests(TestCase):
    def test_comboitem_cost_cached_updates_on_ingredient_change(self):
        # Create an ingredient with positive stock and unit cost
        ingr = Ingredient.objects.create(
            name="TS-Ingredient",
            unit=Ingredient.UNIT_PCS,
            stock_qty=Decimal("10"),
            cost_per_unit=Decimal("5.00"),
        )

        # Prepared item that uses the ingredient (1 pcs per prepared item)
        pi = PreparedItem.objects.create(
            name="TS-Prepared",
            unit="pcs",
            serving_size=Decimal("1.000"),
        )

        PreparedItemRecipe.objects.create(
            prepared_item=pi,
            ingredient=ingr,
            quantity=Decimal("1"),
            quantity_unit="pcs",
        )

        # Create combo and a combo item (quantity 2)
        combo = Combo.objects.create(name="TS-Combo", selling_price=Decimal("100.00"))
        item = ComboItem.objects.create(combo=combo, prepared_item=pi, quantity=2, item_type="combo")

        # After creation, saved cost_cached should equal computed cost
        item.refresh_from_db()
        self.assertEqual(item.cost_cached, item.compute_cost())

        # Update ingredient cost — signals should backfill cached values
        ingr.cost_per_unit = Decimal("6.00")
        ingr.save()

        # Reload and assert combo item cached cost updated
        item.refresh_from_db()
        self.assertEqual(item.cost_cached, item.compute_cost())
