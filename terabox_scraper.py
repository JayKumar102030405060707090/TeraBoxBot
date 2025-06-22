import re
import aiohttp
import asyncio
import json
import logging
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup
import trafilatura

logger = logging.getLogger(__name__)

class TeraBoxScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def extract_video_info(self, url):
        """Extract video information from TeraBox URL"""
        try:
            session = await self.get_session()
            
            # First, try to get the page content
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch URL: {response.status}")
                    return None
                
                html_content = await response.text()
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract video information using multiple methods
            video_info = await self._extract_from_page(soup, url, session)
            
            if not video_info:
                # Try alternative extraction methods
                video_info = await self._extract_from_api(url, session)
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error extracting video info: {e}")
            return None
    
    async def _extract_from_page(self, soup, url, session):
        """Extract video info from HTML page"""
        try:
            video_info = {}
            
            # Try to find video title
            title_selectors = [
                'title',
                '.file-name',
                '.filename',
                'h1',
                '.video-title',
                '[data-title]'
            ]
            
            title = None
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True) or element.get('data-title')
                    if title and len(title) > 5:  # Basic validation
                        break
            
            if not title:
                # Try to extract from URL or meta tags
                title = self._extract_title_from_meta(soup) or self._extract_title_from_url(url)
            
            video_info['title'] = title or 'Unknown Video'
            
            # Try to find download links
            download_urls = await self._find_download_urls(soup, url, session)
            video_info['download_urls'] = download_urls
            
            # Try to find video URL for streaming
            video_url = await self._find_video_url(soup, url, session)
            video_info['video_url'] = video_url
            
            # Try to extract file size and other metadata
            file_info = self._extract_file_info(soup)
            video_info.update(file_info)
            
            # Try to find thumbnail
            thumbnail = self._find_thumbnail(soup)
            video_info['thumbnail_url'] = thumbnail
            
            return video_info if download_urls or video_url else None
            
        except Exception as e:
            logger.error(f"Error extracting from page: {e}")
            return None
    
    async def _extract_from_api(self, url, session):
        """Try to extract using API endpoints"""
        try:
            # Extract file ID from URL
            file_id = self._extract_file_id(url)
            if not file_id:
                return None
            
            # Try different API endpoints
            api_endpoints = [
                f"https://www.terabox.com/api/file/download?fid={file_id}",
                f"https://teraboxlink.com/api/file/info?id={file_id}",
            ]
            
            for endpoint in api_endpoints:
                try:
                    async with session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            video_info = self._parse_api_response(data)
                            if video_info:
                                return video_info
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting from API: {e}")
            return None
    
    async def _find_download_urls(self, soup, original_url, session):
        """Find download URLs from the page"""
        download_urls = []
        
        # Look for direct download links
        download_selectors = [
            'a[href*="download"]',
            'a[href*="dl."]',
            'a[data-url]',
            '.download-btn',
            '.btn-download',
            'a[href*=".mp4"]',
            'a[href*=".mkv"]',
            'a[href*=".avi"]'
        ]
        
        for selector in download_selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href') or element.get('data-url')
                if href:
                    if href.startswith('/'):
                        href = f"https://www.terabox.com{href}"
                    elif not href.startswith('http'):
                        continue
                    download_urls.append(href)
        
        # Look for JavaScript variables containing download URLs
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for download URLs in JavaScript
                url_patterns = [
                    r'"(https?://[^"]*\.mp4[^"]*)"',
                    r'"(https?://[^"]*download[^"]*)"',
                    r'"download_url":\s*"([^"]+)"',
                    r'"dlink":\s*"([^"]+)"'
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        if match not in download_urls:
                            download_urls.append(match)
        
        # If no direct download URLs found, try to generate them
        if not download_urls:
            download_urls = await self._generate_download_urls(original_url, session)
        
        return list(set(download_urls))  # Remove duplicates
    
    async def _find_video_url(self, soup, original_url, session):
        """Find streaming video URL"""
        # Look for video tags
        video_element = soup.find('video')
        if video_element:
            src = video_element.get('src')
            if src:
                return src if src.startswith('http') else f"https://www.terabox.com{src}"
        
        # Look for source tags
        source_elements = soup.find_all('source')
        for source in source_elements:
            src = source.get('src')
            if src and any(ext in src for ext in ['.mp4', '.webm', '.ogg']):
                return src if src.startswith('http') else f"https://www.terabox.com{src}"
        
        # Look in JavaScript for video URLs
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                patterns = [
                    r'"video_url":\s*"([^"]+)"',
                    r'"stream_url":\s*"([^"]+)"',
                    r'"playUrl":\s*"([^"]+)"'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        return match.group(1)
        
        return None
    
    async def _generate_download_urls(self, original_url, session):
        """Generate potential download URLs"""
        download_urls = []
        
        # Try common download URL patterns
        base_patterns = [
            original_url.replace('/s/', '/dl/'),
            original_url + '&download=1',
            original_url + '/download',
            original_url.replace('terabox.com', 'dl.terabox.com'),
        ]
        
        for pattern in base_patterns:
            # Validate URL before adding
            try:
                async with session.head(pattern, allow_redirects=True) as response:
                    if response.status in [200, 302]:
                        download_urls.append(str(response.url))
            except:
                continue
        
        return download_urls
    
    def _extract_file_info(self, soup):
        """Extract file information like size, duration"""
        info = {}
        
        # Look for file size
        size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(MB|GB|KB)',
            r'Size:\s*(\d+(?:\.\d+)?)\s*(MB|GB|KB)',
            r'(\d+(?:\.\d+)?)\s*(mb|gb|kb)'
        ]
        
        text_content = soup.get_text()
        for pattern in size_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                size_value = float(match.group(1))
                size_unit = match.group(2).upper()
                
                # Convert to bytes
                multipliers = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
                info['file_size'] = int(size_value * multipliers.get(size_unit, 1))
                break
        
        # Look for duration
        duration_patterns = [
            r'(\d+):(\d+):(\d+)',  # HH:MM:SS
            r'(\d+):(\d+)',        # MM:SS
            r'Duration:\s*(\d+):(\d+):(\d+)',
            r'Length:\s*(\d+):(\d+)'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text_content)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    hours, minutes, seconds = map(int, groups)
                    info['duration'] = hours * 3600 + minutes * 60 + seconds
                elif len(groups) == 2:
                    minutes, seconds = map(int, groups)
                    info['duration'] = minutes * 60 + seconds
                break
        
        return info
    
    def _find_thumbnail(self, soup):
        """Find video thumbnail"""
        # Look for image tags
        img_selectors = [
            'img[src*="thumb"]',
            'img[src*="preview"]',
            'img[data-src*="thumb"]',
            '.thumbnail img',
            '.preview img'
        ]
        
        for selector in img_selectors:
            img = soup.select_one(selector)
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    return src if src.startswith('http') else f"https://www.terabox.com{src}"
        
        # Look for meta tags
        meta_image = soup.find('meta', property='og:image')
        if meta_image:
            return meta_image.get('content')
        
        return None
    
    def _extract_title_from_meta(self, soup):
        """Extract title from meta tags"""
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            return meta_title.get('content')
        
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title:
            return meta_title.get('content')
        
        return None
    
    def _extract_title_from_url(self, url):
        """Extract title from URL"""
        try:
            # Parse URL to get filename
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            
            # Look for filename in path
            for part in reversed(path_parts):
                if part and '.' in part:
                    # Remove file extension
                    return part.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
            
            # Look in query parameters
            query_params = parse_qs(parsed.query)
            for key in ['filename', 'title', 'name']:
                if key in query_params:
                    return unquote(query_params[key][0])
            
        except:
            pass
        
        return "TeraBox Video"
    
    def _extract_file_id(self, url):
        """Extract file ID from TeraBox URL"""
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
    
    def _parse_api_response(self, data):
        """Parse API response data"""
        try:
            if not isinstance(data, dict):
                return None
            
            video_info = {}
            
            # Try different response formats
            if 'file_info' in data:
                file_info = data['file_info']
                video_info['title'] = file_info.get('filename', 'Unknown')
                video_info['file_size'] = file_info.get('size', 0)
                video_info['download_urls'] = file_info.get('download_urls', [])
            
            elif 'title' in data:
                video_info['title'] = data['title']
                video_info['file_size'] = data.get('size', 0)
                video_info['download_urls'] = data.get('urls', [])
            
            return video_info if video_info else None
            
        except:
            return None
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
