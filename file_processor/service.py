"""File Processor Service - main service logic."""

import logging
import shutil
import time
from pathlib import Path
from typing import List, Optional

from file_processor.config import Config
from file_processor.context import set_global_stage_callback
from file_processor.handlers.base import BaseFileHandler
from file_processor.queue_state import QueueState

logger = logging.getLogger(__name__)


class FileProcessorService:
    """
    Service that monitors a directory and processes files.

    The service:
    1. Checks for files in the watch directory (not subdirectories)
    2. If a file exists, clears and recreates the data directory
    3. Copies the first file to data directory
    4. Processes the file using the configured handler
    5. Moves the processed file to the processed directory
    6. Waits for the configured interval before checking again
    """

    def __init__(
        self,
        config: Config,
        handler: BaseFileHandler,
        queue_state: Optional[QueueState] = None,
    ) -> None:
        """
        Initialize the service.

        Args:
            config: Service configuration.
            handler: File handler to use for processing.
            queue_state: Optional queue state tracker for monitoring.
        """
        self._config = config
        self._handler = handler
        self._running = False
        self._queue_state = queue_state or QueueState()

    @property
    def queue_state(self) -> QueueState:
        """Get queue state for monitoring."""
        return self._queue_state

    @property
    def dirs(self):
        """Shortcut to directories config."""
        return self._config.directories

    def _get_files_in_watch_dir(self) -> List[Path]:
        """
        Get list of files in watch directory (excluding subdirectories).

        Returns:
            List of file paths sorted by name.
        """
        if not self.dirs.watch_dir.exists():
            return []

        files = [
            f for f in self.dirs.watch_dir.iterdir()
            if f.is_file()
        ]
        return sorted(files, key=lambda f: f.name)

    def _reset_data_dir(self) -> None:
        """Delete and recreate the data directory."""
        data_dir = self.dirs.data_dir

        if data_dir.exists():
            logger.debug("Removing data directory: %s", data_dir)
            shutil.rmtree(data_dir)

        logger.debug("Creating data directory: %s", data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_processed_dir(self) -> None:
        """Ensure processed directory exists."""
        self.dirs.processed_dir.mkdir(parents=True, exist_ok=True)

    def _copy_to_data_dir(self, file_path: Path) -> Path:
        """
        Copy file to data directory.

        Args:
            file_path: Source file path.

        Returns:
            Path to the copied file in data directory.
        """
        dest_path = self.dirs.data_dir / file_path.name
        logger.info("Copying %s to %s", file_path.name, self.dirs.data_dir)
        shutil.copy2(file_path, dest_path)
        return dest_path

    def _move_to_processed(self, file_path: Path) -> Path:
        """
        Move file from data directory to processed directory.

        Args:
            file_path: File path in data directory.

        Returns:
            New path in processed directory.
        """
        self._ensure_processed_dir()
        dest_path = self.dirs.processed_dir / file_path.name
        logger.info("Moving %s to %s", file_path.name, self.dirs.processed_dir)
        shutil.move(str(file_path), str(dest_path))
        return dest_path

    def _remove_original(self, file_path: Path) -> None:
        """Remove original file from watch directory."""
        logger.debug("Removing original file: %s", file_path)
        file_path.unlink()

    def process_single_file(self, file_path: Path) -> None:
        """
        Process a single file through the full pipeline.

        Args:
            file_path: Path to file in watch directory.
        """
        logger.info("Starting processing of: %s", file_path.name)

        # Mark file as being processed
        self._queue_state.start_processing(file_path)

        try:
            # Reset data directory
            self._reset_data_dir()

            # Copy file to data directory
            data_file_path = self._copy_to_data_dir(file_path)

            # Process the file
            result = self._handler.process(data_file_path)
            logger.info(
                "Handler %s completed with result: %s",
                self._handler.get_name(),
                result
            )

            # Move to processed
            self._move_to_processed(data_file_path)

            # Remove original from watch directory
            self._remove_original(file_path)

            logger.info("Finished processing: %s", file_path.name)
        finally:
            # Mark processing as finished
            self._queue_state.finish_processing()

    def run_once(self) -> bool:
        """
        Check for files and process one if available.

        Returns:
            True if a file was processed, False otherwise.
        """
        # Update queue state
        self._queue_state.update_queue(self.dirs.watch_dir)

        files = self._get_files_in_watch_dir()

        if not files:
            logger.debug("No files found in watch directory")
            return False

        # Process the first file
        self.process_single_file(files[0])
        return True

    def run(self) -> None:
        """
        Run the service continuously.

        Processes files as they appear, with polling interval between checks.
        """
        self._running = True
        poll_interval = self._config.service.poll_interval_sec

        # Set up stage change callback for monitoring
        set_global_stage_callback(self._queue_state.update_stage)

        logger.info(
            "Starting FileProcessorService (handler: %s, poll interval: %ds)",
            self._handler.get_name(),
            poll_interval
        )
        logger.info("Watching directory: %s", self.dirs.watch_dir.absolute())

        # Ensure watch directory exists
        self.dirs.watch_dir.mkdir(parents=True, exist_ok=True)

        while self._running:
            try:
                # Process all available files
                while self.run_once():
                    pass

                # Wait before next check
                logger.debug("Waiting %d seconds...", poll_interval)
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt, stopping...")
                self.stop()
            except Exception as e:
                logger.exception("Error during processing: %s", e)
                time.sleep(poll_interval)

    def stop(self) -> None:
        """Stop the service."""
        logger.info("Stopping FileProcessorService")
        self._running = False
        set_global_stage_callback(None)
