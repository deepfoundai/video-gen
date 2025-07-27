# Audio Implementation Design Document

## Overview
This document outlines the design and implementation plan for adding audio generation to the video pipeline.

## Current Architecture
```
User → Frontend → Jobs API → DynamoDB → Job Processor → EventBridge → Fal Invoker → fal.ai
```

## Proposed Architecture for Audio

### Option 1: Sequential Generation (Recommended for POC)
```
1. Video Generation:
   Job Processor → EventBridge (video.job.submitted) → Fal Invoker → fal.ai (video)
   
2. Audio Generation (if feature.audio = true):
   Job Processor → EventBridge (audio.job.submitted) → Fal Invoker → fal.ai (audio)
```

### Option 2: Parallel Generation
```
Job Processor → EventBridge → {
   video.job.submitted → Fal Invoker → fal.ai (video)
   audio.job.submitted → Fal Invoker → fal.ai (audio)
}
```

## Implementation Plan

### Phase 1: Job Processor Updates

#### 1.1 Modify emit_job_event() to handle audio
```python
def emit_job_event(job):
    # Existing video event
    emit_video_event(job)
    
    # New: Check for audio feature
    if job.get('feature', {}).get('audio'):
        emit_audio_event(job)
```

#### 1.2 Add emit_audio_event() function
```python
def emit_audio_event(job):
    audio_tier = job.get('feature', {}).get('audioTier', 'fast')
    
    event_detail = {
        "jobId": job['jobId'],
        "userId": job.get('user_id'),
        "provider": "fal",
        "model": AUDIO_TIER_TO_MODEL[audio_tier],
        "parameters": build_audio_parameters(job),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Emit audio.job.submitted event
```

### Phase 2: Fal Invoker Updates

#### 2.1 Handle Different Event Types
- Detect event type (video.job.submitted vs audio.job.submitted)
- Route to appropriate handler

#### 2.2 Audio Generation Handler
```python
def handle_audio_generation(event):
    # Extract audio-specific parameters
    # Call fal.ai audio model
    # Update job with audioUrl
```

### Phase 3: Database Schema Updates

#### 3.1 Add audio fields to Jobs table
- `audioUrl`: S3 URL of generated audio
- `audioStatus`: Status of audio generation
- `audioError`: Error message if audio fails

### Phase 4: Frontend Updates
- Display audio player when audioUrl is available
- Show audio generation status

## Audio Model Parameters

### For cassetteai/sound-effects-generator:
```python
{
    "prompt": job['prompt'] + " ambient sounds",  # Enhance prompt for audio
    "duration": job['duration_seconds'],
    "format": "mp3",
    "sample_rate": 44100
}
```

## Event Schemas

### video.job.submitted (existing)
```json
{
    "jobId": "uuid",
    "userId": "user-id",
    "provider": "fal",
    "model": "fal-ai/ltx-video-13b-distilled",
    "parameters": { ... }
}
```

### audio.job.submitted (new)
```json
{
    "jobId": "uuid",
    "userId": "user-id", 
    "provider": "fal",
    "model": "fal-ai/cassetteai/sound-effects-generator",
    "parameters": {
        "prompt": "enhanced audio prompt",
        "duration": 5,
        "format": "mp3"
    }
}
```

## Error Handling
- Video and audio generation are independent
- If audio fails, video should still be available
- Track separate status for each

## Cost Considerations
- Each generation (video + audio) will make 2 API calls
- Monitor costs during POC phase
- Consider caching for repeated prompts

## Implementation Order
1. Update Job Processor to emit audio events
2. Create EventBridge rule for audio.job.submitted
3. Update Fal Invoker to handle audio
4. Test with simple audio generation
5. Update frontend to display audio

## Questions for Implementation

1. **Audio-Video Sync**: Should audio match video length exactly?
   - Recommendation: Yes, use same duration

2. **Audio Prompt Enhancement**: Should we modify the prompt for better audio?
   - Recommendation: Add "ambient sounds" or "with sound effects" to prompt

3. **File Storage**: Separate S3 paths for audio?
   - Recommendation: Same bucket, different prefix (/audio vs /video)

4. **Failure Handling**: What if only audio fails?
   - Recommendation: Show video with message "Audio generation failed"

## Next Steps
1. Review this design
2. Implement Phase 1 (Job Processor)
3. Test event emission
4. Proceed with Phase 2 (Fal Invoker)