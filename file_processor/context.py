"""Processing context for file operations."""

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

# Type alias for stage change callback
StageCallback = Callable[["ProcessingStage"], None]


class ProcessingStage(Enum):
    """Stages of file processing pipeline."""

    INIT = "INIT"
    CHUNKING = "CHUNK"
    # Threat analysis stages
    FIND_RISKS = "RISK"
    FIND_RISKS_CHECK = "RISKC"
    FIND_RISKS_SUMMARIZATION = "RISKS"
    FIND_MITIGATIONS = "MITG"
    FIND_MITIGATIONS_CHECK = "MITGC"
    FIND_MITIGATIONS_SUMMARIZATION = "MITGS"


@dataclass
class ProcessingContext:
    """
    Context for a single file processing operation.

    Holds UUID and current stage for logging purposes.
    """

    file_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    stage: ProcessingStage = ProcessingStage.INIT
    file_name: Optional[str] = None
    _on_stage_change: Optional[StageCallback] = field(default=None, repr=False)

    @property
    def short_id(self) -> str:
        """Return first 1/4 of the UUID (8 characters)."""
        return self.file_id[:8]

    def set_stage(self, stage: ProcessingStage) -> None:
        """Update current processing stage."""
        self.stage = stage
        if self._on_stage_change:
            self._on_stage_change(stage)

    def set_on_stage_change(self, callback: Optional[StageCallback]) -> None:
        """Set callback to be called when stage changes."""
        self._on_stage_change = callback


# Context variable for current processing context
_current_context: ContextVar[Optional[ProcessingContext]] = ContextVar(
    "processing_context", default=None
)

# Global stage change callback
_global_stage_callback: Optional[StageCallback] = None


def get_current_context() -> Optional[ProcessingContext]:
    """Get the current processing context."""
    return _current_context.get()


def set_current_context(ctx: Optional[ProcessingContext]) -> None:
    """Set the current processing context."""
    # Attach global callback if set
    if ctx is not None and _global_stage_callback is not None:
        ctx.set_on_stage_change(_global_stage_callback)
    _current_context.set(ctx)


def set_global_stage_callback(callback: Optional[StageCallback]) -> None:
    """
    Set a global callback for stage changes.

    This callback will be attached to all new contexts.
    """
    global _global_stage_callback
    _global_stage_callback = callback
