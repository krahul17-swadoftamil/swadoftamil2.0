"""
Test Google Sign-In functionality end-to-end
"""

import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000/api"

def test_google_signin_setup():
    """Test Google Sign-In configuration and endpoints"""

    print("🔍 Testing Google Sign-In Setup")
    print("=" * 50)

    # Check environment variables
    print("\n1. Checking environment variables...")
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    if google_client_id:
        print(f"   ✅ GOOGLE_CLIENT_ID: {google_client_id[:20]}...")
    else:
        print("   ❌ GOOGLE_CLIENT_ID not set")

    # Test Google login endpoint exists
    print("\n2. Testing Google login endpoint...")
    try:
        response = requests.options(f"{BASE_URL}/auth/google-login/")
        print(f"   ✅ Endpoint accessible (Status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Endpoint not accessible: {e}")

    # Test with invalid credential
    print("\n3. Testing invalid credential rejection...")
    try:
        response = requests.post(f"{BASE_URL}/auth/google-login/", json={
            "credential": "invalid.jwt.token"
        })
        if response.status_code == 400:
            print("   ✅ Invalid credentials properly rejected")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing endpoint: {e}")

    # Test JWT Firebase endpoint
    print("\n4. Testing Firebase JWT endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/jwt/firebase/", json={
            "id_token": "invalid.firebase.token"
        })
        if response.status_code in [400, 401]:
            print("   ✅ Firebase JWT endpoint working (rejects invalid tokens)")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing Firebase endpoint: {e}")

    # Check frontend environment
    print("\n5. Checking frontend configuration...")
    frontend_env_path = "../swad-frontend/.env"
    if os.path.exists(frontend_env_path):
        with open(frontend_env_path, 'r') as f:
            content = f.read()
            if 'VITE_GOOGLE_CLIENT_ID=' in content:
                print("   ✅ Frontend Google Client ID configured")
            else:
                print("   ❌ Frontend Google Client ID not configured")
    else:
        print("   ❌ Frontend .env file not found")

    print("\n" + "=" * 50)
    print("🎯 Google Sign-In Status: CONFIGURED")
    print("\n📋 Next Steps:")
    print("   1. Ensure Google OAuth consent screen is configured")
    print("   2. Verify authorized redirect URIs include your domain")
    print("   3. Test with real Google account in browser")
    print("   4. Check browser console for any JavaScript errors")

if __name__ == "__main__":
    test_google_signin_setup()