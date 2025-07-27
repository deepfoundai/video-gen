#!/usr/bin/env python3
import boto3
import json
import requests

# Test if the API returns audioUrl field

# Configuration
API_URL = "https://l3erksseb4.execute-api.us-east-1.amazonaws.com/prod/v1"
JOB_ID = "92fdd638-c687-4a78-9f4c-9c6c48d39b08"  # Job with audio

print("🎬 Testing Job API for audioUrl field")
print("=" * 50)

# Get auth token
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

# Test get single job
print(f"\n2️⃣ Testing GET /jobs/{JOB_ID}...")
headers = {
    "Authorization": f"Bearer {id_token}",
    "Accept": "application/json"
}

try:
    response = requests.get(f"{API_URL}/jobs/{JOB_ID}", headers=headers)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Job found")
        print(f"   Fields: {list(data.keys())}")
        print(f"   Has audioUrl: {'audioUrl' in data}")
        if 'audioUrl' in data:
            print(f"   AudioUrl: {data['audioUrl'][:50]}...")
    else:
        print(f"❌ Request failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test list jobs
print("\n3️⃣ Testing GET /jobs...")
try:
    response = requests.get(f"{API_URL}/jobs", headers=headers)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        jobs = data.get('jobs', [])
        print(f"✅ Got {len(jobs)} jobs")
        
        # Check for audio jobs
        audio_jobs = [j for j in jobs if 'audioUrl' in j]
        print(f"   Jobs with audioUrl: {len(audio_jobs)}")
        
        if audio_jobs:
            print(f"   Sample job with audio: {audio_jobs[0]['jobId']}")
            print(f"   AudioUrl: {audio_jobs[0]['audioUrl'][:50]}...")
        elif jobs:
            print(f"   Sample job fields: {list(jobs[0].keys())}")
    else:
        print(f"❌ Request failed: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

# Check DynamoDB directly for comparison
print("\n4️⃣ Checking DynamoDB directly...")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Jobs-prod')

try:
    db_response = table.get_item(Key={'jobId': JOB_ID})
    if 'Item' in db_response:
        job = db_response['Item']
        print(f"✅ Job in DynamoDB has audioUrl: {'audioUrl' in job}")
        if 'audioUrl' in job:
            print(f"   AudioUrl in DB: {job['audioUrl'][:50]}...")
except Exception as e:
    print(f"❌ DynamoDB error: {e}")

print("\n" + "=" * 50)