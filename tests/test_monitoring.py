"""Tests for monitoring API and queue state."""

import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from file_processor.api import create_api
from file_processor.context import ProcessingStage
from file_processor.queue_state import (
    QueueState,
    QueuedFile,
    get_stage_progress,
)


class TestQueueState:
    """Tests for QueueState."""

    def test_initial_state_empty(self):
        """Initial queue should be empty."""
        state = QueueState()

        assert state.get_queue_count() == 0
        assert state.get_queue_files() == []
        assert state.get_current() is None

    def test_update_queue_adds_files(self, tmp_path: Path):
        """update_queue should detect files in directory."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        state = QueueState()
        state.update_queue(tmp_path)

        assert state.get_queue_count() == 2
        files = state.get_queue_files()
        names = [f.name for f in files]
        assert "file1.txt" in names
        assert "file2.txt" in names

    def test_update_queue_removes_missing_files(self, tmp_path: Path):
        """update_queue should remove files no longer present."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")

        state = QueueState()
        state.update_queue(tmp_path)
        assert state.get_queue_count() == 1

        file1.unlink()
        state.update_queue(tmp_path)
        assert state.get_queue_count() == 0

    def test_start_processing_sets_current(self, tmp_path: Path):
        """start_processing should set current file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        state = QueueState()
        state.update_queue(tmp_path)
        state.start_processing(file_path)

        current = state.get_current()
        assert current is not None
        assert current.name == "test.txt"
        assert current.stage == ProcessingStage.INIT

    def test_start_processing_removes_from_queue(self, tmp_path: Path):
        """start_processing should remove file from queue."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        state = QueueState()
        state.update_queue(tmp_path)
        assert state.get_queue_count() == 1

        state.start_processing(file_path)
        assert state.get_queue_count() == 0

    def test_update_stage(self, tmp_path: Path):
        """update_stage should change current file stage."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        state = QueueState()
        state.start_processing(file_path)
        state.update_stage(ProcessingStage.CHUNKING)

        assert state.get_current().stage == ProcessingStage.CHUNKING

    def test_finish_processing_clears_current(self, tmp_path: Path):
        """finish_processing should clear current file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        state = QueueState()
        state.start_processing(file_path)
        state.finish_processing()

        assert state.get_current() is None

    def test_queued_file_time_in_queue(self):
        """QueuedFile should track time in queue."""
        queued = QueuedFile(
            name="test.txt",
            size_bytes=100,
            queued_at=time.time() - 5.0,
        )

        assert queued.time_in_queue_sec >= 5.0

    def test_queue_ignores_subdirectories(self, tmp_path: Path):
        """update_queue should ignore subdirectories."""
        (tmp_path / "file.txt").write_text("content")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested")

        state = QueueState()
        state.update_queue(tmp_path)

        assert state.get_queue_count() == 1
        assert state.get_queue_files()[0].name == "file.txt"


class TestStageProgress:
    """Tests for stage progress calculation."""

    def test_init_stage_is_zero(self):
        """INIT stage should be 0%."""
        assert get_stage_progress(ProcessingStage.INIT) == 0

    def test_chunking_stage_progress(self):
        """CHUNKING stage should have some progress."""
        assert get_stage_progress(ProcessingStage.CHUNKING) == 5

    def test_final_stage_near_complete(self):
        """Final stage should be near 100%."""
        assert get_stage_progress(ProcessingStage.FIND_MITIGATIONS_SUMMARIZATION) == 95

    def test_progress_increases_through_stages(self):
        """Progress should increase through stages."""
        stages = [
            ProcessingStage.INIT,
            ProcessingStage.CHUNKING,
            ProcessingStage.FIND_RISKS,
            ProcessingStage.FIND_RISKS_CHECK,
            ProcessingStage.FIND_RISKS_SUMMARIZATION,
            ProcessingStage.FIND_MITIGATIONS,
            ProcessingStage.FIND_MITIGATIONS_CHECK,
            ProcessingStage.FIND_MITIGATIONS_SUMMARIZATION,
        ]

        prev_progress = -1
        for stage in stages:
            progress = get_stage_progress(stage)
            assert progress > prev_progress
            prev_progress = progress


class TestMonitoringAPI:
    """Tests for monitoring API endpoints."""

    @pytest.fixture
    def queue_state(self):
        """Create queue state for testing."""
        return QueueState()

    @pytest.fixture
    def client(self, queue_state: QueueState):
        """Create test client."""
        app = create_api(queue_state)
        return TestClient(app)

    def test_queue_count_empty(self, client: TestClient):
        """GET /queue/count should return 0 for empty queue."""
        response = client.get("/queue/count")

        assert response.status_code == 200
        assert response.json() == {"count": 0}

    def test_queue_count_with_files(
        self, client: TestClient, queue_state: QueueState, tmp_path: Path
    ):
        """GET /queue/count should return correct count."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        queue_state.update_queue(tmp_path)

        response = client.get("/queue/count")

        assert response.status_code == 200
        assert response.json() == {"count": 2}

    def test_queue_status_empty(self, client: TestClient):
        """GET /queue/status should return empty list."""
        response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["files"] == []

    def test_queue_status_with_files(
        self, client: TestClient, queue_state: QueueState, tmp_path: Path
    ):
        """GET /queue/status should return file details."""
        (tmp_path / "test.txt").write_text("hello world")
        queue_state.update_queue(tmp_path)

        response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["files"]) == 1
        assert data["files"][0]["name"] == "test.txt"
        assert data["files"][0]["size_bytes"] == 11
        assert "time_in_queue_sec" in data["files"][0]

    def test_current_no_file_processing(self, client: TestClient):
        """GET /current should return null when no file processing."""
        response = client.get("/current")

        assert response.status_code == 200
        assert response.json() is None

    def test_current_with_processing_file(
        self, client: TestClient, queue_state: QueueState, tmp_path: Path
    ):
        """GET /current should return processing file info."""
        file_path = tmp_path / "processing.txt"
        file_path.write_text("content being processed")
        queue_state.start_processing(file_path)
        queue_state.update_stage(ProcessingStage.CHUNKING)

        response = client.get("/current")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "processing.txt"
        assert data["stage"] == "CHUNK"
        assert data["progress_percent"] == 5
        assert "time_in_queue_sec" in data
        assert "processing_time_sec" in data
