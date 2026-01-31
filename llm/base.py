"""Base LLM client abstraction."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Provides a unified interface for interacting with different LLM providers.
    """

    @abstractmethod
    def complete(self, system: str, user_message: str) -> str:
        """
        Send a completion request to the LLM.

        Args:
            system: System prompt that sets the behavior of the assistant.
            user_message: User message to send to the LLM.

        Returns:
            The LLM's response as a string.

        Raises:
            LLMError: If the request fails.
        """
        pass


class LLMError(Exception):
    """Base exception for LLM client errors."""

    pass
