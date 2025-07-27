#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

# Test Lambda functions directly to see if they return audioUrl

lambda_client = boto3.client('lambda', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Jobs-prod')

print("🔍 Testing Lambda Functions for audioUrl field")
print("=" * 50)

# First, find a job with audio in DynamoDB
print("\n1️⃣ Finding a job with audio in DynamoDB...")
response = table.scan(
    FilterExpression='attribute_exists(audioUrl)',
    Limit=5
)

if not response['Items']:
    print("❌ No jobs with audio found in DynamoDB")
    exit(1)

test_job = response['Items'][0]
job_id = test_job['jobId']
print(f"✅ Found job with audio: {job_id}")
print(f"   - Prompt: {test_job.get('prompt', 'N/A')}")
print(f"   - AudioUrl: {test_job.get('audioUrl', 'N/A')[:50]}...")

# Test GetJobFn-prod
print("\n2️⃣ Testing GetJobFn-prod Lambda...")
try:
    # Create the event that API Gateway would send
    event = {
        "pathParameters": {
            "jobId": job_id
        },
        "headers": {
            "Authorization": "Bearer dummy-token"  # We'll test without auth
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": "test-user"
                }
            }
        }
    }
    
    response = lambda_client.invoke(
        FunctionName='GetJobFn-prod',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"Lambda response status: {result.get('statusCode', 'N/A')}")
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        has_audio = 'audioUrl' in body
        print(f"✅ Response includes audioUrl: {has_audio}")
        if has_audio:
            print(f"   AudioUrl value: {body['audioUrl'][:50]}...")
        else:
            print("❌ audioUrl field is missing from response!")
            print(f"   Fields returned: {list(body.keys())}")
    else:
        print(f"❌ Lambda returned error: {result}")
        
except Exception as e:
    print(f"❌ Error invoking GetJobFn-prod: {e}")

# Test list-jobs-api-prod
print("\n3️⃣ Testing list-jobs-api-prod Lambda...")
try:
    event = {
        "headers": {
            "Authorization": "Bearer dummy-token"
        },
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": test_job.get('user_id', 'test-user')
                }
            }
        }
    }
    
    response = lambda_client.invoke(
        FunctionName='list-jobs-api-prod',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"Lambda response status: {result.get('statusCode', 'N/A')}")
    
    if result.get('statusCode') == 200:
        body = json.loads(result.get('body', '{}'))
        jobs = body.get('jobs', [])
        
        # Find a job with audio
        audio_job = next((j for j in jobs if j.get('audioUrl')), None)
        
        if audio_job:
            print(f"✅ Found job with audioUrl in list response")
            print(f"   Job ID: {audio_job['jobId']}")
            print(f"   AudioUrl: {audio_job['audioUrl'][:50]}...")
        else:
            print(f"❌ No jobs with audioUrl found in list of {len(jobs)} jobs")
            if jobs:
                print(f"   Sample job fields: {list(jobs[0].keys())}")
    else:
        print(f"❌ Lambda returned error: {result}")
        
except Exception as e:
    print(f"❌ Error invoking list-jobs-api-prod: {e}")

print("\n" + "=" * 50)
print("Test complete!")