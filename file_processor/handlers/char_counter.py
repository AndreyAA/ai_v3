"""Character counter file handler implementation."""

import logging
from dataclasses import dataclass
from pathlib import Path

from file_processor.handlers.base import BaseFileHandler

logger = logging.getLogger(__name__)


@dataclass
class CharCountResult:
    """Result of character counting operation."""

    file_name: str
    char_count: int


class CharCounterHandler(BaseFileHandler):
    """
    Simple file handler that counts characters in a file.

    This is a test/example handler. Replace with actual
    processing logic as needed.
    """

    def process(self, file_path: Path) -> CharCountResult:
        """
        Count characters in the given file.

        Args:
            file_path: Path to the file to process.

        Returns:
            CharCountResult with file name and character count.
        """
        logger.info("Processing file: %s", file_path.name)

        content = file_path.read_text(encoding="utf-8")
        char_count = len(content)

        logger.info("File %s has %d characters", file_path.name, char_count)

        return CharCountResult(
            file_name=file_path.name,
            char_count=char_count,
        )
