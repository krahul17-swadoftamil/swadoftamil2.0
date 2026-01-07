#!/usr/bin/env python3
"""
Test script for JWT authentication endpoints
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8011"

def test_status_endpoint():
    """Test the basic status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/status/")
        print(f"Status endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✅ Status endpoint working")
            return True
        else:
            print(f"❌ Status endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False

def test_jwt_endpoints():
    """Test JWT token endpoints"""
    print("\n--- Testing JWT Endpoints ---")

    # Test token obtain endpoint (this will fail without Firebase token, but should return proper error)
    try:
        response = requests.post(f"{BASE_URL}/api/auth/jwt/create/")
        print(f"JWT create endpoint: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ JWT create endpoint error: {e}")

    # Test token refresh endpoint
    try:
        response = requests.post(f"{BASE_URL}/api/auth/jwt/refresh/")
        print(f"JWT refresh endpoint: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ JWT refresh endpoint error: {e}")

    # Test token verify endpoint
    try:
        response = requests.post(f"{BASE_URL}/api/auth/jwt/verify/")
        print(f"JWT verify endpoint: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ JWT verify endpoint error: {e}")

def main():
    print("Testing JWT Authentication Setup")
    print("=" * 40)

    # Test basic connectivity
    if not test_status_endpoint():
        print("❌ Server not responding. Exiting.")
        sys.exit(1)

    # Test JWT endpoints
    test_jwt_endpoints()

    print("\n✅ JWT endpoint testing completed")

if __name__ == "__main__":
    main()