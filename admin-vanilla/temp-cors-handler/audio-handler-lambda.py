import json
import boto3
import requests
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')
secrets_client = boto3.client('secretsmanager')

# Configuration
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'Jobs-prod')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')

def get_fal_api_key():
    """Get FAL API key from environment or Secrets Manager"""
    # First try environment variable
    api_key = os.environ.get('FAL_API_KEY')
    if api_key:
        return api_key
    
    # Fallback to Secrets Manager
    try:
        response = secrets_client.get_secret_value(SecretId='/contentcraft/fal/api_key')
        secret = json.loads(response['SecretString'])
        return secret['api_key']
    except Exception as e:
        logger.error(f"Failed to get API key: {str(e)}")
        # For testing, use a placeholder
        return "fal-api-key-placeholder"

def lambda_handler(event, context):
    """Handle audio.job.submitted events"""
    logger.info(f"Audio handler received event: {json.dumps(event)}")
    
    # Extract event details
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    model = detail.get('model', 'fal-ai/cassetteai/sound-effects-generator')
    parameters = detail.get('parameters', {})
    
    if not job_id or not user_id:
        logger.error("Missing required fields: jobId or userId")
        return {'statusCode': 400, 'body': 'Missing required fields'}
    
    logger.info(f"Processing audio for job {job_id}, model: {model}")
    
    try:
        # Get API key
        api_key = get_fal_api_key()
        
        # Update job status to processing
        jobs_table = dynamodb.Table(JOBS_TABLE)
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET audioStatus = :status, audioStartTime = :time',
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':time': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Call fal.ai audio model
        # Handle models with or without fal-ai/ prefix
        if model.startswith('fal-ai/'):
            url = f"https://fal.run/{model}"
        else:
            url = f"https://fal.run/fal-ai/{model}"
        headers = {
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Calling fal.ai: {url} with params: {json.dumps(parameters)}")
        response = requests.post(url, json=parameters, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"FAL API error: {response.status_code} - {response.text}")
        
        result = response.json()
        logger.info(f"FAL response: {json.dumps(result)}")
        
        # Extract audio URL from various possible response formats
        audio_url = None
        if 'audio_url' in result:
            audio_url = result['audio_url']
        elif 'url' in result:
            audio_url = result['url']
        elif 'output' in result and isinstance(result['output'], dict):
            audio_url = result['output'].get('url') or result['output'].get('audio_url')
        elif 'audio' in result and isinstance(result['audio'], dict):
            audio_url = result['audio'].get('url')
        elif 'audio_file' in result and isinstance(result['audio_file'], dict):
            audio_url = result['audio_file'].get('url')
        
        if not audio_url:
            # Log the full response to debug
            logger.error(f"No audio URL found in response: {json.dumps(result)}")
            raise Exception('No audio URL in FAL response')
        
        # Update job with audio URL
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET audioUrl = :url, audioStatus = :status, audioCompletedTime = :time',
            ExpressionAttributeValues={
                ':url': audio_url,
                ':status': 'COMPLETED',
                ':time': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Emit audio.rendered event
        events_client.put_events(
            Entries=[{
                'Source': 'contentcraft.audiohandler',
                'DetailType': 'audio.rendered',
                'Detail': json.dumps({
                    'jobId': job_id,
                    'userId': user_id,
                    'audioUrl': audio_url,
                    'model': model,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }),
                'EventBusName': EVENT_BUS_NAME
            }]
        )
        
        logger.info(f"Audio generation successful for job {job_id}: {audio_url}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Audio generated successfully',
                'jobId': job_id,
                'audioUrl': audio_url
            })
        }
        
    except Exception as e:
        logger.error(f"Audio generation failed for job {job_id}: {str(e)}")
        
        # Update job with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET audioStatus = :status, audioError = :error, audioFailedTime = :time',
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except:
            pass  # Don't fail if we can't update the job
        
        # Emit audio.failed event
        try:
            events_client.put_events(
                Entries=[{
                    'Source': 'contentcraft.audiohandler',
                    'DetailType': 'audio.failed',
                    'Detail': json.dumps({
                        'jobId': job_id,
                        'userId': user_id,
                        'error': str(e),
                        'model': model,
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }),
                    'EventBusName': EVENT_BUS_NAME
                }]
            )
        except:
            pass  # Don't fail if we can't emit event
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Audio generation failed',
                'jobId': job_id,
                'error': str(e)
            })
        }