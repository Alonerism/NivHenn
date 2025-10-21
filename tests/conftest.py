"""Pytest configuration for path adjustments and lightweight stubs."""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


if "crewai" not in sys.modules:
    class _StubAgent:
        def __init__(self, **kwargs):
            self.config = kwargs

    class _StubTask:
        def __init__(self, description, agent, expected_output=None):
            self.description = description
            self.agent = agent
            self.expected_output = expected_output
            self.output = types.SimpleNamespace(raw_output="{}")

    class _StubCrew:
        def __init__(self, agents, tasks, verbose=False):
            self.agents = agents
            self.tasks = tasks
            self.verbose = verbose

        def kickoff(self):
            return {}

    sys.modules["crewai"] = types.SimpleNamespace(
        Agent=_StubAgent,
        Crew=_StubCrew,
        Task=_StubTask,
    )
