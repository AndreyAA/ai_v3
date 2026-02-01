"""Text chunking utilities."""

import logging
from dataclasses import dataclass
from typing import List

from file_processor.logging_utils import timed

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A single text chunk with metadata."""

    index: int
    content: str
    start_pos: int
    end_pos: int

    @property
    def length(self) -> int:
        """Character count in the chunk."""
        return len(self.content)


@dataclass
class ChunkingResult:
    """Result of chunking operation."""

    chunks: List[Chunk]
    total_chars: int
    chunk_size: int
    overlap: int

    @property
    def chunk_count(self) -> int:
        """Number of chunks produced."""
        return len(self.chunks)


class TextChunker:
    """
    Splits text into overlapping chunks.

    Args:
        chunk_size: Maximum characters per chunk.
        overlap: Number of overlapping characters between adjacent chunks.
    """

    def __init__(self, chunk_size: int, overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")

        self._chunk_size = chunk_size
        self._overlap = overlap

    @property
    def chunk_size(self) -> int:
        """Maximum chunk size in characters."""
        return self._chunk_size

    @property
    def overlap(self) -> int:
        """Overlap size in characters."""
        return self._overlap

    @property
    def step(self) -> int:
        """Step size between chunk starts."""
        return self._chunk_size - self._overlap

    @timed(logger, "Chunking text")
    def chunk(self, text: str) -> ChunkingResult:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to split.

        Returns:
            ChunkingResult with list of chunks and metadata.
        """
        if not text:
            return ChunkingResult(
                chunks=[],
                total_chars=0,
                chunk_size=self._chunk_size,
                overlap=self._overlap,
            )

        chunks: List[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            content = text[start:end]

            chunk = Chunk(
                index=index,
                content=content,
                start_pos=start,
                end_pos=end,
            )
            chunks.append(chunk)

            logger.debug(
                "Created chunk %d: pos %d-%d, %d chars",
                index,
                start,
                end,
                len(content),
            )

            start += self.step
            index += 1

        logger.info(
            "Chunked %d chars into %d chunks (size=%d, overlap=%d)",
            len(text),
            len(chunks),
            self._chunk_size,
            self._overlap,
        )

        return ChunkingResult(
            chunks=chunks,
            total_chars=len(text),
            chunk_size=self._chunk_size,
            overlap=self._overlap,
        )
