"""PawPal+ logic layer: domain models and scheduling (skeleton from UML)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


@dataclass
class Owner:
    """Human who owns one or more pets."""

    name: str
    preferences: dict = field(default_factory=dict)


@dataclass
class Pet:
    """Animal that needs scheduled care tasks."""

    name: str
    species: str


@dataclass
class Task:
    """One care item to possibly place on the daily plan."""

    title: str
    duration_minutes: int
    priority: str

    def validate(self) -> None:
        """Ensure task fields are usable by the scheduler."""
        raise NotImplementedError


@dataclass
class ScheduledBlock:
    """One placed task on the plan with optional clock times and reasons."""

    task: Task
    start_time: time | None = None
    end_time: time | None = None
    reasons: list[str] = field(default_factory=list)


@dataclass
class DailyPlan:
    """Result of planning: ordered blocks plus notes (e.g. skipped tasks)."""

    blocks: list[ScheduledBlock] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled blocks."""
        raise NotImplementedError


class Scheduler:
    """Builds a DailyPlan from owner/pet context, tasks, and time budget."""

    def plan(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[Task],
        available_minutes: int,
    ) -> DailyPlan:
        """Produce a plan for the given pet's tasks within the time budget."""
        raise NotImplementedError
