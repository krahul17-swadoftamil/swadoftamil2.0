import logging
from decimal import Decimal

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from ingredients.models import Ingredient
from menu.models import (
    PreparedItem,
    PreparedItemRecipe,
    ComboItem,
)

logger = logging.getLogger(__name__)
ZERO = Decimal("0.00")


# ======================================================
# INGREDIENT → PREPARED ITEM COST RECALC
# ======================================================

@receiver(post_save, sender=Ingredient)
def on_ingredient_change(sender, instance, **kwargs):
    """
    When ingredient cost or stock changes,
    recompute all dependent PreparedItem costs.
    """
    recipes = PreparedItemRecipe.objects.select_related(
        "prepared_item"
    ).filter(ingredient=instance)

    for recipe in recipes:
        pi = recipe.prepared_item
        if not pi:
            continue

        try:
            pi.recompute_and_cache_cost()
            PreparedItem.objects.filter(pk=pi.pk).update(
                cost_price_cached=pi.cost_price_cached
            )
        except Exception:
            logger.exception(
                "PreparedItem cost recompute failed (ingredient=%s, item=%s)",
                instance.id,
                pi.id,
            )


# ======================================================
# PREPARED ITEM RECIPE → PREPARED ITEM COST RECALC
# ======================================================

@receiver([post_save, post_delete], sender=PreparedItemRecipe)
def on_recipe_change(sender, instance, **kwargs):
    """
    When recipe ingredients or quantities change,
    recompute PreparedItem cost.
    """
    pi = instance.prepared_item
    if not pi:
        return

    try:
        pi.recompute_and_cache_cost()
        PreparedItem.objects.filter(pk=pi.pk).update(
            cost_price_cached=pi.cost_price_cached
        )
    except Exception:
        logger.exception(
            "PreparedItem cost recompute failed (prepared_item=%s)",
            pi.id,
        )


# ======================================================
# COMBO ITEM → COST CACHE UPDATE
# ======================================================

@receiver(post_save, sender=ComboItem)
def on_combo_item_change(sender, instance, **kwargs):
    """
    When a ComboItem quantity or PreparedItem changes,
    recompute and cache its cost.
    """
    try:
        cost = instance.compute_cost() or ZERO
        ComboItem.objects.filter(pk=instance.pk).update(
            cost_cached=cost
        )
    except Exception:
        logger.exception(
            "ComboItem cost recompute failed (combo_item=%s)",
            instance.id,
        )
