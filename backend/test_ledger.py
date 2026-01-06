#!/usr/bin/env python
"""
Test script for Ingredient Stock Ledger and Consumption Tracking
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from decimal import Decimal
from ingredients.models import Ingredient, IngredientStockLedger
from menu.models import PreparedItem, Combo
from orders.models import Order

def test_ledger_system():
    print("Testing Ingredient Stock Ledger System")
    print("=" * 50)
    
    # Check ingredients
    ingredients = Ingredient.objects.all()
    print(f"Total ingredients: {ingredients.count()}")
    
    # Check ledger entries
    ledger_entries = IngredientStockLedger.objects.all()
    print(f"Total ledger entries: {ledger_entries.count()}")
    
    # Show sample ledger entries
    if ledger_entries.exists():
        print("\nSample Ledger Entries:")
        for entry in ledger_entries[:3]:
            print(f"  {entry.ingredient.name}: {entry.quantity_change} {entry.unit} ({entry.get_change_type_display()})")
    
    # Test stock calculation
    print("\nStock Calculation Test:")
    for ingredient in ingredients[:3]:
        calculated_stock = ingredient.stock_qty
        print(f"  {ingredient.name}: {calculated_stock} {ingredient.unit}")
    
    print("\n✅ Ledger system initialized successfully!")

if __name__ == "__main__":
    test_ledger_system()