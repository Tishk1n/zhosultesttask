"""AMQP consumer implementation."""
import json
from typing import Any, Dict, Optional, TypedDict

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractIncomingMessage
from aio_pika.exceptions import AMQPConnectionError

from app.callback import CallbackSender, HttpMethod
from app.config import config
from app.logger import logger
from app.metrics import AMQP_RECONNECTS


class CallbackMessageRequired(TypedDict):
    """Required fields for callback message."""
    target_url: str
    hmac_secret: str
    payload: Dict[str, Any]


class CallbackMessage(CallbackMessageRequired, total=False):
    """Complete callback message type.

    Required fields (inherited from CallbackMessageRequired):
        target_url: Target URL to send callback to
        hmac_secret: Secret for HMAC signing
        payload: Payload to send

    Optional fields:
        target_method: HTTP method to use
    """
    target_method: Optional[str]


VALID_HTTP_METHODS: set[str] = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def validate_http_method(method: Optional[str]) -> Optional[HttpMethod]:
    """Validate and convert HTTP method string to HttpMethod type.

    Args:
        method (Optional[str]): HTTP method string to validate

    Returns:
        Optional[HttpMethod]: Valid HTTP method or None if not valid
    """
    if method is None:
        return None

    method_upper = method.upper()
    if method_upper in VALID_HTTP_METHODS:
        return method_upper  # type: ignore

    logger.warning(f"Invalid HTTP method: {method}")
    return None


class Consumer:
    """Asynchronous AMQP consumer for callback service."""

    def __init__(self) -> None:
        """Initialize consumer."""
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self._closing: bool = False
        self.callback_sender: Optional[CallbackSender] = None

    async def connect(self) -> AbstractConnection:
        """Connect to AMQP server.

        Returns:
            AbstractConnection: Connection instance

        Raises:
            AMQPConnectionError: If connection fails
        """
        try:
            return await aio_pika.connect_robust(config.amqp_url)
        except AMQPConnectionError:
            AMQP_RECONNECTS.inc()
            logger.error("Connection to AMQP failed, retrying...")
            raise

    async def setup_channel(self) -> None:
        """Set up AMQP channel and declare queue.

        Raises:
            RuntimeError: If connection is not initialized
        """
        if not self.connection:
            raise RuntimeError("Connection not initialized")

        self.channel = await self.connection.channel()

        # Declare queue
        await self.channel.declare_queue(
            name=config.queue,
            durable=True,
            auto_delete=False
        )

        # Set QoS
        await self.channel.set_qos(prefetch_count=1)

    async def process_message(self, message: AbstractIncomingMessage) -> None:
        """Process AMQP message.

        Args:
            message (AbstractIncomingMessage): Incoming message

        Raises:
            ValueError: If message is missing required fields
            json.JSONDecodeError: If message body is invalid JSON
        """
        async with message.process():
            try:
                # Parse and validate message
                try:
                    raw_body = json.loads(message.body.decode())

                    # Check required fields are present and have correct types
                    if not isinstance(raw_body, dict):
                        raise ValueError("Message body must be a JSON object")

                    required_fields = {
                        'target_url': str,
                        'hmac_secret': str,
                        'payload': dict
                    }

                    for field, expected_type in required_fields.items():
                        if field not in raw_body:
                            raise ValueError(f"Missing required field: {field}")
                        if not isinstance(raw_body[field], expected_type):
                            raise ValueError(
                                f"Field {field} must be of type {expected_type.__name__}"
                            )

                    # Now we can safely cast to our TypedDict
                    body: CallbackMessage = raw_body  # type: ignore

                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Invalid message format: {e}")
                    # Don't requeue invalid messages
                    return

                if not self.callback_sender:
                    raise RuntimeError("Callback sender not initialized")

                # Validate HTTP method
                method = validate_http_method(body.get('target_method'))

                # Send callback
                success = await self.callback_sender.send_callback(
                    target_url=body['target_url'],
                    payload=body['payload'],
                    hmac_secret=body['hmac_secret'],
                    method=method
                )

                if not success:
                    # Requeue message on failure
                    await message.nack(requeue=True)

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Requeue message on error
                await message.nack(requeue=True)

    async def start_consuming(self) -> None:
        """Start consuming messages.

        Raises:
            AMQPConnectionError: If connection fails
            RuntimeError: If channel is not initialized
        """
        try:
            self.connection = await self.connect()
            await self.setup_channel()

            if not self.channel:
                raise RuntimeError("Channel not initialized")

            queue = await self.channel.get_queue(config.queue)
            self.callback_sender = CallbackSender()

            async with self.callback_sender:
                logger.info(
                    "Started consuming",
                    extra={'queue': config.queue}
                )

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        if self._closing:
                            break
                        await self.process_message(message)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            raise

    async def run(self) -> None:
        """Run consumer with automatic reconnection."""
        while not self._closing:
            try:
                await self.start_consuming()
            except AMQPConnectionError:
                continue
            except KeyboardInterrupt:
                self._closing = True
                if (
                    self.connection and
                    not self.connection.is_closed
                ):
                    await self.connection.close()
