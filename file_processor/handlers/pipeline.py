"""Pipeline handler for multi-stage file processing."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from file_processor.chunker import ChunkingResult, TextChunker
from file_processor.config import ChunkingConfig
from file_processor.context import (
    ProcessingContext,
    ProcessingStage,
    get_current_context,
    set_current_context,
)
from file_processor.handlers.base import BaseFileHandler
from file_processor.logging_utils import log_timing

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    file_name: str
    chunks: List[str]
    chunk_count: int
    total_chars: int


class PipelineHandler(BaseFileHandler):
    """
    Multi-stage file processing handler.

    Processes files through a pipeline of stages:
    1. CHUNKING - Split file into overlapping chunks
    2. (Future stages will be added)
    """

    def __init__(self, chunking_config: ChunkingConfig) -> None:
        """
        Initialize pipeline handler.

        Args:
            chunking_config: Configuration for text chunking.
        """
        self._chunker = TextChunker(
            chunk_size=chunking_config.chunk_size,
            overlap=chunking_config.overlap,
        )

    def process(self, file_path: Path) -> PipelineResult:
        """
        Process file through the pipeline.

        Args:
            file_path: Path to the file to process.

        Returns:
            PipelineResult with processing results.
        """
        # Create processing context
        ctx = ProcessingContext(file_name=file_path.name)
        set_current_context(ctx)

        logger.info("Starting pipeline for file: %s", file_path.name)

        try:
            with log_timing(logger, "Full pipeline"):
                # Stage 1: Chunking
                chunking_result = self._stage_chunking(file_path)

                # Future stages will be added here

            logger.info(
                "Pipeline completed: %d chunks from %d chars",
                chunking_result.chunk_count,
                chunking_result.total_chars,
            )

            return PipelineResult(
                file_name=file_path.name,
                chunks=[c.content for c in chunking_result.chunks],
                chunk_count=chunking_result.chunk_count,
                total_chars=chunking_result.total_chars,
            )

        finally:
            set_current_context(None)

    def _stage_chunking(self, file_path: Path) -> ChunkingResult:
        """Execute chunking stage."""
        ctx = get_current_context()
        if ctx:
            ctx.set_stage(ProcessingStage.CHUNKING)

        # Read file content
        content = file_path.read_text(encoding="utf-8")
        logger.info("Read file: %d characters", len(content))

        # Chunk the content
        return self._chunker.chunk(content)
