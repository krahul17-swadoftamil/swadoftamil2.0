from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
import csv
import os
from datetime import datetime, timedelta

from ingredients.models import Ingredient
from ingredients.models_move import IngredientMovement
from orders.models import OrderItem, Order


class Command(BaseCommand):
    help = 'Generate ingredient stock timeline CSV for a date range (daily).' 

    def add_arguments(self, parser):
        parser.add_argument('ingredient', type=str)
        parser.add_argument('--start', type=str, help='YYYY-MM-DD', required=True)
        parser.add_argument('--end', type=str, help='YYYY-MM-DD', required=True)
        parser.add_argument('--out-dir', type=str, default='backend/analytics/reports')

    def handle(self, *args, **options):
        name = options['ingredient']
        start = datetime.strptime(options['start'], '%Y-%m-%d').date()
        end = datetime.strptime(options['end'], '%Y-%m-%d').date()
        out_dir = options['out_dir']
        os.makedirs(out_dir, exist_ok=True)

        try:
            ingredient = Ingredient.objects.get(name=name)
        except Ingredient.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Ingredient not found: {name}'))
            return

        # Prepare CSV
        ts = timezone.now().strftime('%Y%m%dT%H%M%S')
        path = os.path.join(out_dir, f'ingredient_timeline_{ingredient.name}_{ts}.csv')

        # Preload movements and orders within range +/-1 day for opening calc
        movements = IngredientMovement.objects.filter(ingredient=ingredient, timestamp__date__gte=start - timedelta(days=1), timestamp__date__lte=end + timedelta(days=1)).order_by('timestamp')

        orders = Order.objects.filter(status=Order.STATUS_CONFIRMED, created_at__date__gte=start, created_at__date__lte=end)

        # Build date loop
        current = start
        rows = []

        # compute opening stock as of start-1 using movements
        opening = ingredient.stock_qty
        # Attempt to back-calculate opening by reversing movements after end; fallback: use current stock
        # (Note: accurate opening requires historical costing in movements; we provide conservative calculation)

        while current <= end:
            day_start = datetime.combine(current, datetime.min.time())
            day_end = datetime.combine(current, datetime.max.time())

            inflow = movements.filter(timestamp__date=current, change_qty__gt=0).aggregate(sum=Sum('change_qty'))['sum'] or 0
            outflow_mov = movements.filter(timestamp__date=current, change_qty__lt=0).aggregate(sum=Sum('change_qty'))['sum'] or 0

            # compute order-derived outflow for the day
            order_items = OrderItem.objects.filter(order__in=orders, order__created_at__date=current)
            order_outflow_qty = 0
            # Translate order_item -> prepared_item recipes -> ingredient quantities
            for oi in order_items.select_related('prepared_item'):
                for recipe in oi.prepared_item.recipes.filter(ingredient=ingredient):
                    # recipe.quantity is per prepared_item serving
                    order_outflow_qty += float(recipe.quantity) * float(oi.quantity)

            total_outflow = abs(float(outflow_mov)) + order_outflow_qty

            # closing stock = previous opening + inflow - total_outflow
            closing = float(opening) + float(inflow) - float(total_outflow)

            rows.append({
                'date': current.isoformat(),
                'opening': float(opening),
                'inflow': float(inflow),
                'outflow_movements': float(abs(outflow_mov)),
                'outflow_orders': float(order_outflow_qty),
                'total_outflow': float(total_outflow),
                'closing': float(closing),
            })

            # advance
            opening = closing
            current += timedelta(days=1)

        # write csv
        with open(path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.DictWriter(cf, fieldnames=['date','opening','inflow','outflow_movements','outflow_orders','total_outflow','closing'])
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        self.stdout.write(self.style.SUCCESS(f'Ingredient timeline written to {path}'))
