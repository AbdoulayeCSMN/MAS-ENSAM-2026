"""Routing logic: decides which agent runs next based on state."""

from graph.state import AgentState, Language


MEMORY_UNSAFE_LANGUAGES = {Language.C, Language.CPP, Language.RUST}


def route_after_triage(state: AgentState) -> str:
    if state.errors:
        return "report"
    return "scanner"


def route_after_scanner(state: AgentState) -> list[str]:
    """Fan-out: run memory safety and semantic analysis in parallel."""
    next_agents = ["semantic_analyst"]
    if state.needs_memory_safety:
        next_agents.append("memory_safety")
    return next_agents


def route_after_analysis(state: AgentState) -> str:
    all_vulns = (
        state.vulnerabilities
        + state.memory_safety_findings
        + state.semantic_findings
    )
    if not all_vulns:
        return "report"
    return "exploit_scorer"


def route_after_exploit_scorer(state: AgentState) -> str:
    exploitable = [v for v in state.vulnerabilities if v.is_exploitable]
    if exploitable:
        return "patcher"
    return "report"


def route_after_patcher(state: AgentState) -> str:
    if state.patches_pending:
        return "validator"
    return "report"


def route_after_validator(state: AgentState) -> str:
    # If some patches were rejected and we haven't hit the retry limit
    if state.patches_rejected and state.iteration < state.max_patch_iterations:
        return "patcher"
    return "report"


def should_run_memory_safety(state: AgentState) -> bool:
    return bool(state.detected_languages & MEMORY_UNSAFE_LANGUAGES)
