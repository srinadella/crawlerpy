#!/usr/bin/env python3
import subprocess
import time

print("🔄 Long-running test (retrying every 10 seconds for 2 minutes)...\n")

for i in range(12):
    cmd = ['curl', '-s', '-u', 'sri:7wrVFEn9N.zT', 'https://search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com/']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    response = result.stdout
    
    if 'cluster_name' in response:
        print(f"✅ SUCCESS at attempt {i+1}!")
        print(response[:200])
        break
    elif 'User: anonymous' in response:
        print(f"  Attempt {i+1}: Still anonymous (policy syncing...)")
    else:
        print(f"  Attempt {i+1}: {response[:100]}")
    
    if i < 11:
        time.sleep(10)
    else:
        print("\n❌ Could not connect after 2 minutes")
        print("\nPossible issues:")
        print("  1. Master user 'sri' might have incorrect credentials")
        print("  2. Domain might need explicit restart in AWS Console")
        print("  3. Fine-grained access control (FGAC) might be blocking access")
