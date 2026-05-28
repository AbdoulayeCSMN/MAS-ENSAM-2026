"""Shared state schema for the multi-agent security workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Language(str, Enum):
    C = "c"
    CPP = "cpp"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    JAVA = "java"
    GO = "go"
    PHP = "php"
    UNKNOWN = "unknown"


@dataclass
class Vulnerability:
    id: str
    title: str
    severity: Severity
    cwe_id: str
    cve_id: str | None
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    description: str
    is_exploitable: bool = False
    exploitability_score: float = 0.0
    cvss_score: float = 0.0
    taint_sources: list[str] = field(default_factory=list)
    taint_sinks: list[str] = field(default_factory=list)
    patch_applied: bool = False
    patch_diff: str | None = None
    memory_safety_issue: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanTarget:
    path: str
    language: Language
    content: str | None = None
    file_hash: str | None = None


@dataclass
class AgentState:
    """Central state passed through the LangGraph workflow."""
    # Input
    targets: list[ScanTarget] = field(default_factory=list)
    repo_root: str = ""
    scan_id: str = ""

    # Routing
    detected_languages: set[Language] = field(default_factory=set)
    needs_memory_safety: bool = False

    # Findings
    raw_findings: list[dict[str, Any]] = field(default_factory=list)
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    memory_safety_findings: list[Vulnerability] = field(default_factory=list)
    semantic_findings: list[Vulnerability] = field(default_factory=list)

    # Patching
    patches_pending: list[Vulnerability] = field(default_factory=list)
    patches_validated: list[Vulnerability] = field(default_factory=list)
    patches_rejected: list[Vulnerability] = field(default_factory=list)

    # Output
    report: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    # Control
    current_agent: str = "triage"
    iteration: int = 0
    max_patch_iterations: int = 3

    def to_dict(self) -> dict:
        """Convertit l'état en dictionnaire pour la sérialisation."""
        return {
            "targets": self.targets,
            "repo_root": self.repo_root,
            "scan_id": self.scan_id,
            "detected_languages": [lang.value for lang in self.detected_languages],
            "needs_memory_safety": self.needs_memory_safety,
            "raw_findings": self.raw_findings,
            "vulnerabilities": self.vulnerabilities,
            "memory_safety_findings": self.memory_safety_findings,
            "semantic_findings": self.semantic_findings,
            "patches_pending": self.patches_pending,
            "patches_validated": self.patches_validated,
            "patches_rejected": self.patches_rejected,
            "report": self.report,
            "errors": self.errors,
            "current_agent": self.current_agent,
            "iteration": self.iteration,
            "max_patch_iterations": self.max_patch_iterations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AgentState:
        """Crée un état à partir d'un dictionnaire."""
        state = cls(
            repo_root=data.get("repo_root", ""),
            scan_id=data.get("scan_id", ""),
            max_patch_iterations=data.get("max_patch_iterations", 3)
        )
        state.targets = data.get("targets", [])
        state.detected_languages = set(
            Language(lang) for lang in data.get("detected_languages", [])
        )
        state.needs_memory_safety = data.get("needs_memory_safety", False)
        state.raw_findings = data.get("raw_findings", [])
        state.vulnerabilities = data.get("vulnerabilities", [])
        state.memory_safety_findings = data.get("memory_safety_findings", [])
        state.semantic_findings = data.get("semantic_findings", [])
        state.patches_pending = data.get("patches_pending", [])
        state.patches_validated = data.get("patches_validated", [])
        state.patches_rejected = data.get("patches_rejected", [])
        state.report = data.get("report", {})
        state.errors = data.get("errors", [])
        state.current_agent = data.get("current_agent", "triage")
        state.iteration = data.get("iteration", 0)
        return state