#!/usr/bin/env python3
"""Diagnose OpenSearch connectivity issues."""

import time
import subprocess
import sys

def test_connection(attempt=1, max_attempts=5):
    """Test connection with retries."""
    print(f"\n🔄 Attempt {attempt}/{max_attempts}...")
    
    cmd = [
        'curl', '-s', '-u', 'sri:7wrVFEn9N.zT',
        'https://search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com/'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        response = result.stdout
        
        if 'cluster_name' in response:
            print("✅ SUCCESS! Connected to OpenSearch")
            print(f"   Response: {response[:100]}")
            return True
        elif 'User: anonymous' in response:
            print("⏳ Policy change in progress... OpenSearch still showing anonymous user")
            print(f"   This usually syncs within 1-2 minutes")
            if attempt < max_attempts:
                print(f"   Retrying in 15 seconds...")
                time.sleep(15)
                return test_connection(attempt + 1, max_attempts)
            else:
                print("❌ Max retries reached. OpenSearch domain policy may not be properly configured.")
                return False
        else:
            print(f"❌ Unexpected response: {response[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing AWS OpenSearch Connectivity...")
    print(f"   Host: search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com")
    print(f"   User: sri")
    print(f"   Password: ***")
    
    if test_connection():
        print("\n✅ You can now start the crawler application!")
        print("   bash run.sh")
        sys.exit(0)
    else:
        print("\n⚠️  Connection issues detected. Possible solutions:")
        print("   1. Wait 2-3 minutes for domain policy to sync")
        print("   2. Verify master user credentials in AWS OpenSearch console")
        print("   3. Check domain status is 'Active' in AWS console")
        print("   4. Try restarting the domain if changes don't apply")
        sys.exit(1)
