#!/usr/bin/env python3
"""
Test Google JWT signup flow
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8012'

def test_status():
    """Test status endpoint"""
    print('1. Testing status endpoint...')
    try:
        r = requests.get(f'{BASE_URL}/api/status/')
        print(f'   Status: {r.status_code}')
        print(f'   Response: {r.json()}')
        return r.status_code == 200
    except Exception as e:
        print(f'   Error: {e}')
        return False

def test_google_jwt_firebase():
    """Test Google JWT Firebase endpoint"""
    print('\n2. Testing Google JWT Firebase endpoint...')
    try:
        r = requests.post(f'{BASE_URL}/api/auth/jwt/firebase/', json={'id_token': 'google-jwt-token-here'})
        print(f'   Status: {r.status_code}')
        print(f'   Response: {r.json()}')
        return r.status_code == 200
    except Exception as e:
        print(f'   Error: {e}')
        return False

def test_standard_jwt():
    """Test standard JWT create endpoint"""
    print('\n3. Testing standard JWT create endpoint...')
    try:
        r = requests.post(f'{BASE_URL}/api/auth/jwt/create/', json={'username': 'test', 'password': 'test'})
        print(f'   Status: {r.status_code}')
        print(f'   Response: {r.json() if r.status_code == 200 else r.text[:200]}')
        return r.status_code in [200, 401]
    except Exception as e:
        print(f'   Error: {e}')
        return False

if __name__ == '__main__':
    print('Testing Google JWT Signup Flow')
    print('=' * 50)
    
    results = {
        'status': test_status(),
        'google_jwt': test_google_jwt_firebase(),
        'standard_jwt': test_standard_jwt(),
    }
    
    print('\n' + '=' * 50)
    print('Results:')
    for test_name, passed in results.items():
        status = '✓' if passed else '✗'
        print(f'  {status} {test_name}')
