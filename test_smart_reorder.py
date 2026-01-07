#!/usr/bin/env python3
"""
Test Smart Re-Order Feature
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test.client import Client
from core.models import BreakfastWindow

def test_breakfast_window_api():
    """Test that the breakfast window API works"""
    client = Client()

    # Test the API endpoint
    response = client.get('/api/system/breakfast-window/')
    print(f"API Status: {response.status_code}")

    if response.status_code == 200:
        import json
        data = response.json()
        print("API Response:")
        print(json.dumps(data, indent=2))

        # Verify required fields
        required_fields = ['is_open', 'status_label', 'status_message', 'opens_at', 'closes_at', 'next_open_at']
        for field in required_fields:
            if field in data:
                print(f"✓ {field}: {data[field]}")
            else:
                print(f"✗ Missing field: {field}")
    else:
        print(f"API Error: {response.content}")

def test_breakfast_window_model():
    """Test that the BreakfastWindow model works"""
    try:
        # Get the breakfast window
        bw = BreakfastWindow.objects.first()
        if bw:
            print(f"BreakfastWindow exists: {bw}")
            print(f"Is open now: {bw.is_open_now}")
            status = bw.get_current_status()
            print(f"Status: {status}")
        else:
            print("No BreakfastWindow found")

    except Exception as e:
        print(f"Model test failed: {e}")

if __name__ == '__main__':
    print("Testing Smart Re-Order Backend Integration...")
    print("=" * 50)

    test_breakfast_window_model()
    print()
    test_breakfast_window_api()

    print("\nSmart Re-Order feature backend test complete!")