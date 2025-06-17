"""Crypto utilities for HMAC signing."""
import hmac
import hashlib
import json
from typing import Any, Dict

from app.logger import logger

def generate_hmac_signature(payload: Dict[str, Any], secret: str) -> str:
    """Generate HMAC signature for payload.
    
    Args:
        payload (Dict[str, Any]): Payload to sign
        secret (str): Secret key for HMAC
        
    Returns:
        str: HMAC signature as hex string
    """
    try:
        # Sort keys to ensure consistent ordering
        payload_str = json.dumps(payload, sort_keys=True)
        
        # Create HMAC with SHA256
        signature = hmac.new(
            key=secret.encode(),
            msg=payload_str.encode(),
            digestmod=hashlib.sha256
        )
        
        return signature.hexdigest()
        
    except Exception as e:
        logger.error(f"Error generating HMAC signature: {e}")
        raise
