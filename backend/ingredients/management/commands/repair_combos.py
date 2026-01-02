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
    help = 'Suggest automated repairs for invalid combos (non-destructive).' 

    def add_arguments(self, parser):
        parser.add_argument('--out-dir', type=str, default='backend/analytics/reports')

    def handle(self, *args, **options):
        out_dir = options['out_dir']
        os.makedirs(out_dir, exist_ok=True)

        ts = timezone.now().strftime('%Y%m%dT%H%M%S')
        csv_path = os.path.join(out_dir, f'repair_combos_{ts}.csv')
        json_path = os.path.join(out_dir, f'repair_combos_{ts}.json')

        results = []

        with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            writer.writerow(['combo_id', 'combo_name', 'issue', 'suggestion', 'impact_cost_delta'])

            for combo in Combo.objects.prefetch_related('items__prepared_item__recipes__ingredient'):
                for item in combo.items.all():
                    pi = item.prepared_item
                    name = pi.name.strip()

                    # If forbidden sku, recommend manual review
                    if name not in ALLOWED_SKUS:
                        suggestion = 'MANUAL_REVIEW: unknown SKU. Consider mapping to allowed SKU or create correct PreparedItem.'
                        writer.writerow([str(combo.id), combo.name, f'Forbidden SKU: {name}', suggestion, ''])
                        results.append({'combo': combo.name, 'issue': f'Forbidden SKU: {name}', 'suggestion': suggestion})
                        continue

                    sku = ALLOWED_SKUS[name]

                    # Pack size repair suggestion
                    pack_size = sku['pack_size']
                    if not pi.serving_size or int(pi.serving_size) != pack_size:
                        suggestion = f'Set PreparedItem.serving_size to {pack_size} (pack size)'
                        # estimate cost delta
                        orig_cost = float(combo.total_cost)
                        # naive recompute: assume prepared item recipes scale to pack_size — keep same proportions
                        new_cost = orig_cost  # difficult to compute without adjusting recipes; leave blank
                        writer.writerow([str(combo.id), combo.name, f'Pack size mismatch for {name}', suggestion, ''])
                        results.append({'combo': combo.name, 'issue': f'Pack size mismatch: {name}', 'suggestion': suggestion})

                    # Quantity integer suggestion
                    try:
                        if float(item.quantity).is_integer() is False:
                            suggestion = f'Round quantity to nearest integer for {name} (was {item.quantity})'
                            writer.writerow([str(combo.id), combo.name, f'Non-integer quantity for {name}', suggestion, ''])
                            results.append({'combo': combo.name, 'issue': f'Non-integer quantity: {name}', 'suggestion': suggestion})
                    except Exception:
                        pass

        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump({'timestamp': ts, 'results': results}, jf, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Repair suggestions written: CSV {csv_path} JSON {json_path}'))
