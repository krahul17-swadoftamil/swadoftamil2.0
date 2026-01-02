from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compute and persist total_protein for all combos'

    def handle(self, *args, **options):
        from menu.models import Combo
        updated = 0

        for combo in Combo.objects.all():
            try:
                val = combo.compute_total_protein() if hasattr(combo, 'compute_total_protein') else getattr(combo, 'total_protein', None)
                if val is None:
                    continue
                if getattr(combo, 'total_protein', None) != val:
                    combo.total_protein = val
                    combo.save(update_fields=['total_protein'])
                    updated += 1
            except Exception as e:
                self.stderr.write(f"Skipping {combo}: {e}")

        self.stdout.write(self.style.SUCCESS(f'Updated total_protein for {updated} combo(s).'))
