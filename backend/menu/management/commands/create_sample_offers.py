from django.core.management.base import BaseCommand
from django.utils import timezone
from menu.models import MarketingOffer

class Command(BaseCommand):
    help = 'Create sample marketing offers for testing'

    def handle(self, *args, **options):
        # Clear existing offers
        MarketingOffer.objects.all().delete()

        # Create sample offers
        offers_data = [
            {
                'title': 'Pongal Special Offer',
                'description': 'Celebrate Pongal with our special discount on all breakfast combos',
                'short_text': '🥳 Pongal Offer! Flat 15% off all Idli Boxes this week!',
                'discount_percentage': 15,
                'priority': 10,
                'is_active': True,
            },
            {
                'title': 'New Customer Welcome',
                'description': 'Get ₹50 off on your first order with us',
                'short_text': '🌟 New Customer? Get ₹50 off on your first order!',
                'discount_amount': 50.00,
                'priority': 8,
                'is_active': True,
            },
            {
                'title': 'Happy Hour Deal',
                'description': '20% off on all Combos between 2-4 PM',
                'short_text': '⏰ Happy Hour! 20% off on all Combos between 2-4 PM',
                'discount_percentage': 20,
                'priority': 6,
                'is_active': True,
            },
            {
                'title': 'Snack Combo Deal',
                'description': 'Buy 2 Get 1 Free on all Snack Add-ons',
                'short_text': '🎁 Buy 2 Get 1 Free on all Snack Add-ons today!',
                'priority': 5,
                'is_active': True,
            },
        ]

        for offer_data in offers_data:
            offer = MarketingOffer.objects.create(**offer_data)
            self.stdout.write(
                self.style.SUCCESS(f'Created offer: {offer.title}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(offers_data)} marketing offers')
        )