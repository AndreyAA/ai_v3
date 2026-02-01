"""Monitoring API for file processor service."""

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from file_processor.queue_state import QueueState, get_stage_progress


class QueueCountResponse(BaseModel):
    """Response for queue count endpoint."""

    count: int


class QueueFileInfo(BaseModel):
    """Information about a queued file."""

    name: str
    size_bytes: int
    time_in_queue_sec: float


class QueueStatusResponse(BaseModel):
    """Response for queue status endpoint."""

    count: int
    files: List[QueueFileInfo]


class CurrentFileResponse(BaseModel):
    """Response for current file endpoint."""

    name: str
    size_bytes: int
    time_in_queue_sec: float
    processing_time_sec: float
    stage: str
    progress_percent: int


def create_api(queue_state: QueueState) -> FastAPI:
    """
    Create FastAPI application for monitoring.

    Args:
        queue_state: Queue state tracker to monitor.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="File Processor Monitor",
        description="API for monitoring file processing queue",
        version="1.0.0",
    )

    @app.get("/queue/count", response_model=QueueCountResponse)
    def get_queue_count() -> QueueCountResponse:
        """Get number of files waiting in queue."""
        return QueueCountResponse(count=queue_state.get_queue_count())

    @app.get("/queue/status", response_model=QueueStatusResponse)
    def get_queue_status() -> QueueStatusResponse:
        """Get detailed status of all queued files."""
        files = queue_state.get_queue_files()
        return QueueStatusResponse(
            count=len(files),
            files=[
                QueueFileInfo(
                    name=f.name,
                    size_bytes=f.size_bytes,
                    time_in_queue_sec=round(f.time_in_queue_sec, 2),
                )
                for f in files
            ],
        )

    @app.get("/current", response_model=Optional[CurrentFileResponse])
    def get_current() -> Optional[CurrentFileResponse]:
        """Get information about currently processing file."""
        current = queue_state.get_current()

        if current is None:
            return None

        return CurrentFileResponse(
            name=current.name,
            size_bytes=current.size_bytes,
            time_in_queue_sec=round(current.time_in_queue_sec, 2),
            processing_time_sec=round(current.processing_time_sec, 2),
            stage=current.stage.value,
            progress_percent=get_stage_progress(current.stage),
        )

    return app
