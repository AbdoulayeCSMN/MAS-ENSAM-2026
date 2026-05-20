"""Semgrep wrapper — multi-language static analysis."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from orchestrator.graph.state import Language

logger = logging.getLogger(__name__)

LANG_RULESET: dict[Language, list[str]] = {
    Language.C:          ["p/c", "p/default"],
    Language.CPP:        ["p/cpp", "p/default"],
    Language.PYTHON:     ["p/python", "p/owasp-top-ten", "p/secrets"],
    Language.JAVASCRIPT: ["p/javascript", "p/nodejs", "p/owasp-top-ten"],
    Language.TYPESCRIPT: ["p/typescript", "p/nodejs", "p/owasp-top-ten"],
    Language.JAVA:       ["p/java", "p/owasp-top-ten"],
    Language.GO:         ["p/golang", "p/default"],
    Language.RUST:       ["p/rust"],
    Language.PHP:        ["p/php"],
}


class SemgrepTool:
    def run(self, repo_root: str, languages: set[Language]) -> list[dict]:
        rulesets: set[str] = set()
        for lang in languages:
            rulesets.update(LANG_RULESET.get(lang, []))

        if not rulesets:
            return []

        cmd = [
            "semgrep",
            "--json",
            "--no-rewrite-rule-ids",
            "--quiet",
        ]
        for ruleset in rulesets:
            cmd += ["--config", ruleset]
        cmd.append(repo_root)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            data = json.loads(result.stdout)
            return self._normalize(data.get("results", []))
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
            logger.warning("[semgrep] error: %s", exc)
            return []

    def _normalize(self, results: list[dict]) -> list[dict]:
        findings = []
        for r in results:
            findings.append({
                "tool": "semgrep",
                "rule_id": r.get("check_id", ""),
                "file": r.get("path", ""),
                "line": r.get("start", {}).get("line", 0),
                "message": r.get("extra", {}).get("message", ""),
                "severity": r.get("extra", {}).get("severity", "WARNING").lower(),
                "cwe": _extract_cwe(r),
                "snippet": r.get("extra", {}).get("lines", ""),
            })
        return findings


def _extract_cwe(result: dict) -> str:
    metadata = result.get("extra", {}).get("metadata", {})
    cwe = metadata.get("cwe", [])
    if isinstance(cwe, list) and cwe:
        return cwe[0]
    if isinstance(cwe, str):
        return cwe
    return "CWE-Unknown"
