"""LangGraph workflow definition for the multi-agent security pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from orchestrator.agents.exploit_scorer import ExploitScorerAgent
from orchestrator.agents.memory_safety import MemorySafetyAgent
from orchestrator.agents.patcher import PatcherAgent
from orchestrator.agents.report import ReportAgent
from orchestrator.agents.scanner import ScannerAgent
from orchestrator.agents.semantic import SemanticAnalystAgent
from orchestrator.agents.triage import TriageAgent
from orchestrator.agents.validator import ValidatorAgent
from orchestrator.graph.router import (
    route_after_analysis,
    route_after_exploit_scorer,
    route_after_patcher,
    route_after_triage,
    route_after_validator,
)
from orchestrator.graph.state import AgentState


def build_workflow() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register agents as nodes
    graph.add_node("triage", TriageAgent().run)
    graph.add_node("scanner", ScannerAgent().run)
    graph.add_node("memory_safety", MemorySafetyAgent().run)
    graph.add_node("semantic_analyst", SemanticAnalystAgent().run)
    graph.add_node("exploit_scorer", ExploitScorerAgent().run)
    graph.add_node("patcher", PatcherAgent().run)
    graph.add_node("validator", ValidatorAgent().run)
    graph.add_node("report", ReportAgent().run)

    # Entry point
    graph.set_entry_point("triage")

    # Edges
    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {"scanner": "scanner", "report": "report"},
    )

    # After scanner: parallel fan-out to memory_safety + semantic_analyst
    graph.add_conditional_edges(
        "scanner",
        route_after_analysis,
        {
            "exploit_scorer": "exploit_scorer",
            "report": "report",
        },
    )

    graph.add_edge("memory_safety", "exploit_scorer")
    graph.add_edge("semantic_analyst", "exploit_scorer")

    graph.add_conditional_edges(
        "exploit_scorer",
        route_after_exploit_scorer,
        {"patcher": "patcher", "report": "report"},
    )

    graph.add_conditional_edges(
        "patcher",
        route_after_patcher,
        {"validator": "validator", "report": "report"},
    )

    graph.add_conditional_edges(
        "validator",
        route_after_validator,
        {"patcher": "patcher", "report": "report"},
    )

    graph.add_edge("report", END)

    return graph.compile()
