"""HTTP callback sender module."""
from types import TracebackType
from typing import Any, Dict, Literal, Optional, Type, TypeVar

import backoff
from aiohttp import ClientError, ClientSession

from app.config import config
from app.crypto import generate_hmac_signature
from app.logger import logger
from app.metrics import CALLBACK_COUNTER, CALLBACK_DURATION
from app.validators import is_safe_url

T = TypeVar("T", bound="CallbackSender")
HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class CallbackSender:
    """Asynchronous HTTP callback sender with retries and HMAC signing."""

    def __init__(self) -> None:
        """Initialize callback sender."""
        self._session: Optional[ClientSession] = None

    async def __aenter__(self: T) -> T:
        """Create aiohttp session on entering context."""
        self._session = ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Close aiohttp session on exiting context."""
        if self._session:
            await self._session.close()
            self._session = None

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
        method: Optional[HttpMethod] = None,
    ) -> bool:
        """Send callback to target URL with HMAC signature.

        Args:
            target_url (str): Target URL to send callback to
            payload (Dict[str, Any]): Payload to send
            hmac_secret (str): Secret for HMAC signing
            method (HttpMethod, optional): HTTP method to use. Defaults to POST.

        Returns:
            bool: True if callback was successful, False otherwise

        Raises:
            RuntimeError: If session is not initialized
            ClientError: On HTTP errors (will be retried)
            ValueError: On invalid input
        """
        if not self._session:
            raise RuntimeError("Session not initialized")

        used_method = method if method is not None else config.default_method.upper()

        try:
            # Validate URL
            if not is_safe_url(target_url):
                logger.error(
                    "Invalid or unsafe target URL",
                    extra={"target_url": target_url}
                )
                CALLBACK_COUNTER.labels(status="error").inc()
                return False

            with CALLBACK_DURATION.labels(target_url=target_url).time():
                # Generate HMAC signature
                signature = generate_hmac_signature(payload, hmac_secret)

                # Prepare headers
                headers = {
                    "Content-Type": "application/json",
                    "X-Signature": signature
                }

                # Send request
                async with self._session.request(
                    method=used_method,
                    url=target_url,
                    headers=headers,
                    json=payload
                ) as response:
                    # Check response
                    response.raise_for_status()

                    logger.info(
                        "Callback sent successfully",
                        extra={
                            "target_url": target_url,
                            "status_code": response.status
                        }
                    )
                    CALLBACK_COUNTER.labels(status="success").inc()
                    return True

        except Exception as e:
            logger.error(
                "Error sending callback",
                extra={
                    "target_url": target_url,
                    "error": str(e)
                }
            )
            CALLBACK_COUNTER.labels(status="error").inc()
            raise
