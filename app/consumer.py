"""AMQP consumer implementation."""
import json
from typing import Dict, Any
import pika
from pika.exceptions import AMQPConnectionError

from app.logger import logger
from app.metrics import AMQP_RECONNECTS
from app.config import config
from app.callback import CallbackSender

class Consumer:
    """AMQP consumer for callback service."""
    
    def __init__(self):
        """Initialize consumer."""
        self.connection = None
        self.channel = None
        self._closing = False
        self.callback_sender = CallbackSender()
    
    def connect(self) -> pika.SelectConnection:
        """Connect to AMQP server.
        
        Returns:
            pika.SelectConnection: Connection instance
        """
        try:
            return pika.BlockingConnection(
                pika.URLParameters(config.amqp_url)
            )
        except AMQPConnectionError:
            AMQP_RECONNECTS.inc()
            logger.error("Connection to AMQP failed, retrying...")
            raise
    
    def setup_channel(self):
        """Set up AMQP channel and declare queue."""
        self.channel = self.connection.channel()
        
        # Declare queue
        self.channel.queue_declare(
            queue=config.queue,
            durable=True,
            auto_delete=False
        )
        
        # Set QoS
        self.channel.basic_qos(prefetch_count=1)
    
    def process_message(
        self,
        channel: pika.channel.Channel,
        method_frame: pika.spec.Basic.Deliver,
        _header_frame: pika.spec.BasicProperties,
        body: bytes
    ):
        """Process AMQP message.
        
        Args:
            channel (pika.channel.Channel): AMQP channel
            method_frame (pika.spec.Basic.Deliver): Delivery frame
            _header_frame (pika.spec.BasicProperties): Message properties
            body (bytes): Message body
        """
        try:
            # Parse message
            message = json.loads(body)
            
            # Validate message
            required_fields = {'target_url', 'hmac_secret', 'payload'}
            if not all(field in message for field in required_fields):
                raise ValueError("Missing required fields in message")
            
            # Send callback
            success = self.callback_sender.send_callback(
                target_url=message['target_url'],
                payload=message['payload'],
                hmac_secret=message['hmac_secret'],
                method=message.get('target_method')
            )
            
            if success:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            else:
                channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag,
                    requeue=True
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Requeue message on error
            channel.basic_nack(
                delivery_tag=method_frame.delivery_tag,
                requeue=True
            )
    
    def start_consuming(self):
        """Start consuming messages."""
        try:
            self.connection = self.connect()
            self.setup_channel()
            
            self.channel.basic_consume(
                queue=config.queue,
                on_message_callback=self.process_message
            )
            
            logger.info(
                "Started consuming",
                extra={'queue': config.queue}
            )
            
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                self.channel.stop_consuming()
                
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            raise
    
    def run(self):
        """Run consumer with automatic reconnection."""
        while not self._closing:
            try:
                self.start_consuming()
            except AMQPConnectionError:
                continue
            except KeyboardInterrupt:
                self._closing = True
                if (
                    self.connection and
                    not self.connection.is_closed
                ):
                    self.connection.close()
