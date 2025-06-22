"""
Download feature logic for TeraBox Bot
"""
import logging
from mongodb_config import MongoVideo, MongoDownload

logger = logging.getLogger(__name__)

async def get_download_url(video_id: str) -> str:
    """Get download URL for a video"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return None
        
        download_urls = video.get('download_urls', [])
        
        if isinstance(download_urls, str):
            import json
            try:
                download_urls = json.loads(download_urls)
            except:
                download_urls = [download_urls]
        
        if download_urls and len(download_urls) > 0:
            # Log download attempt
            await MongoDownload.create({
                "user_id": video.get("user_id"),
                "video_id": video_id,
                "download_type": "download"
            })
            
            return download_urls[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting download URL for {video_id}: {e}")
        return None

async def get_all_download_urls(video_id: str) -> list:
    """Get all available download URLs for a video"""
    try:
        video = await MongoVideo.find_by_id(video_id)
        if not video:
            return []
        
        download_urls = video.get('download_urls', [])
        
        if isinstance(download_urls, str):
            import json
            try:
                download_urls = json.loads(download_urls)
            except:
                download_urls = [download_urls]
        
        return download_urls if isinstance(download_urls, list) else []
        
    except Exception as e:
        logger.error(f"Error getting download URLs for {video_id}: {e}")
        return []

async def process_download_request(video_id: str, user_id: int, ip_address: str = None):
    """Process a download request and log it"""
    try:
        # Log download
        await MongoDownload.create({
            "user_id": user_id,
            "video_id": video_id,
            "download_type": "download",
            "ip_address": ip_address
        })
        
        # Get download URL
        return await get_download_url(video_id)
        
    except Exception as e:
        logger.error(f"Error processing download request: {e}")
        return None