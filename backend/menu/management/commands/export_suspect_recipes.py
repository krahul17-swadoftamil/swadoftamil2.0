from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import csv
import os

from menu.models import PreparedItemRecipe


class Command(BaseCommand):
    help = "Export suspect PreparedItemRecipe rows (likely unit mismatches) to CSV for review"

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-threshold",
            type=float,
            default=10.0,
            help="Numeric threshold above which values for kg/ltr base units are considered suspicious (default: 10)",
        )

    def handle(self, *args, **options):
        threshold = options.get("min_threshold")

        qs = PreparedItemRecipe.objects.select_related("ingredient", "prepared_item").all()

        now = timezone.now().strftime("%Y%m%d-%H%M%S")
        reports_dir = getattr(settings, "BASE_DIR", ".")
        reports_dir = os.path.join(reports_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        out_path = os.path.join(reports_dir, f"suspect_recipes_{now}.csv")

        headers = [
            "recipe_id",
            "prepared_item",
            "ingredient",
            "ingredient_base_unit",
            "quantity",
            "quantity_unit",
            "current_interpretation_cost",
            "alt_small_unit_cost",
            "suspect_reason",
        ]

        rows = []
        for r in qs:
            ing = r.ingredient
            q = float(r.quantity or 0)
            q_unit = r.quantity_unit or ""

            current_cost = None
            alt_cost = None
            reason = ""

            try:
                current_cost = str(r.ingredient_cost)
            except Exception:
                current_cost = "ERROR"

            # Heuristic: if ingredient base is kg or ltr, and quantity is large (> threshold)
            # and recipe.quantity_unit is blank, it's likely that admin entered grams/ml.
            if ing.unit in ("kg", "ltr") and not r.quantity_unit and q > threshold:
                reason = "Likely entered in grams/ml while ingredient base is kg/ltr"
                # alt_small_unit: convert using gm or ml
                small_unit = "gm" if ing.unit == "kg" else "ml"
                try:
                    alt_cost = str(ing.cost_for_quantity(r.quantity, small_unit))
                except Exception:
                    alt_cost = "ERROR"

            # Additional heuristic: quantity_unit explicitly provided but inconsistent
            if r.quantity_unit and r.quantity_unit in ("gm", "ml"):
                # if ingredient base is pcs, flag
                if ing.unit == "pcs":
                    if reason:
                        reason += "; "
                    reason += "Recipe uses gm/ml but ingredient stored as pcs"

            if reason:
                rows.append([
                    r.id,
                    r.prepared_item.name,
                    ing.name,
                    ing.unit,
                    str(r.quantity),
                    r.quantity_unit or "",
                    current_cost,
                    alt_cost or "",
                    reason,
                ])

        if not rows:
            self.stdout.write(self.style.SUCCESS("No suspect recipe rows found."))
            return

        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f"Wrote {len(rows)} suspect rows to {out_path}"))
