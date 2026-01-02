from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone
import os

from menu.models import PreparedItemRecipe

Q2 = Decimal("0.01")


class Command(BaseCommand):
    help = (
        "Preview and optionally apply safe conversions for suspect PreparedItemRecipe rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-threshold",
            type=float,
            default=10.0,
            help="Threshold above which numeric quantities for kg/ltr base are suspicious (default: 10)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limit number of rows to process (0 = no limit)",
        )
        parser.add_argument(
            "--mode",
            choices=("set_unit", "convert_value"),
            default="set_unit",
            help=(
                "Fix mode: 'set_unit' will mark quantity_unit as gm/ml; '
                "convert_value' will divide quantity by 1000 and keep base unit."
            ),
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply the suggested changes to the database. Without this flag the command only previews.",
        )

    def handle(self, *args, **options):
        threshold = options.get("min_threshold")
        limit = options.get("limit") or None
        mode = options.get("mode")
        do_apply = options.get("apply")

        qs = PreparedItemRecipe.objects.select_related("ingredient", "prepared_item").all()

        candidates = []
        for r in qs:
            ing = r.ingredient
            if ing.unit in ("kg", "ltr") and not r.quantity_unit:
                try:
                    q = float(r.quantity or 0)
                except Exception:
                    continue
                if q > threshold:
                    candidates.append(r)
                    if limit and len(candidates) >= limit:
                        break

        if not candidates:
            self.stdout.write(self.style.SUCCESS("No candidates found."))
            return

        self.stdout.write(self.style.WARNING(f"Found {len(candidates)} candidate rows (threshold={threshold})."))

        preview_rows = []
        for r in candidates:
            ing = r.ingredient
            small_unit = "gm" if ing.unit == "kg" else "ml"
            old_unit = r.quantity_unit or ing.unit
            old_qty = Decimal(r.quantity or Decimal(0))
            # current interpreted cost (what system is currently using)
            try:
                old_cost = r.ingredient_cost
            except Exception:
                old_cost = None

            if mode == "set_unit":
                # Suggest: mark quantity_unit as small_unit (e.g., gm/ml). Numeric value stays the same.
                try:
                    new_cost = ing.cost_for_quantity(r.quantity, small_unit)
                except Exception:
                    new_cost = None
                suggestion = f"set quantity_unit='{small_unit}' (keep qty={r.quantity})"

            else:  # convert_value
                # Suggest: convert numeric quantity to base unit by dividing by 1000
                new_qty = (Decimal(r.quantity) / Decimal("1000")).quantize(Q2)
                try:
                    new_cost = ing.cost_for_quantity(new_qty, ing.unit)
                except Exception:
                    new_cost = None
                suggestion = f"convert qty -> {new_qty} {ing.unit} (clear quantity_unit)"

            preview_rows.append({
                "id": r.id,
                "prepared_item": r.prepared_item.name,
                "ingredient": ing.name,
                "ingredient_unit": ing.unit,
                "quantity": str(r.quantity),
                "old_cost": str(old_cost) if old_cost is not None else "ERR",
                "new_cost": str(new_cost) if new_cost is not None else "ERR",
                "suggestion": suggestion,
            })

        # Print preview
        for p in preview_rows:
            self.stdout.write(
                f"[{p['id']}] {p['prepared_item']} ← {p['ingredient']} ({p['ingredient_unit']}): qty={p['quantity']} | old_cost={p['old_cost']} -> new_cost={p['new_cost']} | {p['suggestion']}"
            )

        if not do_apply:
            self.stdout.write(self.style.SUCCESS("Preview complete. Run with --apply to perform changes."))
            return

        # Apply changes in a transaction
        applied = 0
        with transaction.atomic():
            for r in candidates:
                ing = r.ingredient
                small_unit = "gm" if ing.unit == "kg" else "ml"
                if mode == "set_unit":
                    r.quantity_unit = small_unit
                else:
                    # convert numeric
                    r.quantity = (Decimal(r.quantity) / Decimal("1000")).quantize(Q2)
                    r.quantity_unit = None
                r.save()
                applied += 1

        self.stdout.write(self.style.SUCCESS(f"Applied changes to {applied} rows."))