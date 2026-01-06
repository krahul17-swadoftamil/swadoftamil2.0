#!/usr/bin/env python
"""
Test script for PreparedItem production modes
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from menu.models import PreparedItem
from ingredients.models import Ingredient

def test_production_modes():
    print("Testing PreparedItem Production Modes")
    print("=" * 50)
    
    # Get some existing prepared items
    items = PreparedItem.objects.all()[:3]
    
    for item in items:
        print(f"\n{item.name}:")
        print(f"  Production Mode: {item.get_production_mode_display()}")
        print(f"  Serving Size: {item.serving_size} {item.unit}")
        if item.batch_output_quantity:
            print(f"  Batch Output: {item.batch_output_quantity} {item.unit}")
        print(f"  Available Quantity: {item.available_quantity}")
        print(f"  Breakdown: {item.availability_breakdown}")

if __name__ == "__main__":
    test_production_modes()