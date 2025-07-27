import json
import boto3
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')

# Configuration
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'Jobs-prod')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')

def lambda_handler(event, context):
    """Handle video.audio.ready events - mark job as complete with separate tracks"""
    logger.info(f"Video-Audio Combiner (Cloud) received event: {json.dumps(event)}")
    
    # Extract event details
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    video_url = detail.get('videoUrl')
    audio_url = detail.get('audioUrl')
    
    if not all([job_id, user_id, video_url, audio_url]):
        logger.error("Missing required fields")
        return {'statusCode': 400, 'body': 'Missing required fields'}
    
    logger.info(f"Processing video and audio for job {job_id}")
    
    try:
        # Update job status
        jobs_table = dynamodb.Table(JOBS_TABLE)
        
        # For now, we'll mark the job as complete with separate video and audio tracks
        # The frontend will handle playing them together
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, completedAt = :time, hasSeparateTracks = :separate',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'COMPLETED',
                ':time': datetime.utcnow().isoformat() + 'Z',
                ':separate': True
            }
        )
        
        # Emit completion event
        events_client.put_events(
            Entries=[{
                'Source': 'contentcraft.combiner',
                'DetailType': 'job.completed.with.audio',
                'Detail': json.dumps({
                    'jobId': job_id,
                    'userId': user_id,
                    'videoUrl': video_url,
                    'audioUrl': audio_url,
                    'separateTracks': True,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }),
                'EventBusName': EVENT_BUS_NAME
            }]
        )
        
        logger.info(f"Job {job_id} marked as complete with separate video and audio tracks")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job completed with separate video and audio tracks',
                'jobId': job_id,
                'videoUrl': video_url,
                'audioUrl': audio_url
            })
        }
            
    except Exception as e:
        logger.error(f"Failed to process job {job_id}: {str(e)}")
        
        # Update job with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, error = :error, failedAt = :time',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to process job',
                'jobId': job_id,
                'error': str(e)
            })
        }