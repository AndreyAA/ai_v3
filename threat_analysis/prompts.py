"""Prompt loading and rendering utilities."""

import logging
from pathlib import Path
from typing import Dict, Optional

from threat_analysis.models import AnalysisStage, ThreatType

logger = logging.getLogger(__name__)

# Default prompts directory relative to project root
DEFAULT_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptLoader:
    """
    Loads and renders prompt templates for threat analysis.

    Prompts are organized by threat type and stage:
    prompts/{threat_type}/{stage}.md
    """

    def __init__(self, prompts_dir: Optional[Path] = None) -> None:
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompts. Uses default if None.
        """
        self._prompts_dir = prompts_dir or DEFAULT_PROMPTS_DIR
        self._cache: Dict[str, str] = {}

    def _get_prompt_path(self, threat_type: ThreatType, stage: AnalysisStage) -> Path:
        """Get path to prompt file."""
        # Stage value is like "findRisks" or "findRisks_check"
        filename = f"{stage.value}.md"
        return self._prompts_dir / threat_type.value / filename

    def _load_prompt(self, threat_type: ThreatType, stage: AnalysisStage) -> str:
        """
        Load prompt template from file.

        Args:
            threat_type: Type of threat being analyzed.
            stage: Analysis stage.

        Returns:
            Prompt template string.

        Raises:
            FileNotFoundError: If prompt file doesn't exist.
        """
        cache_key = f"{threat_type.value}:{stage.value}"

        if cache_key not in self._cache:
            path = self._get_prompt_path(threat_type, stage)
            logger.debug("Loading prompt from: %s", path)

            self._cache[cache_key] = path.read_text(encoding="utf-8")

        return self._cache[cache_key]

    def render(
        self,
        threat_type: ThreatType,
        stage: AnalysisStage,
        variables: Dict[str, str],
    ) -> str:
        """
        Load and render a prompt template with variables.

        Args:
            threat_type: Type of threat being analyzed.
            stage: Analysis stage.
            variables: Variables to substitute in template.
                       Use {{variable_name}} syntax in templates.

        Returns:
            Rendered prompt string.
        """
        template = self._load_prompt(threat_type, stage)

        # Simple variable substitution
        result = template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, value)

        return result

    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._cache.clear()
