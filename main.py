"""Main entry point for File Processor Service."""

import argparse
import logging
import sys

from file_processor.config import load_config
from file_processor.handlers import PipelineHandler
from file_processor.logging_utils import setup_logging
from file_processor.service import FileProcessorService


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

    # Setup logging with context support
    setup_logging(config.logging.level)

    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded successfully")

    # Create pipeline handler with chunking
    handler = PipelineHandler(config.chunking)

    # Create and run service
    service = FileProcessorService(config, handler)

    try:
        service.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
