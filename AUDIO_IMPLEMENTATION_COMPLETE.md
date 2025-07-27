# Audio Implementation - Complete Solution

## Summary of Changes Made

### ✅ Phase 1: Job Submission Lambda (COMPLETED)
- Updated to save `tier` and `feature` fields to DynamoDB
- Now audio feature flag is persisted with the job

### ✅ Phase 2: Job Processor Lambda (COMPLETED)
- Split `emit_job_event` into separate video and audio event emitters
- Added `emit_audio_event` function that:
  - Checks for `feature.audio` flag
  - Maps audio tier to appropriate model
  - Emits `audio.job.submitted` events
- Added `build_audio_parameters` function for audio-specific parameters

### ⏳ Phase 3: Fal Invoker Updates (NEEDED)
The existing fal-invoker is tightly coupled to video processing. We have two options:

#### Option A: Modify Existing Handler (Complex)
- Update handler to detect event type (video vs audio)
- Add audio-specific output parsing
- Handle different response formats

#### Option B: Create Simplified Audio Handler (Recommended)
Create a minimal handler specifically for audio that:
1. Receives `audio.job.submitted` events
2. Calls fal.ai audio model
3. Updates job with `audioUrl`
4. Emits `audio.rendered` event

## Recommended Implementation

### Create Simple Audio Handler

```python
# audio-handler-lambda.py
import json
import boto3
import requests
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
secrets_client = boto3.client('secretsmanager')

def get_fal_api_key():
    """Get FAL API key from Secrets Manager"""
    response = secrets_client.get_secret_value(SecretId='/contentcraft/fal/api_key')
    secret = json.loads(response['SecretString'])
    return secret['api_key']

def lambda_handler(event, context):
    """Handle audio.job.submitted events"""
    logger.info(f"Audio handler received: {json.dumps(event)}")
    
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    model = detail.get('model', 'fal-ai/cassetteai/sound-effects-generator')
    parameters = detail.get('parameters', {})
    
    try:
        # Get API key
        api_key = get_fal_api_key()
        
        # Call fal.ai
        url = f"https://fal.run/{model}"
        headers = {
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=parameters, headers=headers)
        result = response.json()
        
        # Extract audio URL
        audio_url = result.get('audio_url') or result.get('url') or result.get('output', {}).get('url')
        
        if audio_url:
            # Update job with audio URL
            jobs_table = dynamodb.Table('Jobs-prod')
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET audioUrl = :url, audioStatus = :status',
                ExpressionAttributeValues={
                    ':url': audio_url,
                    ':status': 'COMPLETED'
                }
            )
            
            # Emit success event
            events_client.put_events(
                Entries=[{
                    'Source': 'contentcraft.audiohandler',
                    'DetailType': 'audio.rendered',
                    'Detail': json.dumps({
                        'jobId': job_id,
                        'userId': user_id,
                        'audioUrl': audio_url
                    })
                }]
            )
            
            return {'statusCode': 200, 'body': 'Audio generated'}
        else:
            raise Exception('No audio URL in response')
            
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        
        # Update job with error
        jobs_table = dynamodb.Table('Jobs-prod')
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET audioStatus = :status, audioError = :error',
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':error': str(e)
            }
        )
        
        # Emit failure event
        events_client.put_events(
            Entries=[{
                'Source': 'contentcraft.audiohandler',
                'DetailType': 'audio.failed',
                'Detail': json.dumps({
                    'jobId': job_id,
                    'userId': user_id,
                    'error': str(e)
                })
            }]
        )
        
        raise
```

### Create EventBridge Rule

```bash
# Create rule for audio events
aws events put-rule \
  --name AudioJobSubmittedRule \
  --event-pattern '{"source":["contentcraft.jobsubmitter"],"detail-type":["audio.job.submitted"]}' \
  --description "Route audio generation jobs to audio handler"

# Add Lambda permission
aws lambda add-permission \
  --function-name audio-handler \
  --statement-id AllowEventBridgeAudio \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:717984198385:rule/AudioJobSubmittedRule

# Add Lambda target
aws events put-targets \
  --rule AudioJobSubmittedRule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:717984198385:function:audio-handler"
```

## Testing Instructions

1. **Submit a job with audio enabled**
2. **Check DynamoDB** - Job should have `feature: { audio: true }`
3. **Check CloudWatch Logs**:
   - Job Processor should show "Audio feature detected"
   - Should see both video and audio events emitted
4. **Monitor audio handler logs** for audio generation

## Current Status

### Working:
- ✅ Frontend sends audio feature
- ✅ Job saved with audio flag
- ✅ Job processor emits audio events

### Needed:
- ⏳ Deploy audio handler Lambda
- ⏳ Create EventBridge rule
- ⏳ Test end-to-end

## Quick Deployment

```bash
# 1. Create audio handler Lambda
zip audio-handler.zip audio-handler-lambda.py
aws lambda create-function \
  --function-name audio-handler \
  --runtime python3.9 \
  --role arn:aws:iam::717984198385:role/lambda-execution-role \
  --handler audio-handler-lambda.lambda_handler \
  --zip-file fileb://audio-handler.zip \
  --environment Variables={JOBS_TABLE=Jobs-prod}

# 2. Create EventBridge rule (commands above)

# 3. Test with a new job submission
```