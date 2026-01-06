from django.core.management.base import BaseCommand
from orders.services import process_scheduled_orders


class Command(BaseCommand):
    help = 'Process scheduled orders that are ready for preparation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            from orders.services import check_scheduled_orders
            scheduled_orders = check_scheduled_orders()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Found {scheduled_orders.count()} scheduled orders ready for processing'
                )
            )
            for order in scheduled_orders:
                self.stdout.write(
                    f'  Order {order.order_number}: scheduled for {order.scheduled_for}'
                )
        else:
            self.stdout.write('Processing scheduled orders...')
            process_scheduled_orders()
            self.stdout.write(
                self.style.SUCCESS('Successfully processed scheduled orders')
            )