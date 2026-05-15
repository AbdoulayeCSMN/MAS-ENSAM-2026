"""Scanner Agent: runs static analysis tools per language."""

from __future__ import annotations

import logging

from agents.base import BaseAgent
from graph.state import AgentState, Language
from tools.semgrep_tool import SemgrepTool
from tools.bandit_tool import BanditTool
from tools.gosec_tool import GosecTool
from tools.spotbugs_tool import SpotBugsTool
from tools.phpcs_tool import PhpCsTool

logger = logging.getLogger(__name__)


class ScannerAgent(BaseAgent):
    name = "scanner"

    def __init__(self) -> None:
        self._semgrep = SemgrepTool()
        self._bandit = BanditTool()
        self._gosec = GosecTool()
        self._spotbugs = SpotBugsTool()
        self._phpcs = PhpCsTool()

    def _execute(self, state: AgentState) -> AgentState:
        findings: list[dict] = []

        # Semgrep covers C/C++, Python, JS/TS, Java, Go, Rust
        semgrep_langs = {
            Language.C, Language.CPP, Language.PYTHON,
            Language.JAVASCRIPT, Language.TYPESCRIPT,
            Language.JAVA, Language.GO, Language.RUST,
        }
        if state.detected_languages & semgrep_langs:
            findings += self._semgrep.run(state.repo_root, state.detected_languages)

        if Language.PYTHON in state.detected_languages:
            findings += self._bandit.run(state.repo_root)

        if Language.GO in state.detected_languages:
            findings += self._gosec.run(state.repo_root)

        if Language.JAVA in state.detected_languages:
            findings += self._spotbugs.run(state.repo_root)

        if Language.PHP in state.detected_languages:
            findings += self._phpcs.run(state.repo_root)

        state.raw_findings = findings
        logger.info("[scanner] found %d raw findings", len(findings))
        return state
