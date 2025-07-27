import json
import boto3
import os
from datetime import datetime, timezone
from decimal import Decimal
import logging

# Import shared types and model mapping
import sys
sys.path.append('/opt/python')  # Lambda layer path
from shared_types import MODEL_TIER_TO_FAL_MODEL, LEGACY_TIER_MAPPING

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
events_client = boto3.client('events')

# Configuration
JOBS_TABLE_NAME = os.environ.get('JOBS_TABLE', 'Jobs-prod')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

def lambda_handler(event, context):
    """
    Job Processor Lambda - Orchestrates QUEUED jobs
    
    This function:
    1. Scans DynamoDB for jobs with status=QUEUED
    2. Updates their status to PROCESSING
    3. Emits video.job.submitted events to EventBridge
    4. Handles batch processing with limits
    """
    logger.info(f"Job Processor started - Event: {json.dumps(event)}")
    
    try:
        # Get QUEUED jobs from DynamoDB
        queued_jobs = get_queued_jobs()
        logger.info(f"Found {len(queued_jobs)} queued jobs")
        
        if not queued_jobs:
            logger.info("No queued jobs to process")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No queued jobs found', 'processed': 0})
            }
        
        processed_count = 0
        failed_count = 0
        
        # Process each queued job
        for job in queued_jobs:
            try:
                job_id = job['jobId']
                logger.info(f"Processing job: {job_id}")
                
                # Update job status to PROCESSING
                update_job_status(job_id, 'PROCESSING')
                
                # Emit video.job.submitted event
                emit_job_event(job)
                
                processed_count += 1
                logger.info(f"Successfully processed job: {job_id}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process job {job.get('jobId', 'unknown')}: {str(e)}")
                
                # Update job status to FAILED if we can't process it
                try:
                    update_job_status(job.get('jobId'), 'FAILED', str(e))
                except:
                    pass
        
        logger.info(f"Job processing complete - Processed: {processed_count}, Failed: {failed_count}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Job processing complete',
                'processed': processed_count,
                'failed': failed_count,
                'total_found': len(queued_jobs)
            })
        }
        
    except Exception as e:
        logger.error(f"Job processor error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_queued_jobs(limit=20):
    """Get jobs with status=QUEUED from DynamoDB"""
    try:
        # Remove Limit parameter as it's causing DynamoDB to miss records
        # Instead, scan all QUEUED jobs and limit in memory
        response = jobs_table.scan(
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'QUEUED'}
        )
        
        jobs = response.get('Items', [])
        logger.info(f"Retrieved {len(jobs)} queued jobs from DynamoDB")
        
        # Apply limit in memory to avoid DynamoDB scan issues
        if limit and len(jobs) > limit:
            jobs = jobs[:limit]
            logger.info(f"Limited to {limit} jobs for processing")
            
        return jobs
        
    except Exception as e:
        logger.error(f"Error retrieving queued jobs: {str(e)}")
        return []

def update_job_status(job_id, status, error_message=None):
    """Update job status in DynamoDB"""
    try:
        update_expression = 'SET #status = :status, updatedAt = :updated'
        expression_values = {
            ':status': status,
            ':updated': datetime.now(timezone.utc).isoformat()
        }
        expression_names = {'#status': 'status'}
        
        if error_message:
            update_expression += ', error_message = :error'
            expression_values[':error'] = error_message
        
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        
        logger.info(f"Updated job {job_id} status to {status}")
        
    except Exception as e:
        logger.error(f"Error updating job status for {job_id}: {str(e)}")
        raise

def emit_job_event(job):
    """Emit video.job.submitted event to EventBridge and audio event if requested"""
    try:
        job_id = job['jobId']
        
        # First, emit video generation event
        emit_video_event(job)
        
        # Check if audio generation is requested
        if job.get('feature', {}).get('audio'):
            logger.info(f"Audio feature detected for job {job_id}, emitting audio event")
            emit_audio_event(job)
        
    except Exception as e:
        logger.error(f"Error emitting events for job {job_id}: {str(e)}")
        raise

def emit_video_event(job):
    """Emit video.job.submitted event to EventBridge"""
    try:
        job_id = job['jobId']
        
        # Map job data to event format expected by FAL invoker
        event_detail = {
            "jobId": job_id,
            "userId": job.get('user_id', 'unknown'),
            "provider": "fal",  # Default to fal provider
            "model": determine_fal_model(job),
            "parameters": build_fal_parameters(job),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Emitting video event for job {job_id}: {json.dumps(event_detail)}")
        
        # Submit event to EventBridge
        response = events_client.put_events(
            Entries=[
                {
                    'Source': 'contentcraft.jobsubmitter',
                    'DetailType': 'video.job.submitted',
                    'Detail': json.dumps(event_detail, default=decimal_serializer),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        if response['FailedEntryCount'] > 0:
            failed_entry = response['Entries'][0]
            error_msg = failed_entry.get('ErrorMessage', 'Unknown error')
            logger.error(f"Failed to emit video event for job {job_id}: {error_msg}")
            raise Exception(f"EventBridge submission failed: {error_msg}")
        
        logger.info(f"Successfully emitted video event for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error emitting video event for job {job_id}: {str(e)}")
        raise

def emit_audio_event(job):
    """Emit audio.job.submitted event to EventBridge"""
    try:
        job_id = job['jobId']
        
        # Audio tier mapping
        AUDIO_TIER_TO_MODEL = {
            'fast': 'fal-ai/stable-audio',  # Working audio model
            'standard': 'fal-ai/stable-audio',  # Use same for now
            'pro': 'fal-ai/stable-audio'  # Use same for now
        }
        
        audio_tier = job.get('feature', {}).get('audioTier', 'fast')
        audio_model = AUDIO_TIER_TO_MODEL.get(audio_tier, AUDIO_TIER_TO_MODEL['fast'])
        
        # Build audio-specific event
        event_detail = {
            "jobId": job_id,
            "userId": job.get('user_id', 'unknown'),
            "provider": "fal",
            "model": audio_model,
            "parameters": build_audio_parameters(job),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Emitting audio event for job {job_id}: {json.dumps(event_detail)}")
        
        # Submit audio event to EventBridge
        response = events_client.put_events(
            Entries=[
                {
                    'Source': 'contentcraft.jobsubmitter',
                    'DetailType': 'audio.job.submitted',
                    'Detail': json.dumps(event_detail, default=decimal_serializer),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        if response['FailedEntryCount'] > 0:
            failed_entry = response['Entries'][0]
            error_msg = failed_entry.get('ErrorMessage', 'Unknown error')
            logger.error(f"Failed to emit audio event for job {job_id}: {error_msg}")
            raise Exception(f"EventBridge submission failed: {error_msg}")
        
        logger.info(f"Successfully emitted audio event for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error emitting audio event for job {job_id}: {str(e)}")
        raise

def determine_fal_model(job):
    """Determine which fal model to use based on job tier parameter"""
    # Use the imported model tier mapping from shared_types
    
    tier = job.get('tier', 'fast')
    
    # Handle legacy tier names
    if tier in LEGACY_TIER_MAPPING:
        tier = LEGACY_TIER_MAPPING[tier]
    
    # Get the corresponding model or default to fast tier
    model = MODEL_TIER_TO_FAL_MODEL.get(tier, MODEL_TIER_TO_FAL_MODEL['fast'])
    
    logger.info(f"Job tier: {tier}, selected model: {model}")
    return model

def build_fal_parameters(job):
    """Build fal.ai parameters from job data"""
    try:
        # For LTX video model, duration is in frames (24fps * seconds)
        duration_seconds = int(job.get('duration_seconds', job.get('seconds', 5)))
        
        parameters = {
            "prompt": job.get('prompt', ''),
            "num_frames": duration_seconds * 24,  # LTX uses frames, not seconds
        }
        
        # Add resolution if specified
        resolution = job.get('resolution', '720p')
        if resolution == '720p':
            parameters.update({"width": 768, "height": 512})  # LTX optimal resolution
        elif resolution == '1080p':
            parameters.update({"width": 1024, "height": 768})  # Scaled for LTX
        elif resolution == '4k':
            parameters.update({"width": 1280, "height": 768})  # Max for LTX
        
        # Add other parameters specific to LTX model
        parameters.update({
            "num_inference_steps": 25,  # Reduced for faster generation
            "guidance_scale": 7.5,      # Default guidance scale
            "seed": 42  # For reproducibility
        })
        
        logger.info(f"Built fal parameters: {json.dumps(parameters)}")
        return parameters
        
    except Exception as e:
        logger.error(f"Error building fal parameters: {str(e)}")
        # Return minimal parameters if building fails (LTX format)
        return {
            "prompt": job.get('prompt', 'A beautiful landscape'),
            "num_frames": 120,  # 5 seconds * 24fps
            "width": 768,
            "height": 512,
            "num_inference_steps": 25,
            "guidance_scale": 7.5
        }

def build_audio_parameters(job):
    """Build audio generation parameters from job data"""
    try:
        duration_seconds = int(job.get('duration_seconds', job.get('seconds', 5)))
        
        # Enhance prompt for audio generation
        original_prompt = job.get('prompt', '')
        audio_prompt = f"{original_prompt}, ambient sounds and sound effects"
        
        # stable-audio expects 'seconds' not 'duration'
        parameters = {
            "prompt": audio_prompt,
            "seconds": duration_seconds
        }
        
        logger.info(f"Built audio parameters: {json.dumps(parameters)}")
        return parameters
        
    except Exception as e:
        logger.error(f"Error building audio parameters: {str(e)}")
        # Return minimal parameters if building fails
        return {
            "prompt": "ambient nature sounds",
            "duration": 5,
            "format": "mp3",
            "sample_rate": 44100
        }

def decimal_serializer(obj):
    """JSON serializer for DynamoDB Decimal types"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")