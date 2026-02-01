"""Tests for threat analysis module."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from threat_analysis import (
    AnalysisStage,
    AnalysisState,
    MitigationFactor,
    PromptLoader,
    RiskFactor,
    ThreatAnalyzer,
    ThreatType,
)


class TestRiskFactor:
    """Tests for RiskFactor model."""

    def test_from_dict(self):
        """Should create RiskFactor from dictionary."""
        data = {
            "riskFactor": "SQL injection vulnerability",
            "source": ["line 42", "line 55"],
        }

        risk = RiskFactor.from_dict(data)

        assert risk.risk_factor == "SQL injection vulnerability"
        assert risk.source == ["line 42", "line 55"]

    def test_to_dict(self):
        """Should convert to dictionary."""
        risk = RiskFactor(
            risk_factor="XSS vulnerability",
            source=["script.js:10"],
        )

        result = risk.to_dict()

        assert result["riskFactor"] == "XSS vulnerability"
        assert result["source"] == ["script.js:10"]


class TestMitigationFactor:
    """Tests for MitigationFactor model."""

    def test_from_dict(self):
        """Should create MitigationFactor from dictionary."""
        data = {
            "mitigationFactor": "Input sanitization",
            "source": ["utils.py:100"],
        }

        mitigation = MitigationFactor.from_dict(data)

        assert mitigation.mitigation_factor == "Input sanitization"
        assert mitigation.source == ["utils.py:100"]

    def test_to_dict(self):
        """Should convert to dictionary."""
        mitigation = MitigationFactor(
            mitigation_factor="Rate limiting",
            source=["api.py:50"],
        )

        result = mitigation.to_dict()

        assert result["mitigationFactor"] == "Rate limiting"
        assert result["source"] == ["api.py:50"]


class TestAnalysisState:
    """Tests for AnalysisState."""

    def test_add_chunk_risks(self):
        """Should accumulate chunk risks."""
        state = AnalysisState()
        risks1 = [RiskFactor("risk1", ["src1"])]
        risks2 = [RiskFactor("risk2", ["src2"])]

        state.add_chunk_risks(risks1)
        state.add_chunk_risks(risks2)

        assert len(state.chunk_risks) == 2

    def test_get_all_chunk_risks(self):
        """Should flatten all chunk risks."""
        state = AnalysisState()
        state.add_chunk_risks([RiskFactor("risk1", ["src1"])])
        state.add_chunk_risks([RiskFactor("risk2", ["src2"]), RiskFactor("risk3", ["src3"])])

        all_risks = state.get_all_chunk_risks()

        assert len(all_risks) == 3

    def test_add_chunk_mitigations(self):
        """Should accumulate chunk mitigations."""
        state = AnalysisState()
        mit1 = [MitigationFactor("mit1", ["src1"])]
        mit2 = [MitigationFactor("mit2", ["src2"])]

        state.add_chunk_mitigations(mit1)
        state.add_chunk_mitigations(mit2)

        assert len(state.chunk_mitigations) == 2

    def test_get_all_chunk_mitigations(self):
        """Should flatten all chunk mitigations."""
        state = AnalysisState()
        state.add_chunk_mitigations([MitigationFactor("mit1", ["src1"])])
        state.add_chunk_mitigations([MitigationFactor("mit2", ["src2"])])

        all_mitigations = state.get_all_chunk_mitigations()

        assert len(all_mitigations) == 2


class TestPromptLoader:
    """Tests for PromptLoader."""

    def test_load_and_render_prompt(self, tmp_path: Path):
        """Should load and render prompt template."""
        # Create test prompt
        prompts_dir = tmp_path / "prompts" / "promptinjection"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "findRisks.md").write_text(
            "Analyze this: {{chunk}}", encoding="utf-8"
        )

        loader = PromptLoader(tmp_path / "prompts")

        result = loader.render(
            ThreatType.PROMPT_INJECTION,
            AnalysisStage.FIND_RISKS,
            {"chunk": "test code"},
        )

        assert result == "Analyze this: test code"

    def test_cache_prompt(self, tmp_path: Path):
        """Should cache loaded prompts."""
        prompts_dir = tmp_path / "prompts" / "promptinjection"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "findRisks.md").write_text("Template", encoding="utf-8")

        loader = PromptLoader(tmp_path / "prompts")

        # Load twice
        loader.render(ThreatType.PROMPT_INJECTION, AnalysisStage.FIND_RISKS, {})
        loader.render(ThreatType.PROMPT_INJECTION, AnalysisStage.FIND_RISKS, {})

        # Should be cached
        assert len(loader._cache) == 1

    def test_clear_cache(self, tmp_path: Path):
        """Should clear prompt cache."""
        prompts_dir = tmp_path / "prompts" / "promptinjection"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "findRisks.md").write_text("Template", encoding="utf-8")

        loader = PromptLoader(tmp_path / "prompts")
        loader.render(ThreatType.PROMPT_INJECTION, AnalysisStage.FIND_RISKS, {})

        loader.clear_cache()

        assert len(loader._cache) == 0


class TestThreatAnalyzer:
    """Tests for ThreatAnalyzer."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        return MagicMock()

    @pytest.fixture
    def prompt_loader(self, tmp_path: Path):
        """Create prompt loader with test prompts."""
        prompts_dir = tmp_path / "prompts" / "promptinjection"
        prompts_dir.mkdir(parents=True)

        # Create all required prompts
        for stage in AnalysisStage:
            (prompts_dir / f"{stage.value}.md").write_text(
                f"{{{{chunk}}}}{{{{previous_result}}}}{{{{all_risks}}}}{{{{all_mitigations}}}}",
                encoding="utf-8",
            )

        return PromptLoader(tmp_path / "prompts")

    @pytest.fixture
    def sample_risks_response(self):
        """Sample LLM response with multiple risks."""
        return json.dumps([
            {
                "riskFactor": "User input directly concatenated into prompt without sanitization",
                "source": ["api/chat.py:45", "api/chat.py:67"]
            },
            {
                "riskFactor": "No input validation before LLM call",
                "source": ["services/llm_service.py:23"]
            },
            {
                "riskFactor": "System prompt can be overridden by user input",
                "source": ["handlers/completion.py:89", "handlers/completion.py:112"]
            }
        ])

    @pytest.fixture
    def sample_mitigations_response(self):
        """Sample LLM response with multiple mitigations."""
        return json.dumps([
            {
                "mitigationFactor": "Input sanitization function removes special characters",
                "source": ["utils/sanitize.py:12", "utils/sanitize.py:34"]
            },
            {
                "mitigationFactor": "Rate limiting prevents abuse",
                "source": ["middleware/rate_limit.py:56"]
            },
            {
                "mitigationFactor": "Content filtering blocks malicious patterns",
                "source": ["filters/content_filter.py:78", "filters/content_filter.py:92"]
            }
        ])

    def test_analyze_finds_risks(self, mock_llm, prompt_loader, sample_risks_response):
        """Should process chunks and find multiple risks."""
        mock_llm.complete.return_value = sample_risks_response

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1", "chunk2"],
            threat_type=ThreatType.PROMPT_INJECTION,
        )

        assert len(state.risks) == 3
        assert state.risks[0].risk_factor == "User input directly concatenated into prompt without sanitization"
        assert len(state.risks[0].source) == 2
        assert state.threat_type == ThreatType.PROMPT_INJECTION

    def test_analyze_finds_mitigations(self, mock_llm, prompt_loader, sample_mitigations_response):
        """Should process chunks and find multiple mitigations."""
        mock_llm.complete.return_value = sample_mitigations_response

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1"],
            threat_type=ThreatType.PROMPT_INJECTION,
        )

        assert len(state.mitigations) == 3
        assert state.mitigations[0].mitigation_factor == "Input sanitization function removes special characters"
        assert len(state.mitigations[1].source) == 1

    def test_analyze_handles_empty_response(self, mock_llm, prompt_loader):
        """Should handle empty LLM responses."""
        mock_llm.complete.return_value = "[]"

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1"],
            threat_type=ThreatType.PROMPT_INJECTION,
        )

        assert state.risks == []
        assert state.mitigations == []

    def test_analyze_handles_invalid_json(self, mock_llm, prompt_loader):
        """Should handle invalid JSON responses gracefully."""
        mock_llm.complete.return_value = "not valid json"

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1"],
            threat_type=ThreatType.PROMPT_INJECTION,
        )

        # Should not crash, just return empty
        assert state.risks == []
        assert state.mitigations == []

    def test_analyze_continues_existing_state(self, mock_llm, prompt_loader):
        """Should continue from existing state."""
        mock_llm.complete.return_value = "[]"

        existing_state = AnalysisState()
        existing_state.extra["custom"] = "value"

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1"],
            threat_type=ThreatType.PROMPT_INJECTION,
            state=existing_state,
        )

        assert state.extra["custom"] == "value"

    def test_analyze_sets_total_chunks(self, mock_llm, prompt_loader):
        """Should set total chunks in state."""
        mock_llm.complete.return_value = "[]"

        analyzer = ThreatAnalyzer(mock_llm, prompt_loader)

        state = analyzer.analyze(
            chunks=["chunk1", "chunk2", "chunk3"],
            threat_type=ThreatType.PROMPT_INJECTION,
        )

        assert state.total_chunks == 3
