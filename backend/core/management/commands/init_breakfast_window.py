from django.core.management.base import BaseCommand
from core.models import BreakfastWindow
from datetime import time


class Command(BaseCommand):
    help = 'Initialize default BreakfastWindow data'

    def handle(self, *args, **options):
        if BreakfastWindow.objects.exists():
            self.stdout.write('BreakfastWindow already exists, skipping initialization')
            return

        # Create default breakfast window: 6:00 AM - 10:00 AM
        breakfast_window = BreakfastWindow.objects.create(
            name="Breakfast Window",
            opens_at=time(6, 0),  # 6:00 AM
            closes_at=time(10, 0),  # 10:00 AM
            is_active=True,
            status_label="CLOSED",
            status_message="Fresh breakfast available daily"
        )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created BreakfastWindow: {breakfast_window}')
        )