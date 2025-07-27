import json
import time
import boto3
import requests
from datetime import datetime

# Configuration
API_URL = "https://l3erksseb4.execute-api.us-east-1.amazonaws.com/prod/v1/jobs"
JOBS_TABLE = "Jobs-prod"
REGION = "us-east-1"

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(JOBS_TABLE)

print("🎬 Testing Audio Job Submission")
print("=" * 50)

# Step 1: Get auth token
print("\n1️⃣ Getting authentication token...")
cognito = boto3.client('cognito-idp', region_name=REGION)

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
    "prompt": f"Test audio job {datetime.now().isoformat()} - ocean waves",
    "seconds": 5,
    "resolution": "720p",
    "tier": "fast",
    "feature": {
        "audio": True,
        "audioTier": "fast"
    }
}

print(f"Request body: {json.dumps(job_data, indent=2)}")

headers = {
    "Authorization": f"Bearer {id_token}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(API_URL, json=job_data, headers=headers)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        job_id = response.json().get('jobId')
        print(f"\n✅ Job submitted: {job_id}")
        
        # Step 3: Check DynamoDB after a short delay
        print("\n3️⃣ Checking DynamoDB for job details...")
        time.sleep(2)
        
        try:
            db_item = table.get_item(Key={'jobId': job_id})
            if 'Item' in db_item:
                job = db_item['Item']
                print(f"\nJob found in DynamoDB:")
                print(f"  - Status: {job.get('status')}")
                print(f"  - Feature field: {job.get('feature')}")
                print(f"  - Has audio feature: {job.get('feature', {}).get('audio', False)}")
                print(f"  - Audio tier: {job.get('feature', {}).get('audioTier', 'N/A')}")
                
                # Wait and check for audio processing
                print("\n4️⃣ Monitoring audio generation...")
                for i in range(6):
                    time.sleep(5)
                    db_item = table.get_item(Key={'jobId': job_id})
                    job = db_item['Item']
                    
                    print(f"\n[{i+1}/6] Status check:")
                    print(f"  - Job status: {job.get('status')}")
                    print(f"  - Audio status: {job.get('audioStatus', 'Not started')}")
                    print(f"  - Audio URL: {job.get('audioUrl', 'None yet')}")
                    
                    if job.get('audioUrl'):
                        print(f"\n✅ Audio generated successfully!")
                        break
                    elif job.get('audioStatus') == 'FAILED':
                        print(f"\n❌ Audio generation failed: {job.get('audioError')}")
                        break
                
            else:
                print("❌ Job not found in DynamoDB")
                
        except Exception as e:
            print(f"❌ DynamoDB error: {e}")
            
except Exception as e:
    print(f"❌ API request failed: {e}")

print("\n" + "=" * 50)
print("Test complete!")