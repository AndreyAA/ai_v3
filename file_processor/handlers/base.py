"""Base file handler abstraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseFileHandler(ABC):
    """
    Abstract base class for file handlers.

    Inherit from this class to implement custom file processing logic.
    """

    @abstractmethod
    def process(self, file_path: Path) -> Any:
        """
        Process a single file.

        Args:
            file_path: Path to the file to process.

        Returns:
            Processing result (type depends on implementation).

        Raises:
            Exception: If processing fails.
        """
        pass

    def get_name(self) -> str:
        """Return handler name for logging purposes."""
        return self.__class__.__name__
