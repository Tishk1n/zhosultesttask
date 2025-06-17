"""HTTP callback sender module."""
import json
from typing import Dict, Any
import backoff
import requests
from requests.exceptions import RequestException

from app.logger import logger
from app.metrics import CALLBACK_COUNTER, CALLBACK_DURATION
from app.crypto import generate_hmac_signature
from app.config import config

class CallbackSender:
    """HTTP callback sender with retries and HMAC signing."""
    
    def __init__(self):
        """Initialize callback sender."""
        self.session = requests.Session()
    
    @backoff.on_exception(
        backoff.expo,
        RequestException,
        max_tries=config.retry_attempts,
        jitter=None
    )
    def send_callback(
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
            with CALLBACK_DURATION.labels(target_url=target_url).time():
                # Generate HMAC signature
                signature = generate_hmac_signature(payload, hmac_secret)
                
                # Prepare headers
                headers = {
                    'Content-Type': 'application/json',
                    'X-Signature': signature
                }
                
                # Send request
                response = self.session.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    json=payload
                )
                
                # Check response
                response.raise_for_status()
                
                logger.info(
                    "Callback sent successfully",
                    extra={
                        'target_url': target_url,
                        'status_code': response.status_code
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
