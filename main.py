"""Main entry point for File Processor Service."""

import argparse
import logging
import sys

from file_processor.config import load_config
from file_processor.handlers import CharCounterHandler
from file_processor.service import FileProcessorService


def setup_logging(config) -> None:
    """Configure logging based on config settings."""
    logging.basicConfig(
        level=getattr(logging, config.logging.level),
        format=config.logging.format,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="File Processor Service"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to configuration file",
        default=None,
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup logging
    setup_logging(config)

    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded successfully")

    # Create handler
    handler = CharCounterHandler()

    # Create and run service
    service = FileProcessorService(config, handler)

    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
