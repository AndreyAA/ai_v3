"""Tests for File Processor Service."""

import tempfile
from pathlib import Path

import pytest

from file_processor.config import (
    ChunkingConfig,
    Config,
    DirectoriesConfig,
    LoggingConfig,
    ServiceConfig,
)
from file_processor.handlers import CharCounterHandler
from file_processor.service import FileProcessorService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir: Path) -> Config:
    """Create test configuration with temporary directories."""
    return Config(
        directories=DirectoriesConfig(
            watch_dir=temp_dir,
            data_subdir="data",
            processed_subdir="processed",
        ),
        service=ServiceConfig(poll_interval_sec=1),
        logging=LoggingConfig(level="DEBUG", format="%(message)s"),
        chunking=ChunkingConfig(chunk_size=1000, overlap=100),
    )


@pytest.fixture
def service(test_config: Config) -> FileProcessorService:
    """Create service instance for testing."""
    handler = CharCounterHandler()
    return FileProcessorService(test_config, handler)


class TestCharCounterHandler:
    """Tests for CharCounterHandler."""

    def test_counts_characters_correctly(self, temp_dir: Path):
        """Handler should correctly count characters in a file."""
        # Arrange
        test_file = temp_dir / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content, encoding="utf-8")

        handler = CharCounterHandler()

        # Act
        result = handler.process(test_file)

        # Assert
        assert result.file_name == "test.txt"
        assert result.char_count == len(test_content)

    def test_handles_empty_file(self, temp_dir: Path):
        """Handler should handle empty files."""
        # Arrange
        test_file = temp_dir / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        handler = CharCounterHandler()

        # Act
        result = handler.process(test_file)

        # Assert
        assert result.char_count == 0

    def test_handles_unicode(self, temp_dir: Path):
        """Handler should correctly count unicode characters."""
        # Arrange
        test_file = temp_dir / "unicode.txt"
        test_content = "Привет мир"
        test_file.write_text(test_content, encoding="utf-8")

        handler = CharCounterHandler()

        # Act
        result = handler.process(test_file)

        # Assert
        assert result.char_count == len(test_content)


class TestFileProcessorService:
    """Tests for FileProcessorService."""

    def test_run_once_returns_false_when_no_files(self, service: FileProcessorService):
        """run_once should return False when no files in watch directory."""
        # Act
        result = service.run_once()

        # Assert
        assert result is False

    def test_run_once_processes_file(
        self, service: FileProcessorService, test_config: Config
    ):
        """run_once should process a file and return True."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        watch_dir.mkdir(parents=True, exist_ok=True)

        test_file = watch_dir / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content, encoding="utf-8")

        # Act
        result = service.run_once()

        # Assert
        assert result is True

    def test_file_moved_to_processed_after_processing(
        self, service: FileProcessorService, test_config: Config
    ):
        """File should be in processed directory after processing."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        processed_dir = test_config.directories.processed_dir

        test_file = watch_dir / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        # Act
        service.run_once()

        # Assert
        assert not test_file.exists()
        assert (processed_dir / "test.txt").exists()

    def test_original_file_removed_from_watch_dir(
        self, service: FileProcessorService, test_config: Config
    ):
        """Original file should be removed from watch directory."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        test_file = watch_dir / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        # Act
        service.run_once()

        # Assert
        assert not test_file.exists()

    def test_data_dir_is_reset_before_processing(
        self, service: FileProcessorService, test_config: Config
    ):
        """Data directory should be cleared before processing."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        data_dir = test_config.directories.data_dir

        # Create data dir with existing file
        data_dir.mkdir(parents=True, exist_ok=True)
        old_file = data_dir / "old.txt"
        old_file.write_text("old content", encoding="utf-8")

        # Create new file to process
        test_file = watch_dir / "new.txt"
        test_file.write_text("new content", encoding="utf-8")

        # Act
        service.run_once()

        # Assert
        assert not old_file.exists()

    def test_processes_files_in_alphabetical_order(
        self, service: FileProcessorService, test_config: Config
    ):
        """Files should be processed in alphabetical order."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        processed_dir = test_config.directories.processed_dir

        (watch_dir / "c_file.txt").write_text("c", encoding="utf-8")
        (watch_dir / "a_file.txt").write_text("a", encoding="utf-8")
        (watch_dir / "b_file.txt").write_text("b", encoding="utf-8")

        # Act - process first file
        service.run_once()

        # Assert - 'a_file' should be processed first
        assert (processed_dir / "a_file.txt").exists()
        assert not (processed_dir / "b_file.txt").exists()
        assert not (processed_dir / "c_file.txt").exists()

    def test_ignores_subdirectories(
        self, service: FileProcessorService, test_config: Config
    ):
        """Service should not process files in subdirectories."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        subdir = watch_dir / "subdir"
        subdir.mkdir(parents=True)

        # Only create file in subdirectory
        (subdir / "test.txt").write_text("content", encoding="utf-8")

        # Act
        result = service.run_once()

        # Assert
        assert result is False

    def test_multiple_files_processed_sequentially(
        self, service: FileProcessorService, test_config: Config
    ):
        """Multiple run_once calls should process files one by one."""
        # Arrange
        watch_dir = test_config.directories.watch_dir
        processed_dir = test_config.directories.processed_dir

        (watch_dir / "file1.txt").write_text("1", encoding="utf-8")
        (watch_dir / "file2.txt").write_text("2", encoding="utf-8")

        # Act & Assert
        assert service.run_once() is True
        assert (processed_dir / "file1.txt").exists()

        assert service.run_once() is True
        assert (processed_dir / "file2.txt").exists()

        assert service.run_once() is False
