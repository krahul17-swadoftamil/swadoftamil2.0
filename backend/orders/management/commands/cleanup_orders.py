from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order


class Command(BaseCommand):
    help = 'Clean up old orders and related data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep orders (default: 30)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        # Delete old orders
        old_orders = Order.objects.filter(created_at__lt=cutoff_date)
        count = old_orders.count()

        if count > 0:
            old_orders.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} orders older than {days} days')
            )
        else:
            self.stdout.write('No old orders to delete')
