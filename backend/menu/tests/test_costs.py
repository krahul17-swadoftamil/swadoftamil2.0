from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from ingredients.models import Ingredient
from menu.models import PreparedItem, PreparedItemRecipe, Combo, ComboItem


class CostCalculationTests(TestCase):
    def test_ingredient_cost_conversion_weight(self):
        """Ingredient in kg, recipe in grams should convert correctly."""
        rice = Ingredient.objects.create(
            name="Rice",
            unit="kg",
            stock_qty=Decimal("10.000"),
            cost_per_unit=Decimal("500.00")
        )

        idli = PreparedItem.objects.create(
            name="Idli",
            unit="pcs",
            is_active=True
        )

        # 100 grams of rice per idli
        recipe = PreparedItemRecipe.objects.create(
            prepared_item=idli,
            ingredient=rice,
            quantity=Decimal("100"),
            quantity_unit="gm"
        )

        # cost = 0.1 kg * 500 = 50.00
        self.assertEqual(recipe.ingredient_cost, Decimal("50.00"))

    def test_recipe_unit_mismatch_raises(self):
        """Recipe with incompatible units must raise ValidationError on full_clean/save."""
        coconut = Ingredient.objects.create(
            name="Coconut",
            unit="pcs",
            stock_qty=Decimal("100"),
            cost_per_unit=Decimal("20.00")
        )

        chutney = PreparedItem.objects.create(
            name="Coconut Chutney",
            unit="ml",
            is_active=True
        )

        bad = PreparedItemRecipe(
            prepared_item=chutney,
            ingredient=coconut,
            quantity=Decimal("50"),
            quantity_unit="gm"
        )

        with self.assertRaises(ValidationError):
            bad.full_clean()

    def test_combo_profit_negative_detection(self):
        """Create combo where selling price < base cost to show negative profit."""
        rice = Ingredient.objects.create(
            name="Rice2",
            unit="kg",
            stock_qty=Decimal("1.000"),
            cost_per_unit=Decimal("1000.00")
        )

        idli = PreparedItem.objects.create(name="Idli2", unit="pcs", is_active=True)
        PreparedItemRecipe.objects.create(
            prepared_item=idli,
            ingredient=rice,
            quantity=Decimal("500"),
            quantity_unit="gm"
        )

        combo = Combo.objects.create(name="Expensive Combo", selling_price=Decimal("10.00"))
        ComboItem.objects.create(combo=combo, prepared_item=idli, quantity=1, item_type="combo")

        # base cost should exceed selling price -> negative profit
        self.assertTrue(combo.profit() < Decimal("0.00"))