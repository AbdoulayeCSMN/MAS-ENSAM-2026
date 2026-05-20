"""Base class for all security agents."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from orchestrator.graph.state import AgentState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str = "base"

    def run(self, state: AgentState) -> AgentState:
        logger.info("[%s] starting", self.name)
        state.current_agent = self.name
        try:
            state = self._execute(state)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[%s] error: %s", self.name, exc)
            state.errors.append(f"{self.name}: {exc}")
        logger.info("[%s] done", self.name)
        return state

    @abstractmethod
    def _execute(self, state: AgentState) -> AgentState: ...
