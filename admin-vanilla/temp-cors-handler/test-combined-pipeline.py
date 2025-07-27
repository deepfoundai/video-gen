#!/usr/bin/env python3
"""
Test the complete video + audio combination pipeline
"""
import requests
import boto3
import json
import time
from datetime import datetime

# Configuration
API_URL = "https://l3erksseb4.execute-api.us-east-1.amazonaws.com/prod/v1"

print("🎬 Testing Complete Video + Audio Combination Pipeline")
print("=" * 60)

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

# Step 2: Submit job with audio
print("\n2️⃣ Submitting job with audio feature...")

job_data = {
    "prompt": f"Waves crashing on beach at sunset - test {datetime.now().strftime('%H:%M:%S')}",
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
    
    if response.status_code in [200, 201]:
        job_id = response.json().get('jobId')
        print(f"✅ Job submitted: {job_id}")
        
        # Step 3: Monitor job progress
        print("\n3️⃣ Monitoring job progress...")
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('Jobs-prod')
        
        max_wait = 120  # 2 minutes
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            # Check job in database
            db_response = table.get_item(Key={'jobId': job_id})
            if 'Item' in db_response:
                job = db_response['Item']
                status = job.get('status', 'UNKNOWN')
                
                # Print status changes
                if status != last_status:
                    print(f"\n[{int(time.time() - start_time)}s] Status: {status}")
                    last_status = status
                
                # Check detailed progress
                video_url = job.get('outputUrl', '')
                audio_url = job.get('audioUrl', '')
                combined_url = job.get('combinedUrl', '')
                
                print(f"  - Video: {video_url[:50] + '...' if video_url else 'Not ready'}")
                print(f"  - Audio: {job.get('audioStatus', 'Not started')} | {audio_url[:50] + '...' if audio_url else 'Not ready'}")
                print(f"  - Combined: {job.get('combinationStatus', 'Not started')} | {combined_url[:50] + '...' if combined_url else 'Not ready'}")
                
                # Check if we have combined video
                if job.get('combinedUrl'):
                    print(f"\n✅ Video and audio successfully combined!")
                    print(f"🎥 Combined video URL: {job['combinedUrl']}")
                    print(f"\n🎉 Success! The video has synchronized audio track embedded.")
                    break
                
                # Check if job completed with separate tracks
                if status == 'COMPLETED' and job.get('audioUrl') and not job.get('combinedUrl'):
                    print(f"\n⚠️ Job completed with separate video and audio tracks")
                    print(f"Video: {job.get('outputUrl', 'N/A')}")
                    print(f"Audio: {job.get('audioUrl', 'N/A')}")
                    
                    if job.get('combinationError'):
                        print(f"Combination error: {job['combinationError']}")
                    break
                
                # Check for failures
                if status == 'FAILED':
                    print(f"\n❌ Job failed: {job.get('error_message', 'Unknown error')}")
                    break
            
            time.sleep(5)
        
        if time.time() - start_time >= max_wait:
            print(f"\n⏱️ Timeout waiting for job completion")
            
    else:
        print(f"❌ Job submission failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Test complete!")