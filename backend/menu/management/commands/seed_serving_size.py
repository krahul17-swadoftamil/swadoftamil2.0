from django.core.management.base import BaseCommand

from menu.models import PreparedItem


class Command(BaseCommand):
    help = "Seed common serving_size values for prepared items by name (idli/sambar/chutney)."

    MAPPINGS = {
        "idli": ("pcs", 1),
        "sambar": ("ml", 100),
        "chutney": ("ml", 50),
    }

    def handle(self, *args, **options):
        for fragment, (unit, size) in self.MAPPINGS.items():
            qs = PreparedItem.objects.filter(name__icontains=fragment)
            updated = 0
            for pi in qs:
                changed = False
                # Set unit if it differs (safe to authoritatively set from admin intent)
                if pi.unit != unit:
                    pi.unit = unit
                    changed = True
                # Set serving_size when missing or different
                if pi.serving_size != size:
                    pi.serving_size = size
                    changed = True
                if changed:
                    pi.save(update_fields=[f for f in ("unit", "serving_size") if getattr(pi, f) is not None])
                    updated += 1

            self.stdout.write(self.style.SUCCESS(f"Updated {updated} PreparedItem(s) matching '{fragment}'"))
