"""Tests for processing context."""

from file_processor.context import (
    ProcessingContext,
    ProcessingStage,
    get_current_context,
    set_current_context,
)


class TestProcessingContext:
    """Tests for ProcessingContext."""

    def test_default_values(self):
        """Context should have default UUID and INIT stage."""
        ctx = ProcessingContext()

        assert len(ctx.file_id) == 32  # Full UUID hex
        assert ctx.stage == ProcessingStage.INIT
        assert ctx.file_name is None

    def test_short_id_is_quarter_of_uuid(self):
        """short_id should be first 8 characters (1/4 of 32)."""
        ctx = ProcessingContext()

        assert len(ctx.short_id) == 8
        assert ctx.short_id == ctx.file_id[:8]

    def test_set_stage(self):
        """set_stage should update the stage."""
        ctx = ProcessingContext()

        ctx.set_stage(ProcessingStage.CHUNKING)

        assert ctx.stage == ProcessingStage.CHUNKING

    def test_file_name_stored(self):
        """Context should store file name."""
        ctx = ProcessingContext(file_name="test.txt")

        assert ctx.file_name == "test.txt"


class TestContextVar:
    """Tests for context variable functions."""

    def test_default_context_is_none(self):
        """Default context should be None."""
        set_current_context(None)

        assert get_current_context() is None

    def test_set_and_get_context(self):
        """set_current_context and get_current_context should work."""
        ctx = ProcessingContext(file_name="test.txt")

        set_current_context(ctx)

        assert get_current_context() is ctx
        assert get_current_context().file_name == "test.txt"

    def test_context_can_be_cleared(self):
        """Context can be set back to None."""
        ctx = ProcessingContext()
        set_current_context(ctx)

        set_current_context(None)

        assert get_current_context() is None
