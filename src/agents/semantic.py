"""Semantic Analyst Agent: LLM + RAG for logic flaws and context-aware vulnerabilities."""

from __future__ import annotations

import json
import logging
import uuid

from orchestrator.agents.base import BaseAgent
from orchestrator.graph.state import AgentState, Severity, Vulnerability
from orchestrator.llm.client import LLMClient
from orchestrator.memory.persistent import PersistentMemory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an expert security code reviewer. Analyze the provided code for:
- Logic vulnerabilities (auth bypass, IDOR, business logic flaws)
- Injection flaws (SQL, command, LDAP, XPath, template injection)
- Cryptographic weaknesses (weak algorithms, hardcoded keys, improper IV)
- Insecure deserialization
- Race conditions and TOCTOU vulnerabilities
- Information disclosure

For each finding, respond with a JSON array of objects with keys:
title, severity (critical/high/medium/low), cwe_id, description, line_start, line_end, code_snippet.
Return ONLY valid JSON."""


class SemanticAnalystAgent(BaseAgent):
    name = "semantic_analyst"

    def __init__(self) -> None:
        self._llm = LLMClient()
        self._memory = PersistentMemory()

    def _execute(self, state: AgentState) -> AgentState:
        findings: list[Vulnerability] = []

        # Prioritize files flagged by static scanners for deeper analysis
        flagged_paths = {f.get("file") for f in state.raw_findings}
        priority_targets = [t for t in state.targets if t.path in flagged_paths]
        # Also include all targets if no static findings yet
        if not priority_targets:
            priority_targets = state.targets[:20]  # cap at 20 to control cost

        similar_patterns = self._memory.retrieve_similar_patterns(
            [t.content or "" for t in priority_targets[:3]]
        )

        for target in priority_targets:
            if not target.content:
                continue

            context = _build_context(target.content, similar_patterns)
            raw = self._llm.query(
                system=SYSTEM_PROMPT,
                user=f"File: {target.path}\n\n```\n{context}\n```",
            )

            try:
                items = json.loads(raw)
                if not isinstance(items, list):
                    items = items.get("findings", [])
            except json.JSONDecodeError:
                logger.warning("[semantic] failed to parse LLM response for %s", target.path)
                continue

            for item in items:
                findings.append(
                    Vulnerability(
                        id=str(uuid.uuid4()),
                        title=item.get("title", "Unknown"),
                        severity=Severity(item.get("severity", "medium")),
                        cwe_id=item.get("cwe_id", "CWE-Unknown"),
                        cve_id=None,
                        file_path=target.path,
                        line_start=item.get("line_start", 0),
                        line_end=item.get("line_end", 0),
                        code_snippet=item.get("code_snippet", ""),
                        description=item.get("description", ""),
                    )
                )

        state.semantic_findings = findings
        logger.info("[semantic] found %d semantic vulnerabilities", len(findings))
        return state


def _build_context(content: str, similar_patterns: list[str]) -> str:
    """Prepend retrieved vulnerability patterns as context for the LLM."""
    if not similar_patterns:
        return content
    pattern_block = "\n".join(f"# Known pattern: {p}" for p in similar_patterns[:3])
    return f"{pattern_block}\n\n{content}"
