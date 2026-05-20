"""Memory Safety Agent: deep analysis of memory vulnerabilities via Rust engine."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from orchestrator.agents.base import BaseAgent
from orchestrator.graph.state import AgentState, Severity, Vulnerability

logger = logging.getLogger(__name__)

RUST_ENGINE_BIN = Path(__file__).parent.parent.parent / "memory-engine" / "target" / "release" / "memory-engine"


class MemorySafetyAgent(BaseAgent):
    name = "memory_safety"

    def _execute(self, state: AgentState) -> AgentState:
        if not RUST_ENGINE_BIN.exists():
            logger.warning("memory-engine binary not found at %s — skipping", RUST_ENGINE_BIN)
            return state

        try:
            result = subprocess.run(
                [str(RUST_ENGINE_BIN), "--json", state.repo_root],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error("memory-engine stderr: %s", result.stderr)
                return state

            raw = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            state.errors.append(f"memory_safety: {exc}")
            return state

        findings: list[Vulnerability] = []
        for item in raw.get("findings", []):
            vuln = Vulnerability(
                id=item["id"],
                title=item["title"],
                severity=Severity(item.get("severity", "high")),
                cwe_id=item.get("cwe", "CWE-119"),
                cve_id=item.get("cve"),
                file_path=item["file"],
                line_start=item["line_start"],
                line_end=item["line_end"],
                code_snippet=item.get("snippet", ""),
                description=item["description"],
                memory_safety_issue=True,
            )
            findings.append(vuln)

        state.memory_safety_findings = findings
        logger.info("[memory_safety] found %d memory vulnerabilities", len(findings))
        return state
