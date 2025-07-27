import json
import boto3
import os
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Configuration
JOBS_TABLE_NAME = os.environ.get('JOBS_TABLE', 'Jobs-prod')
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

def lambda_handler(event, context):
    """
    Job Status Update Lambda - Handles job completion events
    
    This function listens for EventBridge events:
    - video.rendered: Updates job status to COMPLETED with video URL
    - video.failed: Updates job status to FAILED with error message
    """
    logger.info(f"Job Status Update started - Event: {json.dumps(event)}")
    
    try:
        # Handle different event sources
        if 'Records' in event:
            # EventBridge events come as Records
            for record in event['Records']:
                process_eventbridge_record(record)
        elif 'detail-type' in event:
            # Direct EventBridge event
            process_eventbridge_event(event)
        else:
            # Unknown event format
            logger.warning(f"Unknown event format: {json.dumps(event)}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Unknown event format'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Event processed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Job status update error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_eventbridge_record(record):
    """Process an EventBridge record from SQS or direct invocation"""
    try:
        # Extract EventBridge event from record
        if 'eventbridge' in record:
            event_data = record['eventbridge']
        elif 'body' in record:
            # SQS record with EventBridge event in body
            event_data = json.loads(record['body'])
        else:
            event_data = record
        
        process_eventbridge_event(event_data)
        
    except Exception as e:
        logger.error(f"Error processing EventBridge record: {str(e)}")
        raise

def process_eventbridge_event(event):
    """Process a single EventBridge event"""
    try:
        detail_type = event.get('detail-type', '')
        source = event.get('source', '')
        detail = event.get('detail', {})
        
        logger.info(f"Processing event - Source: {source}, DetailType: {detail_type}")
        
        # Handle video completion events
        if detail_type == 'video.rendered':
            handle_video_rendered(detail)
        elif detail_type == 'video.failed':
            handle_video_failed(detail)
        else:
            logger.info(f"Ignoring event type: {detail_type}")
        
    except Exception as e:
        logger.error(f"Error processing EventBridge event: {str(e)}")
        raise

def handle_video_rendered(detail):
    """Handle successful video generation completion"""
    try:
        job_id = detail.get('jobId')
        video_url = detail.get('videoUrl') or detail.get('outputUrl')
        
        if not job_id:
            logger.error("Missing jobId in video.rendered event")
            return
        
        logger.info(f"Handling video rendered for job: {job_id}")
        
        # Update job status to COMPLETED
        update_expression = 'SET #status = :status, updatedAt = :updated'
        expression_values = {
            ':status': 'COMPLETED',
            ':updated': datetime.now(timezone.utc).isoformat()
        }
        expression_names = {'#status': 'status'}
        
        if video_url:
            update_expression += ', outputUrl = :url'
            expression_values[':url'] = video_url
        
        # Add any additional metadata from the event
        if 'duration' in detail:
            update_expression += ', actual_duration = :duration'
            expression_values[':duration'] = detail['duration']
        
        if 'fileSize' in detail:
            update_expression += ', file_size = :size'
            expression_values[':size'] = detail['fileSize']
        
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names
        )
        
        logger.info(f"Successfully updated job {job_id} to COMPLETED")
        
        # Log completion metrics
        logger.info(f"VIDEO_COMPLETION_SUCCESS jobId={job_id} videoUrl={video_url}")
        
    except Exception as e:
        logger.error(f"Error handling video rendered event: {str(e)}")
        raise

def handle_video_failed(detail):
    """Handle failed video generation"""
    try:
        job_id = detail.get('jobId')
        error_message = detail.get('error', detail.get('errorMessage', 'Video generation failed'))
        
        if not job_id:
            logger.error("Missing jobId in video.failed event")
            return
        
        logger.info(f"Handling video failed for job: {job_id}")
        
        # Update job status to FAILED
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, updatedAt = :updated, error_message = :error',
            ExpressionAttributeValues={
                ':status': 'FAILED',
                ':updated': datetime.now(timezone.utc).isoformat(),
                ':error': error_message
            },
            ExpressionAttributeNames={'#status': 'status'}
        )
        
        logger.info(f"Successfully updated job {job_id} to FAILED")
        
        # Log failure metrics
        logger.error(f"VIDEO_COMPLETION_FAILURE jobId={job_id} error={error_message}")
        
    except Exception as e:
        logger.error(f"Error handling video failed event: {str(e)}")
        raise

def get_job_details(job_id):
    """Retrieve job details from DynamoDB"""
    try:
        response = jobs_table.get_item(Key={'jobId': job_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        return None