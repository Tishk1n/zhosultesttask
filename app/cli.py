"""CLI implementation."""
import argparse
import asyncio
import sys
from typing import Optional, Sequence

from app.config import config
from app.consumer import Consumer
from app.logger import logger
from app.metrics import start_metrics_server


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args (Optional[Sequence[str]]): Command line arguments

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Callback microservice for AMQP messages"
    )

    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Start metrics HTTP server"
    )
    parser.add_argument(
        "--consumer",
        action="store_true",
        help="Start AMQP consumer"
    )
    parser.add_argument(
        "--metrics-port",
        type=int,
        default=8000,
        help="Port for metrics server"
    )

    return parser.parse_args(args if args is not None else [])


async def amain(args: Optional[Sequence[str]] = None) -> None:
    """Async main entry point.

    Args:
        args (Optional[Sequence[str]], optional): Command line arguments.
            Defaults to sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        description="Callback microservice for AMQP messages"
    )
    parsed_args = parse_args(args)

    try:
        # Start metrics server if requested
        if parsed_args.metrics:
            metrics_port = parsed_args.metrics_port
            logger.info(
                "Starting metrics server",
                extra={
                    "host": config.metrics_host,
                    "port": metrics_port
                }
            )
            start_metrics_server(
                host=config.metrics_host,
                port=metrics_port
            )

        # Start consumer if requested
        if parsed_args.consumer:
            logger.info("Starting consumer")
            consumer = Consumer()
            await consumer.run()

        # If neither service was requested, show help
        if not (parsed_args.metrics or parsed_args.consumer):
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        logger.error("Application error", extra={"error": str(e)})
        sys.exit(1)


def main(args: Optional[Sequence[str]] = None) -> None:
    """Main entry point that runs the async main function.

    Args:
        args (Optional[Sequence[str]], optional): Command line arguments.
            Defaults to sys.argv[1:].
    """
    asyncio.run(amain(args if args is not None else []))
