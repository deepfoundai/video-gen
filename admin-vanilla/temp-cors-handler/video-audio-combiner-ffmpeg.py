import json
import boto3
import os
import logging
import urllib.request
import subprocess
from datetime import datetime
import tempfile
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
events_client = boto3.client('events')

# Configuration
JOBS_TABLE = os.environ.get('JOBS_TABLE', 'Jobs-prod')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'contentcraft-videos')

def lambda_handler(event, context):
    """Handle video.audio.ready events - combine video and audio with ffmpeg"""
    logger.info(f"Video-Audio Combiner received event: {json.dumps(event)}")
    
    # Extract event details
    detail = event.get('detail', {})
    job_id = detail.get('jobId')
    user_id = detail.get('userId')
    video_url = detail.get('videoUrl')
    audio_url = detail.get('audioUrl')
    
    if not all([job_id, user_id, audio_url]):
        logger.error("Missing required fields")
        return {'statusCode': 400, 'body': 'Missing required fields'}
    
    # If video URL is missing, fetch from DynamoDB
    if not video_url:
        logger.info(f"Video URL missing in event, fetching from database for job {job_id}")
        jobs_table = dynamodb.Table(JOBS_TABLE)
        job_response = jobs_table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in job_response:
            logger.error(f"Job {job_id} not found")
            return {'statusCode': 404, 'body': 'Job not found'}
        
        job = job_response['Item']
        video_url = job.get('outputUrl')
        
        if not video_url:
            logger.error(f"Video URL not found in database for job {job_id}")
            return {'statusCode': 400, 'body': 'Video URL not found'}
    
    logger.info(f"Processing video and audio combination for job {job_id}")
    logger.info(f"Video URL: {video_url}")
    logger.info(f"Audio URL: {audio_url}")
    
    try:
        # Update job status to indicate combination in progress
        jobs_table = dynamodb.Table(JOBS_TABLE)
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET combinationStatus = :status',
            ExpressionAttributeValues={
                ':status': 'COMBINING'
            }
        )
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video and audio files
            video_path = os.path.join(temp_dir, 'video.mp4')
            audio_path = os.path.join(temp_dir, 'audio.wav')
            output_path = os.path.join(temp_dir, 'combined.mp4')
            
            logger.info("Downloading video file...")
            urllib.request.urlretrieve(video_url, video_path)
            
            logger.info("Downloading audio file...")
            urllib.request.urlretrieve(audio_url, audio_path)
            
            # Combine video and audio using ffmpeg
            logger.info("Combining video and audio with ffmpeg...")
            
            # FFmpeg command to combine video and audio
            # -i video.mp4 -i audio.wav: Input files
            # -c:v copy: Copy video codec (no re-encoding)
            # -c:a aac: Convert audio to AAC
            # -map 0:v:0 -map 1:a:0: Map video from first input, audio from second
            # -shortest: Cut to shortest stream length
            cmd = [
                '/opt/bin/ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',  # Overwrite output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            logger.info("Video and audio combined successfully")
            
            # Upload combined video to S3
            output_key = f"videos/{job_id}/combined.mp4"
            logger.info(f"Uploading combined video to s3://{OUTPUT_BUCKET}/{output_key}")
            
            with open(output_path, 'rb') as f:
                s3.put_object(
                    Bucket=OUTPUT_BUCKET,
                    Key=output_key,
                    Body=f,
                    ContentType='video/mp4',
                    CacheControl='max-age=86400'
                )
            
            # Generate CloudFront URL (assuming standard pattern)
            combined_url = f"https://d3beyg2vg2l65f.cloudfront.net/{output_key}"
            
            # Update job with combined video URL
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, combinedUrl = :url, combinationStatus = :cstatus, completedAt = :time',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':url': combined_url,
                    ':cstatus': 'COMPLETED',
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            # Emit completion event
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
            
            logger.info(f"Job {job_id} completed with combined video/audio at {combined_url}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Video and audio combined successfully',
                    'jobId': job_id,
                    'combinedUrl': combined_url
                })
            }
            
    except Exception as e:
        logger.error(f"Failed to combine video/audio for job {job_id}: {str(e)}")
        
        # Update job with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET combinationStatus = :status, combinationError = :error',
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e)
                }
            )
        except:
            pass
        
        # Still mark job as completed but with separate tracks
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET #status = :status, hasSeparateTracks = :separate, completedAt = :time',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'COMPLETED',
                    ':separate': True,
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
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    }),
                    'EventBusName': EVENT_BUS_NAME
                }]
            )
        except:
            pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to combine video/audio, job completed with separate tracks',
                'jobId': job_id,
                'error': str(e)
            })
        }