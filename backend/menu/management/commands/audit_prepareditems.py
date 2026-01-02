from decimal import Decimal

from django.core.management.base import BaseCommand

from menu.models import PreparedItem

ZERO = Decimal("0.00")


class Command(BaseCommand):
    help = "List PreparedItems with missing/zero serving_size or zero cost_price"

    def handle(self, *args, **options):
        issues = []
        for p in PreparedItem.objects.all():
            try:
                serving = getattr(p, 'serving_size', None)
                cost = getattr(p, 'cost_price', ZERO) or ZERO
                problems = []
                if serving in (None, '', 0) or (hasattr(serving, 'quantize') and serving == 0):
                    problems.append('serving_size=0/missing')
                if cost == ZERO:
                    problems.append('cost_price=0')
                if problems:
                    issues.append((p.id, p.name, serving, cost, problems))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inspecting {p}: {e}"))

        if not issues:
            self.stdout.write(self.style.SUCCESS('No problematic PreparedItems found.'))
            return

        self.stdout.write('Problematic PreparedItems:')
        for pid, name, serving, cost, problems in issues:
            self.stdout.write(f"- id={pid} name={name} serving={serving} cost={cost} issues={problems}")
