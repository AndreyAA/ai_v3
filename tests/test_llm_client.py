"""Tests for LLM client."""

from unittest.mock import MagicMock, patch

import pytest

from llm import BaseLLMClient, LLMError, OpenAIClient


class TestBaseLLMClient:
    """Tests for BaseLLMClient abstraction."""

    def test_cannot_instantiate_directly(self):
        """BaseLLMClient should not be instantiable."""
        with pytest.raises(TypeError):
            BaseLLMClient()

    def test_subclass_must_implement_complete(self):
        """Subclasses must implement complete method."""

        class IncompleteClient(BaseLLMClient):
            pass

        with pytest.raises(TypeError):
            IncompleteClient()


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    @patch("llm.openai_client.OpenAI")
    def test_complete_returns_response(self, mock_openai_class):
        """complete() should return the LLM response."""
        # Arrange
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()

        # Act
        result = client.complete("You are helpful.", "Say hello")

        # Assert
        assert result == "Hello, world!"

    @patch("llm.openai_client.OpenAI")
    def test_complete_sends_correct_messages(self, mock_openai_class):
        """complete() should send system and user messages correctly."""
        # Arrange
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()

        # Act
        client.complete("system prompt", "user message")

        # Assert
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args

        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "system prompt"}
        assert messages[1] == {"role": "user", "content": "user message"}

    @patch("llm.openai_client.OpenAI")
    def test_complete_raises_llm_error_on_failure(self, mock_openai_class):
        """complete() should raise LLMError when API call fails."""
        # Arrange
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        client = OpenAIClient()

        # Act & Assert
        with pytest.raises(LLMError) as exc_info:
            client.complete("system", "user")

        assert "API error" in str(exc_info.value)

    @patch("llm.openai_client.OpenAI")
    def test_complete_handles_empty_response(self, mock_openai_class):
        """complete() should handle None response content."""
        # Arrange
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()

        # Act
        result = client.complete("system", "user")

        # Assert
        assert result == ""

    @patch.dict("os.environ", {"OPENAI_MODEL": "gpt-4"})
    @patch("llm.openai_client.OpenAI")
    def test_uses_model_from_env(self, mock_openai_class):
        """Client should use model from OPENAI_MODEL env variable."""
        # Arrange
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "response"
        mock_client.chat.completions.create.return_value = mock_response

        client = OpenAIClient()

        # Act
        client.complete("system", "user")

        # Assert
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
