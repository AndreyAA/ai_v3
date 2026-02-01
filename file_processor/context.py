"""Processing context for file operations."""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessingStage(Enum):
    """Stages of file processing pipeline."""

    INIT = "INIT"
    CHUNKING = "CHUNK"
    # Future stages will be added here


@dataclass
class ProcessingContext:
    """
    Context for a single file processing operation.

    Holds UUID and current stage for logging purposes.
    """

    file_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    stage: ProcessingStage = ProcessingStage.INIT
    file_name: Optional[str] = None

    @property
    def short_id(self) -> str:
        """Return first 1/4 of the UUID (8 characters)."""
        return self.file_id[:8]

    def set_stage(self, stage: ProcessingStage) -> None:
        """Update current processing stage."""
        self.stage = stage


# Context variable for current processing context
_current_context: ContextVar[Optional[ProcessingContext]] = ContextVar(
    "processing_context", default=None
)


def get_current_context() -> Optional[ProcessingContext]:
    """Get the current processing context."""
    return _current_context.get()


def set_current_context(ctx: Optional[ProcessingContext]) -> None:
    """Set the current processing context."""
    _current_context.set(ctx)
