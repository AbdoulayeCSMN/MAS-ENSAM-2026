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
