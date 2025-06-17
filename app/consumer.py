"""AMQP consumer implementation."""
import json
import asyncio
from typing import Dict, Any
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from aio_pika.exceptions import AMQPConnectionError

from app.logger import logger
from app.metrics import AMQP_RECONNECTS
from app.config import config
from app.callback import CallbackSender

class Consumer:
    """Asynchronous AMQP consumer for callback service."""
    
    def __init__(self):
        """Initialize consumer."""
        self.connection = None
        self.channel = None
        self._closing = False
        self.callback_sender = None
    
    async def connect(self) -> aio_pika.Connection:
        """Connect to AMQP server.
        
        Returns:
            aio_pika.Connection: Connection instance
        """
        try:
            return await aio_pika.connect_robust(config.amqp_url)
        except AMQPConnectionError:
            AMQP_RECONNECTS.inc()
            logger.error("Connection to AMQP failed, retrying...")
            raise
    
    async def setup_channel(self):
        """Set up AMQP channel and declare queue."""
        self.channel = await self.connection.channel()
        
        # Declare queue
        await self.channel.declare_queue(
            name=config.queue,
            durable=True,
            auto_delete=False
        )
        
        # Set QoS
        await self.channel.set_qos(prefetch_count=1)
    
    async def process_message(self, message: AbstractIncomingMessage):
        """Process AMQP message.
        
        Args:
            message (AbstractIncomingMessage): Incoming message
        """
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                
                # Validate message
                required_fields = {'target_url', 'hmac_secret', 'payload'}
                if not all(field in body for field in required_fields):
                    raise ValueError("Missing required fields in message")
                
                # Send callback
                success = await self.callback_sender.send_callback(
                    target_url=body['target_url'],
                    payload=body['payload'],
                    hmac_secret=body['hmac_secret'],
                    method=body.get('target_method')
                )
                
                if not success:
                    # Requeue message on failure
                    await message.nack(requeue=True)
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Requeue message on error
                await message.nack(requeue=True)
    
    async def start_consuming(self):
        """Start consuming messages."""
        try:
            self.connection = await self.connect()
            await self.setup_channel()
            
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
    
    async def run(self):
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
