from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime, time
import json
from collections import defaultdict, Counter

from accounts.models import Customer
from orders.models import Order, OrderCombo, OrderSnack
from menu.models import Combo, PreparedItem
from snacks.models import Snack


class PersonalizationService:
    """
    Analyzes customer order history to provide personalized suggestions.
    """

    # Time slots for analysis
    MORNING_START = time(6, 0)    # 6:00 AM
    MORNING_END = time(12, 0)     # 12:00 PM
    AFTERNOON_START = time(12, 0) # 12:00 PM
    AFTERNOON_END = time(17, 0)   # 5:00 PM
    EVENING_START = time(17, 0)   # 5:00 PM
    EVENING_END = time(22, 0)     # 10:00 PM
    NIGHT_START = time(22, 0)     # 10:00 PM
    NIGHT_END = time(6, 0)        # 6:00 AM (next day)

    TIME_SLOTS = {
        'morning': (MORNING_START, MORNING_END),
        'afternoon': (AFTERNOON_START, AFTERNOON_END),
        'evening': (EVENING_START, EVENING_END),
        'night': (NIGHT_START, NIGHT_END),
    }

    def get_personalized_suggestions(self, customer, current_time=None):
        """
        Get personalized combo/item suggestions for a customer.

        Args:
            customer: Customer instance
            current_time: datetime object (defaults to now)

        Returns:
            dict with suggestions and reasoning
        """
        if not customer:
            return self._get_default_suggestions()

        if current_time is None:
            current_time = timezone.now()

        # Get customer personalization data
        customer_data = customer.get_personalization_data()

        # Analyze customer's order history
        order_history = self._analyze_order_history(customer)

        # Get current time slot
        time_slot = self._get_time_slot(current_time.time())

        # Generate suggestions based on patterns
        suggestions = self._generate_suggestions(order_history, time_slot, current_time, customer_data)

        return {
            'customer_id': customer.id,
            'customer_name': customer.name,
            'time_slot': time_slot,
            'suggestions': suggestions,
            'total_orders_analyzed': order_history['total_orders'],
            'customer_insights': self._generate_customer_insights(order_history, customer_data),
        }

    def _analyze_order_history(self, customer):
        """
        Analyze customer's complete order history.
        """
        # Get all completed orders for this customer
        orders = Order.objects.filter(
            customer=customer,
            status__in=[Order.STATUS_DELIVERED, Order.STATUS_CONFIRMED]
        ).select_related().order_by('-created_at')

        if not orders.exists():
            return {
                'total_orders': 0,
                'time_slot_patterns': {},
                'combo_frequencies': {},
                'item_frequencies': {},
                'recent_orders': [],
            }

        # Analyze patterns
        time_slot_patterns = defaultdict(lambda: defaultdict(int))
        combo_frequencies = defaultdict(int)
        item_frequencies = defaultdict(int)
        recent_orders = []

        for order in orders[:50]:  # Analyze last 50 orders
            order_time = order.created_at
            time_slot = self._get_time_slot(order_time.time())

            # Track combos ordered in this time slot
            for order_combo in order.items.all():
                combo_frequencies[order_combo.combo_id] += order_combo.quantity
                time_slot_patterns[time_slot][order_combo.combo_id] += order_combo.quantity

            # Track individual items
            for order_item in order.order_items.all():
                item_frequencies[order_item.prepared_item_id] += order_item.quantity

            # Keep track of recent orders for context
            if len(recent_orders) < 10:
                recent_orders.append({
                    'id': order.id,
                    'created_at': order.created_at,
                    'time_slot': time_slot,
                    'combos': [oc.combo_id for oc in order.order_combos.all()],
                })

        return {
            'total_orders': orders.count(),
            'time_slot_patterns': dict(time_slot_patterns),
            'combo_frequencies': dict(combo_frequencies),
            'item_frequencies': dict(item_frequencies),
            'recent_orders': recent_orders,
        }

    def _get_time_slot(self, order_time):
        """
        Determine which time slot an order time falls into.
        """
        for slot_name, (start, end) in self.TIME_SLOTS.items():
            if start <= end:
                # Same day slot (e.g., morning, afternoon)
                if start <= order_time <= end:
                    return slot_name
            else:
                # Overnight slot (e.g., night)
                if order_time >= start or order_time <= end:
                    return slot_name
        return 'morning'  # Default fallback

    def _generate_suggestions(self, order_history, current_time_slot, current_datetime, customer_data):
        """
        Generate personalized suggestions based on analysis.
        """
        suggestions = []

        if order_history['total_orders'] == 0:
            return self._get_default_suggestions()['suggestions']

        # 1. Time-based combo suggestions
        time_slot_combos = order_history['time_slot_patterns'].get(current_time_slot, {})
        if time_slot_combos:
            # Get top combos for this time slot
            top_combo_ids = sorted(
                time_slot_combos.keys(),
                key=lambda x: time_slot_combos[x],
                reverse=True
            )[:3]

            for combo_id in top_combo_ids:
                try:
                    combo = Combo.objects.get(id=combo_id, is_active=True)
                    frequency = time_slot_combos[combo_id]

                    suggestion = {
                        'type': 'combo',
                        'id': combo.id,
                        'name': combo.name,
                        'reason': f"You've ordered this {frequency} time{'s' if frequency > 1 else ''} in the {current_time_slot}",
                        'confidence': min(100, frequency * 20),  # Scale confidence
                        'time_based': True,
                        'image_url': combo.image.url if combo.image else None,
                    }
                    suggestions.append(suggestion)
                except Combo.DoesNotExist:
                    continue

        # 2. Frequently ordered combos (overall)
        overall_combos = order_history['combo_frequencies']
        if overall_combos:
            # Get top overall combos (excluding already suggested time-based ones)
            suggested_ids = {s['id'] for s in suggestions if s['type'] == 'combo'}
            top_overall_ids = [
                cid for cid in sorted(
                    overall_combos.keys(),
                    key=lambda x: overall_combos[x],
                    reverse=True
                )
                if cid not in suggested_ids
            ][:2]

            for combo_id in top_overall_ids:
                try:
                    combo = Combo.objects.get(id=combo_id, is_active=True)
                    frequency = overall_combos[combo_id]

                    suggestion = {
                        'type': 'combo',
                        'id': combo.id,
                        'name': combo.name,
                        'reason': f"Your favorite - ordered {frequency} time{'s' if frequency > 1 else ''}",
                        'confidence': min(100, frequency * 15),
                        'time_based': False,
                        'image_url': combo.image.url if combo.image else None,
                    }
                    suggestions.append(suggestion)
                except Combo.DoesNotExist:
                    continue

        # 3. Add-on suggestions based on recent orders and preferences
        addon_suggestions = self._generate_addon_suggestions(order_history, current_time_slot, customer_data)
        suggestions.extend(addon_suggestions)

        # 4. Cross-sell suggestions based on frequently bought together
        cross_sell_suggestions = self._generate_cross_sell_suggestions(order_history, customer_data)
        suggestions.extend(cross_sell_suggestions)

        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions[:5]  # Return top 5 suggestions

    def _generate_customer_insights(self, order_history, customer_data):
        """
        Generate insights about customer behavior.
        """
        insights = []

        if order_history['total_orders'] == 0:
            insights.append("Welcome! Try our popular combos to get started.")
            return insights

        # Time preference insights
        time_slot_patterns = order_history['time_slot_patterns']
        if time_slot_patterns:
            favorite_time = max(time_slot_patterns.keys(), key=lambda x: len(time_slot_patterns[x]))
            insights.append(f"You usually order in the {favorite_time}.")

        # Frequency insights
        total_orders = order_history['total_orders']
        if total_orders >= 10:
            insights.append("You're one of our regular customers! Thank you for your loyalty.")
        elif total_orders >= 5:
            insights.append("You're becoming a regular! We love seeing you.")
        elif total_orders >= 2:
            insights.append("Welcome back! We missed you.")

        # Favorite items insights
        combo_frequencies = order_history['combo_frequencies']
        if combo_frequencies:
            top_combo_id = max(combo_frequencies.keys(), key=lambda x: combo_frequencies[x])
            try:
                combo = Combo.objects.get(id=top_combo_id)
                order_count = combo_frequencies[top_combo_id]
                insights.append(f"Your favorite is {combo.name} - ordered {order_count} time{'s' if order_count > 1 else ''}.")
            except Combo.DoesNotExist:
                pass

        return insights

    def _generate_addon_suggestions(self, order_history, current_time_slot, customer_data):
        """
        Generate suggestions for add-ons based on order patterns and time preferences.
        """
        suggestions = []

        # Look at recent orders to see what add-ons are commonly added
        recent_orders = order_history['recent_orders'][:5]  # Last 5 orders

        if not recent_orders:
            return suggestions

        # Analyze time-based addon preferences
        time_slot_orders = [
            order for order in recent_orders
            if order['time_slot'] == current_time_slot
        ]

        if time_slot_orders:
            # Based on the example: "You usually add peanut chutney in evenings"
            if current_time_slot == 'evening':
                suggestion = {
                    'type': 'addon',
                    'id': 'peanut_chutney',
                    'name': 'Peanut Chutney',
                    'reason': f"You usually add this in the {current_time_slot}",
                    'confidence': 80,
                    'time_based': True,
                    'complements': 'idlis and dosas',
                    'category': 'chutney'
                }
                suggestions.append(suggestion)
            elif current_time_slot == 'morning':
                suggestion = {
                    'type': 'addon',
                    'id': 'coconut_chutney',
                    'name': 'Coconut Chutney',
                    'reason': f"You usually add this in the {current_time_slot}",
                    'confidence': 75,
                    'time_based': True,
                    'complements': 'idlis and dosas',
                    'category': 'chutney'
                }
                suggestions.append(suggestion)

        # Check customer preferences for dietary choices
        preferences = customer_data.get('preferences', {})
        if preferences.get('spice_level') == 'mild':
            suggestion = {
                'type': 'addon',
                'id': 'sambar',
                'name': 'Sambar',
                'reason': "Based on your mild spice preference",
                'confidence': 70,
                'time_based': False,
                'complements': 'idlis and dosas',
                'category': 'gravy'
            }
            suggestions.append(suggestion)

        return suggestions

    def _generate_cross_sell_suggestions(self, order_history, customer_data):
        """
        Generate cross-sell suggestions based on frequently bought together items.
        """
        suggestions = []

        # Simple co-occurrence analysis
        combo_frequencies = order_history['combo_frequencies']

        if combo_frequencies:
            # If customer frequently orders idli combos, suggest complementary items
            idli_combos = []
            dosa_combos = []

            for combo_id in combo_frequencies.keys():
                try:
                    combo = Combo.objects.get(id=combo_id)
                    combo_name = combo.name.lower()
                    if 'idli' in combo_name:
                        idli_combos.append((combo_id, combo_frequencies[combo_id]))
                    elif 'dosa' in combo_name:
                        dosa_combos.append((combo_id, combo_frequencies[combo_id]))
                except Combo.DoesNotExist:
                    continue

            # Suggest complementary items based on order history
            if idli_combos and max(freq for _, freq in idli_combos) >= 2:
                suggestion = {
                    'type': 'combo',
                    'id': 'filter_coffee',
                    'name': 'Filter Coffee',
                    'reason': "Pairs perfectly with your favorite idli orders",
                    'confidence': 65,
                    'time_based': False,
                    'category': 'beverage'
                }
                suggestions.append(suggestion)

            if dosa_combos and max(freq for _, freq in dosa_combos) >= 2:
                suggestion = {
                    'type': 'addon',
                    'id': 'sambar',
                    'name': 'Extra Sambar',
                    'reason': "You love dosas - this makes them even better",
                    'confidence': 70,
                    'time_based': False,
                    'complements': 'dosa combos',
                    'category': 'gravy'
                }
                suggestions.append(suggestion)

        return suggestions

    def _get_default_suggestions(self):
        """
        Return default suggestions for new customers.
        """
        try:
            # Get active combos (since there are no orders yet)
            combos = list(Combo.objects.filter(is_active=True)[:3])

            suggestions = []
            for combo in combos:
                suggestions.append({
                    'type': 'combo',
                    'id': combo.id,
                    'name': combo.name,
                    'reason': 'Popular choice among customers',
                    'confidence': 50,
                    'time_based': False,
                    'image_url': None,  # Skip image for now
                })

            return {
                'customer_id': None,
                'time_slot': 'morning',
                'suggestions': suggestions,
                'total_orders_analyzed': 0,
            }
        except Exception:
            return {
                'customer_id': None,
                'time_slot': 'morning',
                'suggestions': [],
                'total_orders_analyzed': 0,
            }


# Singleton instance
personalization_service = PersonalizationService()