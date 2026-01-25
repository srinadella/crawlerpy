#!/usr/bin/env python3
"""Test the API endpoints."""

import requests
from app.models import SessionLocal, User
from app.auth import create_access_token

# Get editor user
db = SessionLocal()
user = db.query(User).filter(User.username == 'editor').first()
if user:
    token = create_access_token(user.id)
    print(f'✓ Token created: {token[:30]}...')
    
    # Test POST endpoint
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': 'Test Crawler 2',
        'description': 'Test description',
        'seed_urls': ['https://example.com'],
        'enabled': True
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/api/crawlers',
            json=data,
            headers=headers,
            timeout=5
        )
        print(f'✓ POST /api/crawlers returned: {response.status_code}')
        if response.status_code == 201:
            print(f'✓ Crawler created successfully!')
            result = response.json()
            print(f'  Name: {result.get("name")}')
            print(f'  ID: {result.get("id")}')
        else:
            print(f'✗ Unexpected status code')
            print(f'Response: {response.text}')
    except Exception as e:
        print(f'✗ Error: {e}')
else:
    print('✗ Editor user not found')

db.close()
