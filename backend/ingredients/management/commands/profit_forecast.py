from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
import csv
import os
from datetime import datetime, timedelta

from menu.models import Combo
from orders.models import OrderCombo, Order


class Command(BaseCommand):
    help = 'Export combo profit history and simple sales forecast (moving average).' 

    def add_arguments(self, parser):
        parser.add_argument('--days-back', type=int, default=90)
        parser.add_argument('--forecast-days', type=int, default=7)
        parser.add_argument('--out-dir', type=str, default='backend/analytics/reports')

    def handle(self, *args, **options):
        days_back = options['days_back']
        forecast_days = options['forecast_days']
        out_dir = options['out_dir']
        os.makedirs(out_dir, exist_ok=True)

        now = timezone.now()
        start = now - timedelta(days=days_back)

        ts = now.strftime('%Y%m%dT%H%M%S')
        path = os.path.join(out_dir, f'profit_forecast_{ts}.csv')

        combos = Combo.objects.all()

        with open(path, 'w', newline='', encoding='utf-8') as cf:
            writer = csv.writer(cf)
            writer.writerow(['combo_id', 'combo_name', 'avg_daily_sales', f'predicted_{forecast_days}_day_sales', f'predicted_{forecast_days}_day_profit', 'historical_revenue', 'historical_profit'])

            for combo in combos:
                # aggregate daily sales for the combo over the window
                qs = OrderCombo.objects.filter(combo=combo, order__status=Order.STATUS_CONFIRMED, order__created_at__gte=start)
                total_qty = qs.aggregate(sum=Sum('quantity'))['sum'] or 0
                days = max(1, days_back)
                avg_daily = float(total_qty) / days

                predicted_total = avg_daily * forecast_days
                predicted_profit = predicted_total * float(combo.profit)

                # historical revenue/profit
                # revenue = sum(quantity * selling_price at order time) — order snapshot not stored here; approximate with current selling_price
                historical_revenue = float(total_qty) * float(combo.selling_price)
                historical_profit = float(total_qty) * float(combo.profit)

                writer.writerow([str(combo.id), combo.name, round(avg_daily, 3), round(predicted_total, 2), round(predicted_profit, 2), round(historical_revenue, 2), round(historical_profit, 2)])

        self.stdout.write(self.style.SUCCESS(f'Profit forecast written to {path}'))
