"""Validation utilities."""
from urllib.parse import urlparse
from typing import Optional

def is_safe_url(url: str) -> bool:
    """Validate if URL is safe to make requests to.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ('http', 'https'):
            return False
            
        # Prevent localhost, 127.0.0.1 etc
        if parsed.hostname in ('localhost', '127.0.0.1', '::1'):
            return False
            
        # Prevent internal network access
        if parsed.hostname.startswith(('10.', '172.', '192.168.')):
            return False
            
        # Require hostname
        if not parsed.hostname:
            return False
            
        return True
        
    except Exception:
        return False
