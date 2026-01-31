"""File handlers package."""

from file_processor.handlers.base import BaseFileHandler
from file_processor.handlers.char_counter import CharCounterHandler

__all__ = ["BaseFileHandler", "CharCounterHandler"]
