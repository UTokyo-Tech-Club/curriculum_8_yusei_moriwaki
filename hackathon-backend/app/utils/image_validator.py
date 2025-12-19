"""
Image URL validation utility.
"""
import httpx
from typing import List, Tuple
from urllib.parse import urlparse


async def validate_image_url(url: str, timeout: float = 2.0) -> bool:
    """
    Validate if an image URL is accessible and returns an image.
    
    Args:
        url: The image URL to validate
        timeout: Request timeout in seconds
        
    Returns:
        True if URL is valid and accessible, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
    except Exception:
        return False
    
    # Check if it's a data URL (always valid)
    if url.startswith('data:image/'):
        return True
    
    # Try to fetch the image
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(url, follow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                # Check if it's an image
                if content_type.startswith('image/'):
                    return True
    except Exception:
        pass
    
    # If HEAD fails, try GET with limited data
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, follow_redirects=True, timeout=timeout)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if content_type.startswith('image/'):
                    return True
    except Exception:
        pass
    
    return False


async def validate_image_urls(urls: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate a list of image URLs.
    
    Args:
        urls: List of image URLs to validate
        
    Returns:
        Tuple of (valid_urls, invalid_urls)
    """
    if not urls:
        return [], []
    
    valid_urls = []
    invalid_urls = []
    
    for url in urls:
        if await validate_image_url(url):
            valid_urls.append(url)
        else:
            invalid_urls.append(url)
    
    return valid_urls, invalid_urls


