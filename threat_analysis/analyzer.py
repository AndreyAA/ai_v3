"""Threat analyzer for processing chunks through LLM analysis stages."""

import json
import logging
from typing import List

from file_processor.context import ProcessingStage, get_current_context
from file_processor.logging_utils import log_timing
from llm.base import BaseLLMClient
from threat_analysis.models import (
    AnalysisStage,
    AnalysisState,
    MitigationFactor,
    RiskFactor,
    ThreatType,
)
from threat_analysis.prompts import PromptLoader

logger = logging.getLogger(__name__)

# System prompt for JSON responses
SYSTEM_PROMPT = """You are a security analyst specialized in identifying vulnerabilities and security measures in code and documentation.
Always respond with valid JSON arrays as specified in the prompt.
Do not include any text outside the JSON response."""


class ThreatAnalyzer:
    """
    Analyzes text chunks for security threats using LLM.

    Processes chunks through a pipeline of stages:
    1. findRisks - identify risks in each chunk
    2. findRisks_check - verify identified risks
    3. findRisks_summarization - consolidate all risks
    4. findMitigations - identify mitigations in each chunk
    5. findMitigations_check - verify identified mitigations
    6. findMitigations_summarization - consolidate all mitigations
    """

    def __init__(
        self,
        llm_client: BaseLLMClient,
        prompt_loader: PromptLoader,
    ) -> None:
        """
        Initialize threat analyzer.

        Args:
            llm_client: LLM client for API calls.
            prompt_loader: Loader for prompt templates.
        """
        self._llm = llm_client
        self._prompts = prompt_loader

    def _update_processing_stage(self, stage: AnalysisStage) -> None:
        """Update the processing context stage for logging."""
        ctx = get_current_context()
        if ctx:
            # Map analysis stage to processing stage
            stage_map = {
                AnalysisStage.FIND_RISKS: ProcessingStage.FIND_RISKS,
                AnalysisStage.FIND_RISKS_CHECK: ProcessingStage.FIND_RISKS_CHECK,
                AnalysisStage.FIND_RISKS_SUMMARIZATION: ProcessingStage.FIND_RISKS_SUMMARIZATION,
                AnalysisStage.FIND_MITIGATIONS: ProcessingStage.FIND_MITIGATIONS,
                AnalysisStage.FIND_MITIGATIONS_CHECK: ProcessingStage.FIND_MITIGATIONS_CHECK,
                AnalysisStage.FIND_MITIGATIONS_SUMMARIZATION: ProcessingStage.FIND_MITIGATIONS_SUMMARIZATION,
            }
            if stage in stage_map:
                ctx.set_stage(stage_map[stage])

    def _parse_risks(self, response: str) -> List[RiskFactor]:
        """Parse LLM response into RiskFactor list."""
        try:
            data = json.loads(response)
            return [RiskFactor.from_dict(item) for item in data]
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse risks JSON: %s", e)
            return []

    def _parse_mitigations(self, response: str) -> List[MitigationFactor]:
        """Parse LLM response into MitigationFactor list."""
        try:
            data = json.loads(response)
            return [MitigationFactor.from_dict(item) for item in data]
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse mitigations JSON: %s", e)
            return []

    def _call_llm(
        self,
        threat_type: ThreatType,
        stage: AnalysisStage,
        variables: dict,
    ) -> str:
        """Call LLM with rendered prompt."""
        prompt = self._prompts.render(threat_type, stage, variables)
        return self._llm.complete(SYSTEM_PROMPT, prompt)

    def _process_chunk_risks(
        self,
        chunk: str,
        chunk_index: int,
        threat_type: ThreatType,
    ) -> List[RiskFactor]:
        """Process a single chunk for risks (findRisks -> findRisks_check)."""
        # Stage 1: Find risks
        self._update_processing_stage(AnalysisStage.FIND_RISKS)
        with log_timing(logger, f"findRisks chunk {chunk_index}"):
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_RISKS,
                {"chunk": chunk},
            )
            initial_risks = self._parse_risks(response)

        logger.info("Chunk %d: found %d initial risks", chunk_index, len(initial_risks))

        if not initial_risks:
            return []

        # Stage 2: Verify risks
        self._update_processing_stage(AnalysisStage.FIND_RISKS_CHECK)
        with log_timing(logger, f"findRisks_check chunk {chunk_index}"):
            previous_result = json.dumps([r.to_dict() for r in initial_risks])
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_RISKS_CHECK,
                {"chunk": chunk, "previous_result": previous_result},
            )
            verified_risks = self._parse_risks(response)

        logger.info("Chunk %d: %d verified risks", chunk_index, len(verified_risks))
        return verified_risks

    def _process_chunk_mitigations(
        self,
        chunk: str,
        chunk_index: int,
        threat_type: ThreatType,
    ) -> List[MitigationFactor]:
        """Process a single chunk for mitigations (findMitigations -> findMitigations_check)."""
        # Stage 1: Find mitigations
        self._update_processing_stage(AnalysisStage.FIND_MITIGATIONS)
        with log_timing(logger, f"findMitigations chunk {chunk_index}"):
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_MITIGATIONS,
                {"chunk": chunk},
            )
            initial_mitigations = self._parse_mitigations(response)

        logger.info(
            "Chunk %d: found %d initial mitigations",
            chunk_index,
            len(initial_mitigations),
        )

        if not initial_mitigations:
            return []

        # Stage 2: Verify mitigations
        self._update_processing_stage(AnalysisStage.FIND_MITIGATIONS_CHECK)
        with log_timing(logger, f"findMitigations_check chunk {chunk_index}"):
            previous_result = json.dumps([m.to_dict() for m in initial_mitigations])
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_MITIGATIONS_CHECK,
                {"chunk": chunk, "previous_result": previous_result},
            )
            verified_mitigations = self._parse_mitigations(response)

        logger.info(
            "Chunk %d: %d verified mitigations",
            chunk_index,
            len(verified_mitigations),
        )
        return verified_mitigations

    def _summarize_risks(
        self,
        state: AnalysisState,
        threat_type: ThreatType,
    ) -> List[RiskFactor]:
        """Summarize all chunk risks into final list."""
        all_risks = state.get_all_chunk_risks()

        if not all_risks:
            logger.info("No risks to summarize")
            return []

        self._update_processing_stage(AnalysisStage.FIND_RISKS_SUMMARIZATION)
        with log_timing(logger, "findRisks_summarization"):
            all_risks_json = json.dumps([r.to_dict() for r in all_risks])
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_RISKS_SUMMARIZATION,
                {"all_risks": all_risks_json},
            )
            summarized = self._parse_risks(response)

        logger.info("Summarized %d risks into %d", len(all_risks), len(summarized))
        return summarized

    def _summarize_mitigations(
        self,
        state: AnalysisState,
        threat_type: ThreatType,
    ) -> List[MitigationFactor]:
        """Summarize all chunk mitigations into final list."""
        all_mitigations = state.get_all_chunk_mitigations()

        if not all_mitigations:
            logger.info("No mitigations to summarize")
            return []

        self._update_processing_stage(AnalysisStage.FIND_MITIGATIONS_SUMMARIZATION)
        with log_timing(logger, "findMitigations_summarization"):
            all_mitigations_json = json.dumps([m.to_dict() for m in all_mitigations])
            response = self._call_llm(
                threat_type,
                AnalysisStage.FIND_MITIGATIONS_SUMMARIZATION,
                {"all_mitigations": all_mitigations_json},
            )
            summarized = self._parse_mitigations(response)

        logger.info(
            "Summarized %d mitigations into %d",
            len(all_mitigations),
            len(summarized),
        )
        return summarized

    def analyze(
        self,
        chunks: List[str],
        threat_type: ThreatType,
        state: AnalysisState | None = None,
    ) -> AnalysisState:
        """
        Analyze chunks for a specific threat type.

        Args:
            chunks: Text chunks to analyze.
            threat_type: Type of threat to analyze for.
            state: Optional existing state to continue from.

        Returns:
            AnalysisState with risks and mitigations.
        """
        if state is None:
            state = AnalysisState()

        state.threat_type = threat_type
        state.total_chunks = len(chunks)

        logger.info(
            "Starting %s analysis for %d chunks",
            threat_type.value,
            len(chunks),
        )

        # Process each chunk for risks
        for i, chunk in enumerate(chunks):
            state.current_chunk_index = i
            chunk_risks = self._process_chunk_risks(chunk, i, threat_type)
            state.add_chunk_risks(chunk_risks)

        # Summarize risks
        state.risks = self._summarize_risks(state, threat_type)

        # Process each chunk for mitigations
        for i, chunk in enumerate(chunks):
            state.current_chunk_index = i
            chunk_mitigations = self._process_chunk_mitigations(chunk, i, threat_type)
            state.add_chunk_mitigations(chunk_mitigations)

        # Summarize mitigations
        state.mitigations = self._summarize_mitigations(state, threat_type)

        logger.info(
            "Analysis complete: %d risks, %d mitigations",
            len(state.risks),
            len(state.mitigations),
        )

        return state
