"""Agents package for specialized AI agents."""
from .finance import finance_agent
from .calendar import calendar_agent
from .router import main_agent
from .habit_learner import habit_learner

# Agent registry for easy routing
AGENTS = {
    "finance": finance_agent,
    "calendar": calendar_agent,
    "habit_learner": habit_learner,
    "main": main_agent
}

__all__ = [
    "finance_agent",
    "calendar_agent",
    "main_agent",
    "habit_learner",
    "AGENTS"
]

