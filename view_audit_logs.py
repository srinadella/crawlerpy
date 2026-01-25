#!/usr/bin/env python3
"""View audit logs from command line."""

import sys
from app.audit import get_audit_logs
from datetime import datetime

def main():
    """Display recent audit logs."""
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    
    logs = get_audit_logs(limit=limit)
    
    print(f"\n{'='*100}")
    print(f"AUDIT LOGS ({logs['total']} total)")
    print(f"{'='*100}\n")
    
    for log in logs['logs']:
        timestamp = log['timestamp']
        user = f"{log['username']} (ID: {log['user_id']})"
        action = log['action']
        resource = f"{log['resource_type']}: {log['resource_name']}"
        status = "✓ SUCCESS" if log['status'] == 'success' else "✗ ERROR"
        
        print(f"[{timestamp}] {status}")
        print(f"  User: {user}")
        print(f"  Action: {action}")
        print(f"  Resource: {resource}")
        
        if log['details']:
            print(f"  Details: {log['details']}")
        
        if log['error_message']:
            print(f"  Error: {log['error_message']}")
        
        print()
    
    if not logs['logs']:
        print("No audit logs found.")
    
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
