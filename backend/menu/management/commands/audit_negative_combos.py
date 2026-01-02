from django.core.management.base import BaseCommand
from decimal import Decimal
from menu.models import Combo


class Command(BaseCommand):
    help = 'Audit combos and report negative-profit combos with contributing prepared items.'

    def handle(self, *args, **options):
        combos = Combo.objects.prefetch_related('items__prepared_item')
        negative = []
        for c in combos:
            try:
                profit = c.profit()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Combo {c.name} error computing profit: {e}"))
                continue

            if profit < Decimal('0.00'):
                # build breakdown
                breakdown = []
                    for item in c.items.select_related('prepared_item'):
                    pi = item.prepared_item
                    # use cost_per_unit (cost for single base unit) and item_cost
                    pi_cost = getattr(pi, 'cost_per_unit', None)
                    qty = item.quantity
                    contribution = getattr(item, 'cost_cached', None)
                    breakdown.append({
                        'prepared_item': pi.name,
                        'qty': qty,
                        'unit': pi.get_unit_display() if hasattr(pi, 'get_unit_display') else pi.unit,
                        'cost_per_unit': str(pi_cost) if pi_cost is not None else None,
                        'contribution': str(contribution) if contribution is not None else None,
                    })

                negative.append({'combo': c.name, 'selling_price': str(c.selling_price), 'profit': str(profit), 'breakdown': breakdown})

        if not negative:
            self.stdout.write(self.style.SUCCESS('No negative-profit combos found.'))
            return

        for entry in negative:
            self.stdout.write(self.style.ERROR(f"Combo: {entry['combo']}  Selling: {entry['selling_price']}  Profit: {entry['profit']}"))
            self.stdout.write('Breakdown:')
            for line in entry['breakdown']:
                self.stdout.write(f" - {line['prepared_item']}: qty={line['qty']} {line['unit']}, cost_per_unit={line['cost_per_unit']}, contribution={line['contribution']}")
            self.stdout.write('')
