import json
import boto3
import os
import logging
import requests
from datetime import datetime
import tempfile
import subprocess
import shutil

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
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'deepresearch-video-outputs')
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', 'https://d3beyg2vg2l65f.cloudfront.net')

def lambda_handler(event, context):
    """Handle video.audio.ready events to combine video and audio"""
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
        
        # Download video and audio files to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'video.mp4')
            audio_path = os.path.join(temp_dir, 'audio.wav')
            output_path = os.path.join(temp_dir, 'combined.mp4')
            
            # Download video
            logger.info(f"Downloading video from {video_url}")
            video_response = requests.get(video_url, timeout=60)
            with open(video_path, 'wb') as f:
                f.write(video_response.content)
            
            # Download audio
            logger.info(f"Downloading audio from {audio_url}")
            audio_response = requests.get(audio_url, timeout=60)
            with open(audio_path, 'wb') as f:
                f.write(audio_response.content)
            
            # Combine using ffmpeg (from Lambda layer at /opt/bin/ffmpeg)
            ffmpeg_path = '/opt/bin/ffmpeg'
            if not os.path.exists(ffmpeg_path):
                # Fallback to system ffmpeg
                ffmpeg_path = 'ffmpeg'
            
            logger.info(f"Combining video and audio with ffmpeg at {ffmpeg_path}")
            cmd = [
                ffmpeg_path,
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copy video codec
                '-c:a', 'aac',   # Convert audio to AAC
                '-map', '0:v:0', # Map video from first input
                '-map', '1:a:0', # Map audio from second input
                '-shortest',     # Match shortest duration
                '-y',            # Overwrite output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            # Upload combined video to S3
            s3_key = f"videos/{job_id}-combined.mp4"
            logger.info(f"Uploading combined video to s3://{OUTPUT_BUCKET}/{s3_key}")
            
            with open(output_path, 'rb') as f:
                s3.upload_fileobj(
                    f,
                    OUTPUT_BUCKET,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'video/mp4',
                        'CacheControl': 'public, max-age=31536000'
                    }
                )
            
            # Generate CloudFront URL
            combined_url = f"{CLOUDFRONT_DOMAIN}/{s3_key}"
            
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
        
        # Update job with error
        try:
            jobs_table.update_item(
                Key={'jobId': job_id},
                UpdateExpression='SET combinedStatus = :status, combinedError = :error, combinedFailedTime = :time',
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e),
                    ':time': datetime.utcnow().isoformat() + 'Z'
                }
            )
        except:
            pass
        
        # Emit combined.video.failed event
        try:
            events_client.put_events(
                Entries=[{
                    'Source': 'contentcraft.combiner',
                    'DetailType': 'combined.video.failed',
                    'Detail': json.dumps({
                        'jobId': job_id,
                        'userId': user_id,
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
                'message': 'Failed to combine video and audio',
                'jobId': job_id,
                'error': str(e)
            })
        }