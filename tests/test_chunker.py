"""Tests for text chunking."""

import pytest

from file_processor.chunker import TextChunker


class TestTextChunker:
    """Tests for TextChunker."""

    def test_simple_chunking(self):
        """Chunker should split text into chunks of specified size."""
        chunker = TextChunker(chunk_size=10, overlap=0)

        result = chunker.chunk("0123456789ABCDEF")

        assert result.chunk_count == 2
        assert result.chunks[0].content == "0123456789"
        assert result.chunks[1].content == "ABCDEF"

    def test_chunking_with_overlap(self):
        """Chunker should create overlapping chunks."""
        chunker = TextChunker(chunk_size=10, overlap=3)

        result = chunker.chunk("0123456789ABCDEFGHIJ")

        # Step = 10 - 3 = 7
        # Chunk 0: 0-10  -> "0123456789"
        # Chunk 1: 7-17  -> "789ABCDEFG"
        # Chunk 2: 14-20 -> "EFGHIJ"
        assert result.chunk_count == 3
        assert result.chunks[0].content == "0123456789"
        assert result.chunks[1].content == "789ABCDEFG"
        assert result.chunks[2].content == "EFGHIJ"

    def test_chunk_positions(self):
        """Chunks should have correct start and end positions."""
        chunker = TextChunker(chunk_size=5, overlap=2)

        result = chunker.chunk("0123456789")

        # Step = 5 - 2 = 3
        assert result.chunks[0].start_pos == 0
        assert result.chunks[0].end_pos == 5
        assert result.chunks[1].start_pos == 3
        assert result.chunks[1].end_pos == 8
        assert result.chunks[2].start_pos == 6
        assert result.chunks[2].end_pos == 10

    def test_empty_text(self):
        """Chunker should handle empty text."""
        chunker = TextChunker(chunk_size=10, overlap=2)

        result = chunker.chunk("")

        assert result.chunk_count == 0
        assert result.total_chars == 0

    def test_text_smaller_than_chunk_size(self):
        """Chunker should handle text smaller than chunk size."""
        chunker = TextChunker(chunk_size=100, overlap=10)

        result = chunker.chunk("small")

        assert result.chunk_count == 1
        assert result.chunks[0].content == "small"

    def test_exact_chunk_size(self):
        """Chunker should handle text exactly matching chunk size."""
        chunker = TextChunker(chunk_size=5, overlap=0)

        result = chunker.chunk("12345")

        assert result.chunk_count == 1
        assert result.chunks[0].content == "12345"

    def test_chunk_metadata(self):
        """ChunkingResult should contain correct metadata."""
        chunker = TextChunker(chunk_size=10, overlap=2)

        result = chunker.chunk("0123456789ABCDEF")

        assert result.total_chars == 16
        assert result.chunk_size == 10
        assert result.overlap == 2

    def test_chunk_index(self):
        """Chunks should have correct sequential indices."""
        chunker = TextChunker(chunk_size=3, overlap=0)

        result = chunker.chunk("123456789")

        for i, chunk in enumerate(result.chunks):
            assert chunk.index == i

    def test_invalid_chunk_size(self):
        """Chunker should reject non-positive chunk size."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            TextChunker(chunk_size=0, overlap=0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            TextChunker(chunk_size=-1, overlap=0)

    def test_invalid_overlap(self):
        """Chunker should reject negative overlap."""
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            TextChunker(chunk_size=10, overlap=-1)

    def test_overlap_greater_than_chunk_size(self):
        """Chunker should reject overlap >= chunk_size."""
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            TextChunker(chunk_size=10, overlap=10)

        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            TextChunker(chunk_size=10, overlap=15)

    def test_step_property(self):
        """Step should be chunk_size - overlap."""
        chunker = TextChunker(chunk_size=100, overlap=20)

        assert chunker.step == 80

    def test_unicode_text(self):
        """Chunker should handle unicode text correctly."""
        chunker = TextChunker(chunk_size=5, overlap=0)

        result = chunker.chunk("привет")

        assert result.chunk_count == 2
        assert result.chunks[0].content == "приве"
        assert result.chunks[1].content == "т"
        assert result.total_chars == 6
