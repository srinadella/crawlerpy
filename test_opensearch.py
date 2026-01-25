#!/usr/bin/env python3
"""Test OpenSearch connectivity with master user credentials."""

import os
import sys

print("=== Testing OpenSearch Connectivity ===\n")

# Check environment
print("✓ Environment variables:")
opensearch_user = os.environ.get('OPENSEARCH_USER')
opensearch_password = os.environ.get('OPENSEARCH_PASSWORD')
print(f"  OPENSEARCH_USER: {opensearch_user if opensearch_user else 'NOT SET'}")
print(f"  OPENSEARCH_PASSWORD: {'***' if opensearch_password else 'NOT SET'}")

# Test config
from app.config import settings
print(f"\n✓ Configuration loaded:")
print(f"  Host: {settings.OPENSEARCH_HOST}")
print(f"  Port: {settings.OPENSEARCH_PORT}")
print(f"  Scheme: {settings.OPENSEARCH_SCHEME}")
print(f"  User: {settings.OPENSEARCH_USER}")
print(f"  Verify Certs: {settings.OPENSEARCH_VERIFY_CERTS}")

# Test client
print(f"\n✓ Initializing OpenSearch client...")
try:
    from app.opensearch_client import OpenSearchClient
    client = OpenSearchClient()
    print("  Client initialized successfully")
except Exception as e:
    print(f"  Error initializing client: {e}")
    sys.exit(1)

# Try to connect
print(f"\n✓ Testing connection...")
try:
    info = client.client.info()
    print(f"\n✅ CONNECTED TO AWS OPENSEARCH!")
    print(f"  Cluster: {info.get('cluster_name', 'N/A')}")
    print(f"  Version: {info.get('version', {}).get('number', 'N/A')}")
    print(f"\n✅ OpenSearch is ready for crawling!")
except Exception as e:
    print(f"\n❌ Connection failed:")
    print(f"  Error: {str(e)[:300]}")
    sys.exit(1)
