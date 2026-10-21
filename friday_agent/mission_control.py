"""Session-scoped mission planning with evidence-based progress tracking.

Mission state is ephemeral to the voice session. A model's assertion of success
is never labelled verified; verification requires a deterministic local check.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import RLock
from uuid import uuid4

MAX_STEPS = 8
MAX_MISSIONS = 5


@dataclass
class MissionStep:
    description: str
    status: str = "pending"
    evidence: str = ""
    verification: str = ""


@dataclass
class Mission:
    id: str
    goal: str
    success_criteria: str
    steps: list[MissionStep] = field(default_factory=list)


class MissionControl:
    """Bounded, in-memory mission state machine; no arbitrary code execution."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._missions: dict[str, Mission] = {}

    @staticmethod
    def _require_text(text: str, label: str, max_length: int = 500) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{label} must be nonempty text")
        value = text.strip()
        if len(value) > max_length:
            raise ValueError(f"{label} exceeds {max_length} characters")
        return value

    def create(self, goal: str, steps: list[str], success_criteria: str) -> dict:
        goal = self._require_text(goal, "goal")
        success_criteria = self._require_text(success_criteria, "success_criteria")
        if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
            raise ValueError(f"steps must be a list of 1 to {MAX_STEPS} actions")
        descriptions = [self._require_text(step, "step", 300) for step in steps]
        with self._lock:
            if len(self._missions) >= MAX_MISSIONS:
                raise ValueError("Mission capacity reached for this voice session")
            mission = Mission(
                id=uuid4().hex[:12],
                goal=goal,
                success_criteria=success_criteria,
                steps=[MissionStep(description=step) for step in descriptions],
            )
            mission.steps[0].status = "active"
            self._missions[mission.id] = mission
            return self._snapshot(mission)

    def _get(self, mission_id: str) -> Mission:
        if not isinstance(mission_id, str) or mission_id not in self._missions:
            raise ValueError("Unknown mission_id for this voice session")
        return self._missions[mission_id]

    @staticmethod
    def _overall(mission: Mission) -> str:
        statuses = [step.status for step in mission.steps]
        if all(status == "verified" for status in statuses):
            return "verified"
        if "blocked" in statuses:
            return "blocked"
        if all(status in ("reported", "verified") for status in statuses):
            return "awaiting_verification"
        return "in_progress"

    @classmethod
    def _snapshot(cls, mission: Mission) -> dict:
        return {
            "id": mission.id,
            "goal": mission.goal,
            "success_criteria": mission.success_criteria,
            "status": cls._overall(mission),
            "steps": [asdict(step) for step in mission.steps],
        }

    def status(self, mission_id: str) -> dict:
        with self._lock:
            return self._snapshot(self._get(mission_id))

    def report(self, mission_id: str, step_number: int, evidence: str, passed: bool) -> dict:
        """Record an unverified report; a failure blocks further execution."""
        evidence = self._require_text(evidence, "evidence", 1200)
        if type(passed) is not bool:
            raise ValueError("passed must be boolean")
        with self._lock:
            mission = self._get(mission_id)
            index = step_number - 1
            if type(step_number) is not int or not 0 <= index < len(mission.steps):
                raise ValueError("step_number is out of range")
            current = next(
                (i for i, step in enumerate(mission.steps) if step.status in ("active", "blocked")),
                None,
            )
            if current != index:
                raise ValueError("Only the active or blocked step can be reported")
            step = mission.steps[index]
            step.evidence = evidence
            step.verification = ""
            step.status = "reported" if passed else "blocked"
            if passed and index + 1 < len(mission.steps):
                mission.steps[index + 1].status = "active"
            return self._snapshot(mission)

    def verify_file(
        self, mission_id: str, step_number: int, path: str, must_contain: str
    ) -> dict:
        """Verify a reported step with a real workspace read, not model testimony."""
        from friday_agent.mcp_tools import read_workspace_file

        path = self._require_text(path, "path", 500)
        needle = self._require_text(must_contain, "must_contain", 200)
        with self._lock:
            mission = self._get(mission_id)
            if type(step_number) is not int or not 1 <= step_number <= len(mission.steps):
                raise ValueError("step_number is out of range")
            step = mission.steps[step_number - 1]
            if step.status != "reported":
                raise ValueError("Only reported steps can be verified")
            result = read_workspace_file(path)
            if not result.ok or needle not in result.content:
                raise ValueError("Workspace verification failed: expected text not found")
            step.status = "verified"
            step.verification = f"workspace:{path} contains required text"
            return self._snapshot(mission)
