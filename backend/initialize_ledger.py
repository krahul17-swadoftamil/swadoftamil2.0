#!/usr/bin/env python
"""
Initialize opening stock ledger entries for existing ingredients
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from ingredients.models import Ingredient, IngredientStockLedger

def initialize_ledger():
    print("Initializing Ingredient Stock Ledger...")
    
    ingredients = Ingredient.objects.all()
    count = 0
    
    for ingredient in ingredients:
        # Check if opening entry already exists
        if not ingredient.stock_ledger.filter(change_type=IngredientStockLedger.OPENING).exists():
            # Create opening stock entry
            current_stock = ingredient._stock_qty  # Use the cached field
            if current_stock > 0:
                IngredientStockLedger.objects.create(
                    ingredient=ingredient,
                    change_type=IngredientStockLedger.OPENING,
                    quantity_change=current_stock,
                    unit=ingredient.unit,
                    note="Opening stock from migration"
                )
                count += 1
                print(f"Created opening entry for {ingredient.name}: {current_stock} {ingredient.unit}")
    
    print(f"Initialized ledger for {count} ingredients")

if __name__ == "__main__":
    initialize_ledger()