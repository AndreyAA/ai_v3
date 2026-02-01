"""Data models for threat analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ThreatType(Enum):
    """Supported threat types for analysis."""

    PROMPT_INJECTION = "promptinjection"
    # Future threat types will be added here


class AnalysisStage(Enum):
    """Stages of threat analysis pipeline."""

    FIND_RISKS = "findRisks"
    FIND_RISKS_CHECK = "findRisks_check"
    FIND_RISKS_SUMMARIZATION = "findRisks_summarization"
    FIND_MITIGATIONS = "findMitigations"
    FIND_MITIGATIONS_CHECK = "findMitigations_check"
    FIND_MITIGATIONS_SUMMARIZATION = "findMitigations_summarization"


@dataclass
class RiskFactor:
    """A single identified risk factor."""

    risk_factor: str
    source: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskFactor":
        """Create RiskFactor from dictionary."""
        return cls(
            risk_factor=data.get("riskFactor", ""),
            source=data.get("source", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "riskFactor": self.risk_factor,
            "source": self.source,
        }


@dataclass
class MitigationFactor:
    """A single identified mitigation factor."""

    mitigation_factor: str
    source: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MitigationFactor":
        """Create MitigationFactor from dictionary."""
        return cls(
            mitigation_factor=data.get("mitigationFactor", ""),
            source=data.get("source", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mitigationFactor": self.mitigation_factor,
            "source": self.source,
        }


@dataclass
class AnalysisState:
    """
    State object passed between analysis stages.

    Holds intermediate and final results of the analysis.
    """

    # Final results
    risks: List[RiskFactor] = field(default_factory=list)
    mitigations: List[MitigationFactor] = field(default_factory=list)

    # Intermediate results per chunk
    chunk_risks: List[List[RiskFactor]] = field(default_factory=list)
    chunk_mitigations: List[List[MitigationFactor]] = field(default_factory=list)

    # Metadata
    threat_type: Optional[ThreatType] = None
    current_stage: Optional[AnalysisStage] = None
    current_chunk_index: int = 0
    total_chunks: int = 0

    # Custom data storage
    extra: Dict[str, Any] = field(default_factory=dict)

    def add_chunk_risks(self, risks: List[RiskFactor]) -> None:
        """Add risks from a processed chunk."""
        self.chunk_risks.append(risks)

    def add_chunk_mitigations(self, mitigations: List[MitigationFactor]) -> None:
        """Add mitigations from a processed chunk."""
        self.chunk_mitigations.append(mitigations)

    def get_all_chunk_risks(self) -> List[RiskFactor]:
        """Get flattened list of all chunk risks."""
        return [risk for chunk in self.chunk_risks for risk in chunk]

    def get_all_chunk_mitigations(self) -> List[MitigationFactor]:
        """Get flattened list of all chunk mitigations."""
        return [mit for chunk in self.chunk_mitigations for mit in chunk]
