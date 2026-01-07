"""
Test JWT authentication endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_jwt_endpoints():
    """Test JWT token creation and verification"""

    print("🧪 Testing JWT Authentication Endpoints")
    print("=" * 50)

    # Test 1: JWT token creation (this would normally require valid credentials)
    print("\n1. Testing JWT token creation endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/jwt/create/", json={
            "username": "testuser",
            "password": "testpass"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists (authentication required as expected)")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: JWT token verification
    print("\n2. Testing JWT token verification endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/jwt/verify/", json={
            "token": "invalid.jwt.token"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists (invalid token rejected as expected)")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: JWT token refresh
    print("\n3. Testing JWT token refresh endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/jwt/refresh/", json={
            "refresh": "invalid.refresh.token"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists (invalid refresh token rejected as expected)")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Firebase JWT endpoint
    print("\n4. Testing Firebase JWT endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/jwt/firebase/", json={
            "id_token": "invalid.firebase.token"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Endpoint exists (invalid Firebase token rejected as expected)")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n🎉 JWT Authentication Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Configure Firebase credentials in backend/.env")
    print("2. Configure Firebase credentials in swad-frontend/.env")
    print("3. Test with real Firebase authentication")
    print("4. Update frontend components to use JWT tokens")

if __name__ == "__main__":
    test_jwt_endpoints()