"""OpenAI-compatible LLM client implementation."""

import logging
import os

from openai import OpenAI

from llm.base import BaseLLMClient, LLMError

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """
    LLM client using OpenAI API.

    Reads configuration from environment variables:
    - OPENAI_API_KEY: API key (required)
    - OPENAI_MODEL: Model name (default: gpt-4o-mini)
    - OPENAI_BASE_URL: Base URL for API (optional, for compatible providers)
    """

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self) -> None:
        """Initialize the OpenAI client."""
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self._model = os.environ.get("OPENAI_MODEL", self.DEFAULT_MODEL)

        logger.debug("Initialized OpenAI client with model: %s", self._model)

    def complete(self, system: str, user_message: str) -> str:
        """
        Send a completion request to OpenAI.

        Args:
            system: System prompt that sets the behavior of the assistant.
            user_message: User message to send to the LLM.

        Returns:
            The LLM's response as a string.

        Raises:
            LLMError: If the request fails.
        """
        try:
            logger.debug("Sending completion request to %s", self._model)

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
            )

            result = response.choices[0].message.content
            logger.debug("Received response: %d characters", len(result or ""))

            return result or ""

        except Exception as e:
            logger.error("LLM request failed: %s", e)
            raise LLMError(f"Failed to complete request: {e}") from e
