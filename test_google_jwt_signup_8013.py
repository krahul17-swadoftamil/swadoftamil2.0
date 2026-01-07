#!/usr/bin/env python3
"""
Test Google JWT signup flow on port 8013
"""
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8013'

def test_status():
    """Test status endpoint"""
    print('1. Testing status endpoint...')
    try:
        r = requests.get(f'{BASE_URL}/api/status/', timeout=5)
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Response: {r.json()}')
        return r.status_code == 200
    except Exception as e:
        print(f'   ✗ Error: {e}')
        return False

def test_google_jwt_firebase():
    """Test Google JWT Firebase endpoint"""
    print('\n2. Testing Google JWT Firebase endpoint...')
    try:
        r = requests.post(f'{BASE_URL}/api/auth/jwt/firebase/', json={'id_token': 'google-jwt-token-here'}, timeout=5)
        print(f'   ✓ Status: {r.status_code}')
        print(f'   Response: {r.json()}')
        return r.status_code == 200
    except Exception as e:
        print(f'   ✗ Error: {e}')
        return False

def test_standard_jwt():
    """Test standard JWT create endpoint"""
    print('\n3. Testing standard JWT create endpoint...')
    try:
        r = requests.post(f'{BASE_URL}/api/auth/jwt/create/', json={'username': 'test', 'password': 'test'}, timeout=5)
        print(f'   Status: {r.status_code}')
        if r.status_code == 200:
            print(f'   ✓ Response: {r.json()}')
        else:
            print(f'   Response: {r.json()}')
        return r.status_code in [200, 401]
    except Exception as e:
        print(f'   ✗ Error: {e}')
        return False

if __name__ == '__main__':
    print('Testing Google JWT Signup Flow')
    print('=' * 60)
    
    results = {
        'status_endpoint': test_status(),
        'google_jwt_firebase': test_google_jwt_firebase(),
        'standard_jwt_create': test_standard_jwt(),
    }
    
    print('\n' + '=' * 60)
    print('Results Summary:')
    for test_name, passed in results.items():
        status = '✓ PASS' if passed else '✗ FAIL'
        print(f'  {status:8} - {test_name}')
    
    all_passed = all(results.values())
    print('\n' + ('✓ All tests passed!' if all_passed else '✗ Some tests failed'))
