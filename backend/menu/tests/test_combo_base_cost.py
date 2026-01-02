from decimal import Decimal
from django.test import TestCase

from menu.models import Combo, ComboItem, PreparedItem


class ComboBaseCostTest(TestCase):
    def test_base_cost_is_sum_of_prepared_item_costs(self):
        # Create two prepared items with known cost_price via recipes
        p1 = PreparedItem.objects.create(name="P1", unit="pcs", is_active=True)
        p2 = PreparedItem.objects.create(name="P2", unit="ml", is_active=True)

        # Create ingredients and recipes so cost_price is computed from ingredients
        from ingredients.models import Ingredient

        # For p1: one ingredient 1 pcs @ 10.00
        ing1 = Ingredient.objects.create(name="Ing1", unit="pcs", stock_qty=Decimal("100"), cost_per_unit=Decimal("10.00"))
        p1.recipes.create(ingredient=ing1, quantity=Decimal("1"), quantity_unit="pcs")

        # For p2: ingredient priced per litre; 1 ml should cost 2.50 -> set cost_per_unit=2500 per litre
        ing2 = Ingredient.objects.create(name="Ing2", unit="ltr", stock_qty=Decimal("10"), cost_per_unit=Decimal("2500.00"))
        p2.recipes.create(ingredient=ing2, quantity=Decimal("1"), quantity_unit="ml")

        combo = Combo.objects.create(name="Test Combo", selling_price=Decimal("100.00"))
        # 3 pcs of p1 and 4 ml-units of p2 (quantity is interpreted as "units")
        ComboItem.objects.create(combo=combo, prepared_item=p1, quantity=3, item_type="combo")
        ComboItem.objects.create(combo=combo, prepared_item=p2, quantity=4, item_type="combo")

        # base_cost = 3*10.00 + 4*2.50 = 30 + 10 = 40
        self.assertEqual(combo.base_cost(), Decimal("40.00"))