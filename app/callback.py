"""HTTP callback sender module."""
import json
from typing import Dict, Any
import backoff
import aiohttp
from aiohttp import ClientError

from app.logger import logger
from app.metrics import CALLBACK_COUNTER, CALLBACK_DURATION
from app.crypto import generate_hmac_signature
from app.config import config
from app.validators import is_safe_url

class CallbackSender:
    """Asynchronous HTTP callback sender with retries and HMAC signing."""
    
    def __init__(self):
        """Initialize callback sender."""
        self._session = None
        
    async def __aenter__(self):
        """Create aiohttp session on entering context."""
        self._session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session on exiting context."""
        if self._session:
            await self._session.close()
    
    @backoff.on_exception(
        backoff.expo,
        ClientError,
        max_tries=config.retry_attempts,
        jitter=None
    )
    async def send_callback(
        self,
        target_url: str,
        payload: Dict[str, Any],
        hmac_secret: str,
        method: str = None
    ) -> bool:
        """Send callback to target URL with HMAC signature.
        
        Args:
            target_url (str): Target URL to send callback to
            payload (Dict[str, Any]): Payload to send
            hmac_secret (str): Secret for HMAC signing
            method (str, optional): HTTP method to use. Defaults to POST.
            
        Returns:
            bool: True if callback was successful, False otherwise
        """
        method = method or config.default_method
        
        try:
            # Validate URL
            if not is_safe_url(target_url):
                logger.error(
                    "Invalid or unsafe target URL",
                    extra={'target_url': target_url}
                )
                CALLBACK_COUNTER.labels(status='error').inc()
                return False

            with CALLBACK_DURATION.labels(target_url=target_url).time():
                # Generate HMAC signature
                signature = generate_hmac_signature(payload, hmac_secret)
                
                # Prepare headers
                headers = {
                    'Content-Type': 'application/json',
                    'X-Signature': signature
                }
                
                # Send request
                async with self._session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    json=payload
                ) as response:
                    # Check response
                    response.raise_for_status()
                    
                    logger.info(
                        "Callback sent successfully",
                        extra={
                            'target_url': target_url,
                            'status_code': response.status
                        }
                    )
                    CALLBACK_COUNTER.labels(status='success').inc()
                    return True
                
        except Exception as e:
            logger.error(
                f"Error sending callback: {e}",
                extra={
                    'target_url': target_url,
                    'error': str(e)
                }
            )
            CALLBACK_COUNTER.labels(status='error').inc()
            raise
