"""Crypto utilities for HMAC signing."""
import hashlib
import hmac
import json
from typing import Any, Dict, Final

from app.logger import logger
from app.metrics import HMAC_ERRORS

# Constants
ENCODING: Final[str] = 'utf-8'
HASH_ALGORITHM: Final[str] = 'sha256'


def generate_hmac_signature(payload: Dict[str, Any], secret: str) -> str:
    """Generate HMAC signature for payload.

    Args:
        payload (Dict[str, Any]): Payload to sign
        secret (str): Secret key for HMAC

    Returns:
        str: HMAC signature as hex string

    Raises:
        ValueError: If payload or secret is invalid
        TypeError: If payload cannot be serialized to JSON
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("Invalid HMAC secret")

    try:
        # Sort keys to ensure consistent ordering
        payload_str = json.dumps(payload, sort_keys=True)

        # Create HMAC with SHA256
        signature = hmac.new(
            key=secret.encode(ENCODING),
            msg=payload_str.encode(ENCODING),
            digestmod=hashlib.sha256
        )

        return signature.hexdigest()

    except (TypeError, ValueError) as e:
        HMAC_ERRORS.inc()
        logger.error(f"Error generating HMAC signature: {e}")
        raise
    except Exception as e:
        HMAC_ERRORS.inc()
        logger.error(f"Unexpected error generating HMAC signature: {e}")
        raise
