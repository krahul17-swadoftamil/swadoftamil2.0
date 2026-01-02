from decimal import Decimal

from django.core.management.base import BaseCommand

from menu.models import PreparedItem


class Command(BaseCommand):
    help = "Set serving_size for named PreparedItems"

    def add_arguments(self, parser):
        parser.add_argument(
            "--names",
            type=str,
            required=True,
            help="Comma-separated prepared item names",
        )
        parser.add_argument(
            "--value",
            type=str,
            required=True,
            help="Serving size value to set (decimal)",
        )

    def handle(self, *args, **options):
        names = [n.strip() for n in options["names"].split(",") if n.strip()]
        val = Decimal(options["value"])
        for name in names:
            try:
                p = PreparedItem.objects.get(name=name)
                p.serving_size = val
                p.save()
                self.stdout.write(self.style.SUCCESS(f"Updated {name} id={p.id} serving_size={p.serving_size}"))
            except PreparedItem.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"PreparedItem not found: {name}"))
