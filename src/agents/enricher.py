"""AI Enricher Agent: adds context, remediation, and priority using LLM."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from agents.base import BaseAgent
from graph.state import AgentState, Vulnerability
from llm.client import LLMClient

logger = logging.getLogger(__name__)


class EnricherAgent(BaseAgent):
    """Enriches vulnerabilities with AI-generated context and fixes."""
    
    name = "enricher"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def _execute(self, state: AgentState) -> AgentState:
        if not state.vulnerabilities:
            return state
        
        # Enrich in parallel
        enriched = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._enrich_vulnerability, v) for v in state.vulnerabilities]
            for future in futures:
                enriched.append(future.result())
        
        state.vulnerabilities = enriched
        return state
    
    def _enrich_vulnerability(self, vuln: Vulnerability) -> Vulnerability:
        """Enrich a single vulnerability with AI."""
        prompt = f"""Analyze this vulnerability and provide:
1. Likelihood (High/Medium/Low)
2. Impact (Critical/High/Medium/Low)
3. Simple fix (max 2 sentences)
4. Priority (P1/P2/P3)

Vulnerability: {vuln.title}
CWE: {vuln.cwe_id}
Description: {vuln.description}
Code: {vuln.code_snippet[:500]}

Respond with JSON only: 
{{"likelihood": "...", "impact": "...", "fix": "...", "priority": "..."}}"""

        try:
            response = self._llm.query(system="You are a security expert.", user=prompt, model="fast")
            data = json.loads(response)
            
            vuln.extra['likelihood'] = data.get('likelihood', 'Medium')
            vuln.extra['impact'] = data.get('impact', 'Medium')
            vuln.extra['suggested_fix'] = data.get('fix', '')
            
            priority = data.get('priority', 'P2')
            if priority == 'P1':
                vuln.cvss_score = max(vuln.cvss_score, 8.0)
            elif priority == 'P2':
                vuln.cvss_score = max(vuln.cvss_score, 5.0)
                
        except Exception as e:
            logger.warning(f"Enrichment failed for {vuln.id}: {e}")
            vuln.extra['enrichment_error'] = str(e)
        
        return vuln