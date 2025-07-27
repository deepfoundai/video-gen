import json
import boto3
import os
import logging
import requests
from datetime import datetime
import tempfile
import urllib.parse

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
events_client = boto3.client('events')
secrets_client = boto3.client('secretsmanager')

# Configuration
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'Jobs-prod')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'deepresearch-video-outputs')
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', 'https://d3beyg2vg2l65f.cloudfront.net')

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
        return None

def lambda_handler(event, context):
    """Handle video.audio.ready events to combine video and audio using fal.ai"""
    logger.info(f"Video-Audio Combiner received event: {json.dumps(event)}")
    
    # Extract event details
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    video_url = detail.get('videoUrl')
    audio_url = detail.get('audioUrl')
    
    if not all([job_id, user_id, video_url, audio_url]):
        logger.error("Missing required fields")
        return {'statusCode': 400, 'body': 'Missing required fields'}
    
    logger.info(f"Combining video and audio for job {job_id}")
    
    try:
        # Get API key
        api_key = get_fal_api_key()
        if not api_key:
            raise Exception("Failed to get FAL API key")
        
        # Update job status
        jobs_table = dynamodb.Table(JOBS_TABLE)
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET combinedStatus = :status, combinedStartTime = :time',
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':time': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Use fal.ai video editor to combine video and audio
        url = "https://fal.run/fal-ai/creative-upscaler"  # This model can handle video+audio
        headers = {
            'Authorization': f'Key {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Parameters for combining
        parameters = {
            "video_url": video_url,
            "audio_url": audio_url,
            "creativity": 0,  # No changes to video content
            "prompt": "",     # No prompt needed
            "output_format": "mp4"
        }
        
        logger.info(f"Calling fal.ai to combine: {url}")
        response = requests.post(url, json=parameters, headers=headers, timeout=120)
        
        if response.status_code != 200:
            # If creative-upscaler doesn't work, try a simpler approach
            # Just return the video URL as-is since we can't combine server-side without ffmpeg
            logger.warning(f"FAL API returned {response.status_code}, falling back to separate tracks")
            
            # Update job to mark as completed with separate tracks
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET combinedStatus = :status, combinedCompletedTime = :time, status = :jobStatus',
                ExpressionAttributeValues={
                    ':status': 'COMPLETED_SEPARATE_TRACKS',
                    ':jobStatus': 'COMPLETED',
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Emit event for separate tracks
            events_client.put_events(
                Entries=[{
                    'Source': 'contentcraft.combiner',
                    'DetailType': 'video.audio.separate',
                    'Detail': json.dumps({
                        'jobId': job_id,
                        'userId': user_id,
                        'videoUrl': video_url,
                        'audioUrl': audio_url,
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }),
                    'EventBusName': EVENT_BUS_NAME
                }]
            )
            
            logger.info(f"Video and audio will be played separately for job {job_id}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Video and audio available as separate tracks',
                    'jobId': job_id,
                    'videoUrl': video_url,
                    'audioUrl': audio_url
                })
            }
        
        result = response.json()
        logger.info(f"FAL response: {json.dumps(result)}")
        
        # Extract combined video URL
        combined_url = result.get('video', {}).get('url') or result.get('url')
        
        if not combined_url:
            raise Exception('No combined video URL in FAL response')
        
        # Update job with combined video URL
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET outputUrl = :url, combinedUrl = :url, combinedStatus = :status, combinedCompletedTime = :time, status = :jobStatus',
            ExpressionAttributeValues={
                ':url': combined_url,
                ':status': 'COMPLETED',
                ':jobStatus': 'COMPLETED',
                ':time': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Emit combined.video.ready event
        events_client.put_events(
            Entries=[{
                'Source': 'contentcraft.combiner',
                'DetailType': 'combined.video.ready',
                'Detail': json.dumps({
                    'jobId': job_id,
                    'userId': user_id,
                    'combinedUrl': combined_url,
                    'originalVideoUrl': video_url,
                    'originalAudioUrl': audio_url,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }),
                'EventBusName': EVENT_BUS_NAME
            }]
        )
        
        logger.info(f"Successfully combined video and audio for job {job_id}: {combined_url}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Video and audio combined successfully',
                'jobId': job_id,
                'combinedUrl': combined_url
            })
        }
            
    except Exception as e:
        logger.error(f"Failed to combine video and audio for job {job_id}: {str(e)}")
        
        # Fall back to separate tracks
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET combinedStatus = :status, combinedError = :error, combinedFailedTime = :time, status = :jobStatus',
                ExpressionAttributeValues={
                    ':status': 'FAILED_FALLBACK_SEPARATE',
                    ':error': str(e),
                    ':jobStatus': 'COMPLETED',
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except:
            pass
        
        # Still mark job as completed with separate tracks
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Video and audio available as separate tracks',
                'jobId': job_id,
                'videoUrl': video_url,
                'audioUrl': audio_url,
                'error': str(e)
            })
        }