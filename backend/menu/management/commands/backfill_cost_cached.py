from django.core.management.base import BaseCommand
from menu.models import ComboItem


class Command(BaseCommand):
    help = "Backfill `cost_cached` for all ComboItem rows using compute_cost()"

    def handle(self, *args, **options):
        qs = ComboItem.objects.select_related("prepared_item").all()
        total = qs.count()
        self.stdout.write(f"Backfilling cost_cached for {total} ComboItem rows...")
        updated = 0
        for i, item in enumerate(qs, start=1):
            try:
                value = item.compute_cost()
                # Use queryset update to avoid calling save() hooks repeatedly
                ComboItem.objects.filter(pk=item.pk).update(cost_cached=value)
                updated += 1
            except Exception as e:
                self.stderr.write(f"Failed to compute for ComboItem {item.pk}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Backfilled {updated}/{total} rows."))
