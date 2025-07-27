"""
Shared type definitions for Video Generation Service
This file should be imported by Lambda functions
"""
from typing import Literal, Union
from enum import Enum

# Model tier type definition
ModelTier = Literal['fast', 'standard', 'pro', 'veo3_fast', 'veo3_pro']

# Legacy tier mapping for backward compatibility
LEGACY_TIER_MAPPING = {
    'balanced': 'standard',
    'premium': 'pro'
}

# Default tier for backward compatibility
DEFAULT_MODEL_TIER: ModelTier = 'fast'

# Valid model tiers list
VALID_MODEL_TIERS = ['fast', 'standard', 'pro', 'veo3_fast', 'veo3_pro']

# Model to fal.ai model ID mapping (without fal-ai/ prefix - added by invoker)
MODEL_TIER_TO_FAL_MODEL = {
    'fast': 'ltx-video',  # Text-to-video model for POC
    'standard': 'ltx-video-13b-distilled',  # $0.02/second
    'pro': 'wan-i2v',  # $0.40/video at 720p
    'veo3_fast': 'veo3-fast',  # Premium pricing
    'veo3_pro': 'veo3-pro'  # Premium pricing
}

def is_valid_model_tier(tier: str) -> bool:
    """Validate if a string is a valid model tier"""
    return tier in VALID_MODEL_TIERS or tier in LEGACY_TIER_MAPPING

def validate_and_default_tier(tier: Union[str, None]) -> ModelTier:
    """
    Validate tier parameter and return default if missing or invalid
    
    Args:
        tier: The tier string to validate (can be None)
        
    Returns:
        Valid ModelTier, defaulting to 'fast' if input is invalid/missing
    """
    if tier is None:
        return DEFAULT_MODEL_TIER
    
    # Handle legacy tier names
    if tier in LEGACY_TIER_MAPPING:
        return LEGACY_TIER_MAPPING[tier]
    
    if is_valid_model_tier(tier):
        return tier
    
    # Return default for invalid tiers (for backward compatibility)
    return DEFAULT_MODEL_TIER

# Model tier display names
MODEL_TIER_DISPLAY_NAMES = {
    'fast': 'Fast (Budget)',
    'standard': 'Standard (LTX-Video)',
    'pro': 'Pro (Premium Quality)',
    'veo3_fast': 'VEO-3 Fast (Premium)',
    'veo3_pro': 'VEO-3 Pro (Premium)'
}

# Model tier descriptions
MODEL_TIER_DESCRIPTIONS = {
    'fast': 'Budget option for testing - fastest generation',
    'standard': 'Good quality at $0.02/second - recommended',
    'pro': 'High quality video generation',
    'veo3_fast': 'VEO-3 Fast mode - premium pricing',
    'veo3_pro': 'VEO-3 highest quality - premium pricing'
}

# Credit consumption per tier (for future implementation)
MODEL_TIER_CREDITS = {
    'fast': 1,
    'standard': 2,
    'pro': 3,
    'veo3_fast': 4,
    'veo3_pro': 5
}

# Audio tier type definition
AudioTier = Literal['fast', 'standard', 'pro']

# Audio model mapping
AUDIO_TIER_TO_FAL_MODEL = {
    'fast': 'fal-ai/cassetteai/sound-effects-generator',  # ~$0.01-0.02 for POC
    'standard': 'fal-ai/minimax-music',  # $0.035 per generation
    'pro': 'fal-ai/elevenlabs/sound-effects'  # Premium audio
}

# Audio tier display names
AUDIO_TIER_DISPLAY_NAMES = {
    'fast': 'Fast Audio (POC)',
    'standard': 'Standard Audio',
    'pro': 'Pro Audio'
}

class JobStatus(Enum):
    """Job status enumeration"""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING" 
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"