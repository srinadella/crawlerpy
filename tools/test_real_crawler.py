#!/usr/bin/env python3
"""Test real crawler execution - fixed version."""

import requests
import json
import time

def test_crawler():
    # Login
    print("1. Logging in...")
    login = requests.post("http://localhost:8000/api/auth/login", 
        data={"username": "admin", "password": "admin123"})
    
    if login.status_code != 200:
        print(f"Login failed: {login.status_code}")
        return
    
    token = login.json()["access_token"]
    print("OK - Logged in successfully\n")
    
    # Get crawler configs
    print("2. Fetching crawler configs...")
    crawlers = requests.get("http://localhost:8000/api/crawlers",
        headers={"Authorization": f"Bearer {token}"})
    
    if crawlers.status_code != 200:
        print(f"Failed to fetch crawlers: {crawlers.status_code}")
        return
    
    crawlers_data = crawlers.json()
    if not crawlers_data:
        print("No crawler configs found")
        return
    
    config_id = crawlers_data[0]["id"]
    config_name = crawlers_data[0]["name"]
    print(f"OK - Found crawler: {config_name} (ID: {config_id})")
    print(f"   Seed URLs: {crawlers_data[0].get('seed_urls', [])}\n")
    
    # Create a crawl job
    print("3. Starting crawl job...")
    response = requests.post(f"http://localhost:8000/api/jobs/{config_id}/start",
        headers={"Authorization": f"Bearer {token}"})
    
    if response.status_code != 201:
        print(f"Failed to start job: {response.status_code}")
        print(response.json())
        return
    
    job = response.json()
    job_id = job["id"]
    print(f"OK - Crawl job created: {job_id}")
    print(f"   Initial status: {job['status']}\n")
    
    # Check job status
    print("4. Monitoring job execution (checking for 60 seconds)...")
    start_time = time.time()
    for i in range(120):  # Check for up to 2 minutes
        time.sleep(1)
        job_response = requests.get(f"http://localhost:8000/api/jobs/detail/{job_id}",
            headers={"Authorization": f"Bearer {token}"})
        
        if job_response.status_code == 200:
            job = job_response.json()
            status = job["status"]
            progress = job.get("progress", 0)
            urls = job.get("urls_crawled", 0)
            docs = job.get("documents_indexed", 0)
            
            print(f"   [{i+1:2d}s] Status: {status:12} | Progress: {progress:3}% | URLs: {urls:3} | Docs: {docs:3}")
            
            if status in ["completed", "failed"]:
                elapsed = time.time() - start_time
                print(f"\nOK - Job finished in {elapsed:.1f} seconds")
                print(f"   Final status: {status}")
                print(f"   URLs crawled: {urls}")
                print(f"   Documents indexed: {docs}")
                if job.get("error_details"):
                    print(f"   Error: {job['error_details']}")
                break
        else:
            print(f"   Failed to get job status: {job_response.status_code}")

if __name__ == "__main__":
    test_crawler()
