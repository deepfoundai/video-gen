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
    """Orchestrate job completion - wait for both video and audio before combining"""
    logger.info(f"Job Orchestrator received event: {json.dumps(event)}")
    
    # Get event type
    detail_type = event.get('detail-type', '')
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    
    if not job_id:
        logger.error("No jobId in event")
        return {'statusCode': 400, 'body': 'Missing jobId'}
    
    try:
        # Get current job status
        jobs_table = dynamodb.Table(JOBS_TABLE)
        response = jobs_table.get_item(Key={'jobId': job_id})
        job = response.get('Item')
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return {'statusCode': 404, 'body': 'Job not found'}
        
        # Check if job has audio feature enabled
        has_audio = job.get('feature', {}).get('audio', False)
        video_url = job.get('outputUrl')
        audio_url = job.get('audioUrl')
        video_status = job.get('status', 'PENDING')
        audio_status = job.get('audioStatus', 'PENDING')
        
        logger.info(f"Job {job_id} - Video: {video_status}, Audio: {audio_status}, Has Audio: {has_audio}")
        
        # Handle video.rendered event
        if detail_type == 'video.rendered':
            video_url = detail.get('videoUrl')
            if not has_audio:
                # No audio needed, job is complete
                logger.info(f"Job {job_id} complete (video only)")
                jobs_table.update_item(
                    Key={'jobId': job_id},
                    UpdateExpression='SET #status = :status, completedAt = :time',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'COMPLETED',
                        ':time': datetime.utcnow().isoformat() + 'Z'
                    }
                )
            else:
                # Check if audio is also done
                if audio_status == 'COMPLETED' and audio_url:
                    logger.info(f"Both video and audio ready for job {job_id}, triggering combination")
                    emit_video_audio_ready(job_id, user_id, video_url, audio_url)
                else:
                    logger.info(f"Waiting for audio to complete for job {job_id}")
        
        # Handle audio.rendered event
        elif detail_type == 'audio.rendered':
            audio_url = detail.get('audioUrl')
            # Check if video is also done
            if video_status == 'COMPLETED' and video_url:
                logger.info(f"Both video and audio ready for job {job_id}, triggering combination")
                emit_video_audio_ready(job_id, user_id, video_url, audio_url)
            else:
                logger.info(f"Waiting for video to complete for job {job_id}")
        
        # Handle combined.video.ready event
        elif detail_type == 'combined.video.ready':
            logger.info(f"Job {job_id} fully complete with combined video/audio")
            # Job status already updated by combiner
        
        # Handle video.audio.separate event (fallback)
        elif detail_type == 'video.audio.separate':
            logger.info(f"Job {job_id} complete with separate video/audio tracks")
            # Job status already updated by combiner
        
        return {'statusCode': 200, 'body': json.dumps({'message': 'Event processed'})}
        
    except Exception as e:
        logger.error(f"Error processing event for job {job_id}: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def emit_video_audio_ready(job_id, user_id, video_url, audio_url):
    """Emit event when both video and audio are ready"""
    events_client.put_events(
        Entries=[{
            'Source': 'contentcraft.orchestrator',
            'DetailType': 'video.audio.ready',
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
    logger.info(f"Emitted video.audio.ready event for job {job_id}")