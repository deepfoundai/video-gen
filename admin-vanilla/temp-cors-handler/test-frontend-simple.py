#!/usr/bin/env python3
"""
Simple test to check frontend and submit a job with audio
"""
import requests
import boto3
import json
import time
from datetime import datetime

# Configuration
API_URL = "https://l3erksseb4.execute-api.us-east-1.amazonaws.com/prod/v1"

print("🎬 Testing Frontend Audio Submission")
print("=" * 50)

# Step 1: Get auth token
print("\n1️⃣ Getting authentication token...")
cognito = boto3.client('cognito-idp', region_name='us-east-1')

try:
    auth_response = cognito.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        ClientId='7paapnr8fbkanimk5bgpriagmg',
        AuthParameters={
            'USERNAME': 'admin.test@deepfoundai.com',
            'PASSWORD': 'AdminTest123!'
        }
    )
    
    id_token = auth_response['AuthenticationResult']['IdToken']
    print("✅ Got auth token")
except Exception as e:
    print(f"❌ Auth failed: {e}")
    exit(1)

# Step 2: Submit job exactly as frontend would
print("\n2️⃣ Submitting job with audio (mimicking frontend)...")

# This is exactly what the frontend sends
job_data = {
    "prompt": f"Beautiful sunset over ocean waves - test {datetime.now().strftime('%H:%M:%S')}",
    "seconds": 5,
    "resolution": "720p",
    "tier": "fast",
    "provider": "auto",
    "feature": {
        "audio": True,
        "audioTier": "fast"
    }
}

print(f"Request body:\n{json.dumps(job_data, indent=2)}")

headers = {
    "Authorization": f"Bearer {id_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://video.deepfoundai.com"
}

try:
    response = requests.post(f"{API_URL}/jobs", json=job_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code in [200, 201]:
        job_id = response.json().get('jobId')
        print(f"\n✅ Job submitted successfully: {job_id}")
        
        # Step 3: Monitor job
        print("\n3️⃣ Monitoring job progress...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('Jobs-prod')
        
        for i in range(12):  # Monitor for 1 minute
            time.sleep(5)
            
            # Check job in database
            db_response = table.get_item(Key={'jobId': job_id})
            if 'Item' in db_response:
                job = db_response['Item']
                print(f"\n[{i+1}/12] Job status: {job.get('status')}")
                print(f"  - Has feature field: {'feature' in job}")
                if 'feature' in job:
                    print(f"  - Audio enabled: {job['feature'].get('audio', False)}")
                print(f"  - Audio status: {job.get('audioStatus', 'Not started')}")
                print(f"  - Has audioUrl: {'audioUrl' in job}")
                
                if job.get('audioUrl'):
                    print(f"\n✅ Audio generated successfully!")
                    print(f"  - Audio URL: {job['audioUrl'][:80]}...")
                    break
                elif job.get('audioStatus') == 'FAILED':
                    print(f"\n❌ Audio generation failed")
                    if job.get('audioError'):
                        print(f"  - Error: {job['audioError']}")
                    break
            
            # Also check via API
            api_response = requests.get(f"{API_URL}/jobs", headers=headers)
            if api_response.status_code == 200:
                jobs = api_response.json().get('jobs', [])
                api_job = next((j for j in jobs if j['jobId'] == job_id), None)
                if api_job and api_job.get('audioUrl'):
                    print(f"\n✅ API also returns audioUrl!")
                
    else:
        print(f"❌ Job submission failed")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("Test complete!")