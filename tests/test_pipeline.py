"""Tests for pipeline handler."""

import tempfile
from pathlib import Path

import pytest

from file_processor.config import ChunkingConfig
from file_processor.context import get_current_context, set_current_context
from file_processor.handlers.pipeline import PipelineHandler, PipelineResult


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def chunking_config():
    """Create chunking config for tests."""
    return ChunkingConfig(chunk_size=10, overlap=2)


@pytest.fixture
def handler(chunking_config):
    """Create pipeline handler for tests."""
    return PipelineHandler(chunking_config)


class TestPipelineHandler:
    """Tests for PipelineHandler."""

    def test_process_returns_pipeline_result(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """process() should return PipelineResult."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello World!", encoding="utf-8")

        result = handler.process(test_file)

        assert isinstance(result, PipelineResult)

    def test_result_contains_file_name(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """Result should contain the processed file name."""
        test_file = temp_dir / "myfile.txt"
        test_file.write_text("content", encoding="utf-8")

        result = handler.process(test_file)

        assert result.file_name == "myfile.txt"

    def test_result_contains_chunks(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """Result should contain text chunks."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("0123456789ABCDEF", encoding="utf-8")

        result = handler.process(test_file)

        assert result.chunk_count > 0
        assert len(result.chunks) == result.chunk_count

    def test_chunking_respects_config(self, temp_dir: Path):
        """Chunking should use config parameters."""
        config = ChunkingConfig(chunk_size=5, overlap=0)
        handler = PipelineHandler(config)

        test_file = temp_dir / "test.txt"
        test_file.write_text("0123456789", encoding="utf-8")

        result = handler.process(test_file)

        assert result.chunk_count == 2
        assert result.chunks[0] == "01234"
        assert result.chunks[1] == "56789"

    def test_total_chars_is_correct(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """Result should have correct total character count."""
        test_file = temp_dir / "test.txt"
        content = "Test content here"
        test_file.write_text(content, encoding="utf-8")

        result = handler.process(test_file)

        assert result.total_chars == len(content)

    def test_context_is_cleared_after_processing(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """Processing context should be cleared after process()."""
        set_current_context(None)

        test_file = temp_dir / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        handler.process(test_file)

        assert get_current_context() is None

    def test_context_is_cleared_on_error(
        self, handler: PipelineHandler, temp_dir: Path
    ):
        """Context should be cleared even if processing fails."""
        set_current_context(None)

        non_existent = temp_dir / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            handler.process(non_existent)

        assert get_current_context() is None

    def test_empty_file(self, handler: PipelineHandler, temp_dir: Path):
        """Handler should handle empty files."""
        test_file = temp_dir / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        result = handler.process(test_file)

        assert result.chunk_count == 0
        assert result.total_chars == 0
