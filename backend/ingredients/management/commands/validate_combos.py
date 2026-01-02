from django.core.management.base import BaseCommand
from django.utils import timezone
import csv
import json
import os

from menu.models import Combo


ALLOWED_SKUS = {
    'Idli': {'unit': 'pcs', 'pack_size': 1},
    'Sambar': {'unit': 'ml', 'pack_size': 100},
    'Coconut Chutney': {'unit': 'ml', 'pack_size': 50},
    'Peanut Chutney': {'unit': 'ml', 'pack_size': 50},
    'Tomato Onion Chutney': {'unit': 'ml', 'pack_size': 50},
}


class Command(BaseCommand):
    help = 'Validate combos against SKU and pack rules; recalc cost/profit.'

    def add_arguments(self, parser):
        parser.add_argument('--out-dir', type=str, default='backend/analytics/reports')

    def handle(self, *args, **options):
        out_dir = options['out_dir']
        os.makedirs(out_dir, exist_ok=True)

        timestamp = timezone.now().strftime('%Y%m%dT%H%M%S')
        csv_path = os.path.join(out_dir, f'validate_combos_{timestamp}.csv')
        json_path = os.path.join(out_dir, f'validate_combos_{timestamp}.json')

        results = []

        with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            writer.writerow(['combo_id', 'combo_name', 'status', 'issues', 'stored_total_cost', 'computed_cost', 'stored_profit', 'computed_profit'])

            for combo in Combo.objects.prefetch_related('items__prepared_item__recipes__ingredient'):
                issues = []

                # verify all items are allowed SKUs
                computed_cost = 0
                for item in combo.items.all():
                    pi = item.prepared_item
                    name = pi.name.strip()
                    if name not in ALLOWED_SKUS:
                        issues.append(f'Forbidden SKU: {name}')
                        continue

                    sku_info = ALLOWED_SKUS[name]
                    # unit check
                    unit_ok = (pi.unit == sku_info['unit'])
                    if not unit_ok:
                        issues.append(f'Unit mismatch for {name}: expected {sku_info["unit"]} got {pi.unit}')

                    # pack size check: prepared item serving_size must equal pack_size and quantity must be integer
                    try:
                        pack_size = sku_info['pack_size']
                        if not pi.serving_size or int(pi.serving_size) != pack_size:
                            issues.append(f'Pack size mismatch for {name}: expected {pack_size} got {pi.serving_size}')
                    except Exception:
                        issues.append(f'Invalid serving_size for {name}')

                    # quantity must be integer (no fractional packs)
                    try:
                        if float(item.quantity).is_integer() is False:
                            issues.append(f'Non-integer pack quantity for {name}: {item.quantity}')
                    except Exception:
                        issues.append(f'Invalid quantity for {name}: {item.quantity}')

                    # compute expected ingredient-based cost for this combo item
                    # sum prepared item recipe ingredient costs × item.quantity
                    pi_cost = 0
                    for recipe in pi.recipes.all():
                        ing = recipe.ingredient
                        qty = recipe.quantity * item.quantity
                        try:
                            c = ing.cost_for_quantity(qty, recipe.quantity_unit)
                        except Exception:
                            c = 0
                        pi_cost += float(c)
                    computed_cost += pi_cost

                stored_total_cost = float(combo.total_cost)
                stored_profit = float(combo.profit)
                computed_cost = round(computed_cost, 2)
                computed_profit = round(float(combo.selling_price) - computed_cost, 2)

                status = 'OK' if not issues else 'INVALID'

                writer.writerow([str(combo.id), combo.name, status, '; '.join(issues), stored_total_cost, computed_cost, stored_profit, computed_profit])

                results.append({
                    'id': str(combo.id),
                    'name': combo.name,
                    'status': status,
                    'issues': issues,
                    'stored_total_cost': stored_total_cost,
                    'computed_cost': computed_cost,
                    'stored_profit': stored_profit,
                    'computed_profit': computed_profit,
                })

        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump({'timestamp': timestamp, 'results': results}, jf, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Combo validation complete. CSV: {csv_path} JSON: {json_path}'))
