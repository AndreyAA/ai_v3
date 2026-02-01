"""Queue state tracking for monitoring."""

import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from file_processor.context import ProcessingStage


@dataclass
class QueuedFile:
    """Information about a file in the queue."""

    name: str
    size_bytes: int
    queued_at: float  # timestamp

    @property
    def time_in_queue_sec(self) -> float:
        """Time this file has been in queue."""
        return time.time() - self.queued_at


@dataclass
class ProcessingFile:
    """Information about the currently processing file."""

    name: str
    size_bytes: int
    queued_at: float
    started_at: float
    stage: ProcessingStage = ProcessingStage.INIT

    @property
    def time_in_queue_sec(self) -> float:
        """Time this file spent in queue before processing started."""
        return self.started_at - self.queued_at

    @property
    def processing_time_sec(self) -> float:
        """Time spent processing so far."""
        return time.time() - self.started_at


# Stage weights for progress calculation (cumulative)
STAGE_PROGRESS: Dict[ProcessingStage, int] = {
    ProcessingStage.INIT: 0,
    ProcessingStage.CHUNKING: 5,
    ProcessingStage.FIND_RISKS: 15,
    ProcessingStage.FIND_RISKS_CHECK: 30,
    ProcessingStage.FIND_RISKS_SUMMARIZATION: 45,
    ProcessingStage.FIND_MITIGATIONS: 55,
    ProcessingStage.FIND_MITIGATIONS_CHECK: 75,
    ProcessingStage.FIND_MITIGATIONS_SUMMARIZATION: 95,
}


def get_stage_progress(stage: ProcessingStage) -> int:
    """Get progress percentage for a given stage."""
    return STAGE_PROGRESS.get(stage, 0)


class QueueState:
    """
    Thread-safe state tracker for file processing queue.

    Tracks files waiting in queue and the currently processing file.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queue: Dict[str, QueuedFile] = {}
        self._current: Optional[ProcessingFile] = None

    def update_queue(self, watch_dir: Path) -> None:
        """
        Update queue state from watch directory.

        Args:
            watch_dir: Directory to scan for files.
        """
        with self._lock:
            current_files = set()

            if watch_dir.exists():
                for path in watch_dir.iterdir():
                    if path.is_file():
                        name = path.name
                        current_files.add(name)

                        if name not in self._queue:
                            self._queue[name] = QueuedFile(
                                name=name,
                                size_bytes=path.stat().st_size,
                                queued_at=time.time(),
                            )

            # Remove files no longer in directory
            to_remove = set(self._queue.keys()) - current_files
            for name in to_remove:
                del self._queue[name]

    def start_processing(self, file_path: Path) -> None:
        """
        Mark a file as currently being processed.

        Args:
            file_path: Path to the file being processed.
        """
        with self._lock:
            name = file_path.name
            queued_file = self._queue.pop(name, None)

            queued_at = queued_file.queued_at if queued_file else time.time()
            size_bytes = queued_file.size_bytes if queued_file else file_path.stat().st_size

            self._current = ProcessingFile(
                name=name,
                size_bytes=size_bytes,
                queued_at=queued_at,
                started_at=time.time(),
                stage=ProcessingStage.INIT,
            )

    def update_stage(self, stage: ProcessingStage) -> None:
        """Update the processing stage of current file."""
        with self._lock:
            if self._current:
                self._current.stage = stage

    def finish_processing(self) -> None:
        """Mark current file as finished processing."""
        with self._lock:
            self._current = None

    def get_queue_count(self) -> int:
        """Get number of files in queue."""
        with self._lock:
            return len(self._queue)

    def get_queue_files(self) -> List[QueuedFile]:
        """Get list of queued files."""
        with self._lock:
            return list(self._queue.values())

    def get_current(self) -> Optional[ProcessingFile]:
        """Get currently processing file info."""
        with self._lock:
            return self._current
