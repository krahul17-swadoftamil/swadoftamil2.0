import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Now we can import Django models and test
from menu.models import SubscriptionPlan

print("Testing subscription plans from database:")
plans = SubscriptionPlan.objects.filter(is_active=True)
print(f"Found {plans.count()} active subscription plans:")
for plan in plans:
    print(f"- {plan.name}: ₹{plan.base_price} ({plan.plan_type})")
    print(f"  Discounted price: ₹{plan.get_discounted_price(30)}")

print("\nDatabase test completed successfully!")