"""
Info feature logic for TeraBox Bot
"""
import logging
from utils import format_file_size
from mongodb_config import MongoVideo

logger = logging.getLogger(__name__)

async def get_video_details(video_id: str):
    """Get detailed video information"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return None
        
        return {
            'id': str(video['_id']),
            'title': video.get('title', 'Unknown Title'),
            'file_size': video.get('file_size', 0),
            'file_size_formatted': format_file_size(video.get('file_size', 0)),
            'duration': video.get('duration', 0),
            'video_url': video.get('video_url'),
            'download_urls': video.get('download_urls', []),
            'thumbnail_url': video.get('thumbnail_url'),
            'created_at': video.get('created_at').isoformat() if video.get('created_at') else None,
            'status': video.get('status', 'unknown'),
            'original_url': video.get('original_url')
        }
        
    except Exception as e:
        logger.error(f"Error getting video details for {video_id}: {e}")
        return None

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

async def get_video_metadata(video_id: str):
    """Get basic video metadata"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return None
        
        return {
            'title': video.get('title'),
            'size': format_file_size(video.get('file_size', 0)),
            'duration': format_duration(video.get('duration', 0)),
            'status': video.get('status', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error getting video metadata for {video_id}: {e}")
        return None

async def check_video_exists(video_id: str, user_id: int = None):
    """Check if video exists and optionally verify user access"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return False
        
        if user_id and video.get("user_id") != user_id:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking video existence {video_id}: {e}")
        return False