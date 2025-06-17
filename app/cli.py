"""CLI implementation."""
import argparse
import sys
from typing import List

from app.logger import logger
from app.metrics import start_metrics_server
from app.config import config
from app.consumer import Consumer

def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args (List[str]): Command line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Callback microservice for AMQP messages'
    )
    
    parser.add_argument(
        '--metrics',
        action='store_true',
        help='Start metrics HTTP server'
    )
    
    parser.add_argument(
        '--consumer',
        action='store_true',
        help='Start AMQP consumer'
    )
    
    return parser.parse_args(args)

def main(args: List[str] = None):
    """Main entry point.
    
    Args:
        args (List[str], optional): Command line arguments.
            Defaults to sys.argv[1:].
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    try:
        if parsed_args.metrics:
            logger.info(
                "Starting metrics server",
                extra={
                    'host': config.metrics_host,
                    'port': config.metrics_port
                }
            )
            start_metrics_server(
                host=config.metrics_host,
                port=config.metrics_port
            )
        
        if parsed_args.consumer:
            logger.info("Starting consumer")
            consumer = Consumer()
            consumer.run()
            
        if not (parsed_args.metrics or parsed_args.consumer):
            logger.error("No action specified. Use --help for usage info.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
