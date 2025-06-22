"""
Stream feature logic for TeraBox Bot
"""
import logging
from mongodb_config import MongoVideo, MongoDownload

logger = logging.getLogger(__name__)

async def get_video_by_id(video_id: str):
    """Get video data by ID for streaming"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return None
        
        # Log stream access
        await MongoDownload.create({
            "user_id": video.get("user_id"),
            "video_id": video_id,
            "download_type": "stream"
        })
        
        return video
        
    except Exception as e:
        logger.error(f"Error getting video for streaming {video_id}: {e}")
        return None

def get_video_by_id_sync(video_id: str):
    """Synchronous version for FastAPI compatibility"""
    from mongodb_config import videos_sync
    from bson import ObjectId
    
    try:
        return videos_sync.find_one({"_id": ObjectId(video_id)})
    except Exception as e:
        logger.error(f"Error getting video sync {video_id}: {e}")
        return None

async def get_stream_url(video_id: str) -> str:
    """Get streaming URL for a video"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return None
        
        return video.get('video_url')
        
    except Exception as e:
        logger.error(f"Error getting stream URL for {video_id}: {e}")
        return None

async def process_stream_request(video_id: str, user_id: int, ip_address: str = None):
    """Process a stream request and log it"""
    try:
        # Log stream
        await MongoDownload.create({
            "user_id": user_id,
            "video_id": video_id,
            "download_type": "stream",
            "ip_address": ip_address
        })
        
        # Get video data
        return await get_video_by_id(video_id)
        
    except Exception as e:
        logger.error(f"Error processing stream request: {e}")
        return None

async def get_video_stats(video_id: str):
    """Get streaming statistics for a video"""
    try:
        from mongodb_config import downloads_collection
        
        total_streams = await downloads_collection.count_documents({
            "video_id": video_id,
            "download_type": "stream"
        })
        
        total_downloads = await downloads_collection.count_documents({
            "video_id": video_id,
            "download_type": "download"
        })
        
        return {
            "total_streams": total_streams,
            "total_downloads": total_downloads
        }
        
    except Exception as e:
        logger.error(f"Error getting video stats for {video_id}: {e}")
        return {"total_streams": 0, "total_downloads": 0}