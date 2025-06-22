import re
import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if not seconds:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def validate_terabox_url(url: str) -> bool:
    """Validate if URL is a valid TeraBox link"""
    if not url:
        return False
    
    patterns = [
        r'https?://(?:www\.)?terabox\.com/',
        r'https?://(?:www\.)?teraboxlink\.com/',
        r'https?://(?:www\.)?1024terabox\.com/',
        r'https?://(?:www\.)?4funbox\.com/',
    ]
    
    return any(re.match(pattern, url) for pattern in patterns)

def extract_terabox_id(url: str) -> Optional[str]:
    """Extract TeraBox file ID from URL"""
    patterns = [
        r'/s/([a-zA-Z0-9_-]+)',
        r'[?&]fid=([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
        r'/([a-zA-Z0-9_-]{10,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def generate_unique_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def hash_string(text: str) -> str:
    """Generate MD5 hash of a string"""
    return hashlib.md5(text.encode()).hexdigest()

def clean_filename(filename: str) -> str:
    """Clean filename for safe storage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and dots
    filename = re.sub(r'\.+', '.', filename.strip())
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    
    return filename

def is_video_file(filename: str) -> bool:
    """Check if filename is a video file"""
    video_extensions = [
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.3gp', '.ogv', '.ts', '.mts', '.vob'
    ]
    
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def sanitize_html(text: str) -> str:
    """Basic HTML sanitization"""
    if not text:
        return ""
    
    # Remove potentially dangerous HTML tags
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed']
    for tag in dangerous_tags:
        text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text

def parse_video_quality(width: int, height: int) -> str:
    """Parse video quality from dimensions"""
    if height >= 2160:
        return '4K'
    elif height >= 1440:
        return '1440p'
    elif height >= 1080:
        return '1080p'
    elif height >= 720:
        return '720p'
    elif height >= 480:
        return '480p'
    elif height >= 360:
        return '360p'
    else:
        return '240p'

def time_ago(dt: datetime) -> str:
    """Get human-readable time difference"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def validate_url(url: str) -> bool:
    """Validate if string is a valid URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return None

def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None):
    """Log user action for analytics"""
    try:
        log_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        logger.info(f"User action: {log_data}")
    except Exception as e:
        logger.error(f"Error logging user action: {e}")

def rate_limit_key(user_id: int) -> str:
    """Generate rate limit key for user"""
    return f"rate_limit:{user_id}"

def is_mobile_user_agent(user_agent: str) -> bool:
    """Check if user agent is from mobile device"""
    if not user_agent:
        return False
    
    mobile_patterns = [
        r'Mobile', r'Android', r'iPhone', r'iPad', 
        r'Windows Phone', r'BlackBerry', r'Opera Mini'
    ]
    
    return any(re.search(pattern, user_agent, re.IGNORECASE) for pattern in mobile_patterns)
