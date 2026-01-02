from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.apps import apps
import time

# Configure models to backfill: (app_label, model_name, prefix, field, width)
TARGETS = [
    ("ingredients", "Ingredient", "IG", "code", 2),
    ("menu", "PreparedItem", "PI", "code", 4),
    ("menu", "Combo", "CB", "code", 4),
    ("snacks", "Snack", "SN", "code", 4),
        ("accounts", "Customer", "CUST", "code", 4),
        ("accounts", "UserCode", "USR", "code", 4),
    ("accounts", "Employee", "EMP", "code", 4),
    ("orders", "Order", "SOT", "code", 2),
]


class Command(BaseCommand):
    help = "Backfill missing `code` fields for configured models safely."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without saving.")
        parser.add_argument("--delay", type=float, default=0.0, help="Delay (seconds) between saves to reduce race conditions.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        delay = options["delay"]

        from core.utils import generate_and_set_code

        for app_label, model_name, prefix, field, width in TARGETS:
            Model = apps.get_model(app_label, model_name)
            if Model is None:
                self.stdout.write(self.style.WARNING(f"Model not found: {app_label}.{model_name}. Skipping."))
                continue

            qs = Model.objects.filter(**{f"{field}__isnull": True}) | Model.objects.filter(**{f"{field}": ""})
            qs = qs.order_by("pk")
            total = qs.count()
            if total == 0:
                self.stdout.write(self.style.SUCCESS(f"{app_label}.{model_name}: no missing codes."))
                continue

            self.stdout.write(f"Backfilling {total} rows for {app_label}.{model_name} -> prefix={prefix}")

            processed = 0
            failures = []

            for obj in qs.iterator():
                processed += 1
                try:
                    if getattr(obj, field):
                        continue

                    # Attempt to set code and save with retries on IntegrityError
                    attempts = 0
                    while attempts < 5:
                        attempts += 1
                        try:
                            code = generate_and_set_code(obj, prefix, field, width)
                            if dry_run:
                                self.stdout.write(f"[DRY] {app_label}.{model_name} pk={obj.pk} -> {code}")
                                break

                            # Use transaction to try to save safely
                            with transaction.atomic():
                                obj.save()

                            self.stdout.write(self.style.SUCCESS(f"{app_label}.{model_name} pk={obj.pk} -> {getattr(obj, field)}"))
                            break
                        except IntegrityError as e:
                            # Possible race condition; retry after tiny backoff
                            self.stdout.write(self.style.WARNING(f"IntegrityError saving pk={obj.pk}, attempt={attempts}, retrying..."))
                            time.sleep(0.1 * attempts)
                            # reload object from DB to avoid stale state
                            obj = Model.objects.get(pk=obj.pk)
                            continue

                    else:
                        failures.append(obj.pk)
                        self.stdout.write(self.style.ERROR(f"Failed to backfill pk={obj.pk} after retries."))

                    if delay and not dry_run:
                        time.sleep(delay)

                except Exception as e:
                    failures.append(obj.pk)
                    self.stdout.write(self.style.ERROR(f"Error processing pk={obj.pk}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"Done backfilling {app_label}.{model_name}: processed={processed}, failures={len(failures)}"))

        self.stdout.write(self.style.SUCCESS("Backfill complete."))
