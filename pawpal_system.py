"""PawPal+ logic layer: domain models and scheduling (skeleton from UML)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """One care item to possibly place on the daily plan."""

    title: str
    duration_minutes: int
    priority: str
    frequency: str = "daily"   # "daily" | "weekly" | "as-needed"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def validate(self) -> None:
        """Ensure task fields are usable by the scheduler.

        Raises:
            ValueError: if any field contains an unusable value.
        """
        if not self.title or not self.title.strip():
            raise ValueError("Task title must not be empty.")
        if self.duration_minutes <= 0:
            raise ValueError(
                f"duration_minutes must be > 0, got {self.duration_minutes}."
            )
        valid_priorities = {"high", "medium", "low"}
        if self.priority not in valid_priorities:
            raise ValueError(
                f"priority must be one of {valid_priorities}, got '{self.priority}'."
            )
        valid_frequencies = {"daily", "weekly", "as-needed"}
        if self.frequency not in valid_frequencies:
            raise ValueError(
                f"frequency must be one of {valid_frequencies}, got '{self.frequency}'."
            )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Animal that needs scheduled care tasks."""

    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Validate and append a task to this pet's task list."""
        task.validate()
        self.tasks.append(task)

    def pending_tasks(self) -> list[Task]:
        """Return tasks that have not yet been marked completed."""
        return [t for t in self.tasks if not t.completed]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Human who owns one or more pets."""

    name: str
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every task across all owned pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Return a flat list of incomplete tasks across all owned pets."""
        return [task for pet in self.pets for task in pet.pending_tasks()]


# ---------------------------------------------------------------------------
# ScheduledBlock  (unchanged structure, used by Scheduler)
# ---------------------------------------------------------------------------

@dataclass
class ScheduledBlock:
    """One placed task on the plan with optional clock times and reasons."""

    task: Task
    start_time: time | None = None
    end_time: time | None = None
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    """Result of planning: ordered blocks plus notes (e.g. skipped tasks)."""

    blocks: list[ScheduledBlock] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled blocks."""
        return sum(block.task.duration_minutes for block in self.blocks)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
_DAY_START = time(8, 0)   # schedule blocks beginning at 08:00


class Scheduler:
    """Builds a DailyPlan from owner/pet context, tasks, and a time budget.

    Algorithm
    ---------
    1. Validate each task — skip invalid ones and record a note.
    2. Sort the remaining tasks by priority (high → medium → low).
    3. Greedily walk the sorted list:
       - If the task fits in the remaining time budget, create a
         ScheduledBlock with clock start/end times and reasons.
       - If it does not fit, append a "Skipped" note to the plan.
    4. Return the completed DailyPlan.
    """

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted high → medium → low priority."""
        return sorted(tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))

    def _make_block(self, task: Task, start: time) -> ScheduledBlock:
        """Build a ScheduledBlock with computed clock times and reason strings."""
        dt_start = datetime.combine(datetime.today(), start)
        dt_end = dt_start + timedelta(minutes=task.duration_minutes)
        reasons = [
            f"Priority: {task.priority}",
            f"Duration: {task.duration_minutes} min",
            f"Frequency: {task.frequency}",
        ]
        return ScheduledBlock(
            task=task,
            start_time=dt_start.time(),
            end_time=dt_end.time(),
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def plan(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[Task],
        available_minutes: int,
    ) -> DailyPlan:
        """Produce a DailyPlan for *pet* using *tasks* within *available_minutes*.

        Parameters
        ----------
        owner:
            The pet's owner (used for context / future preference logic).
        pet:
            The pet being scheduled (used for context in notes).
        tasks:
            The task list to schedule (may come from pet.tasks or elsewhere).
        available_minutes:
            Total minutes the owner has free today.

        Returns
        -------
        DailyPlan
            Ordered scheduled blocks plus any skip/error notes.
        """
        daily_plan = DailyPlan()
        valid_tasks: list[Task] = []

        # Step 1 — validate; quarantine bad tasks with a note
        for task in tasks:
            try:
                task.validate()
                valid_tasks.append(task)
            except ValueError as exc:
                daily_plan.notes.append(
                    f"Skipped '{task.title}' for {pet.name} - invalid task: {exc}"
                )

        # Step 2 — sort by priority
        sorted_tasks = self._sort_tasks(valid_tasks)

        # Step 3 — greedy fit
        minutes_used = 0
        current_time = _DAY_START

        for task in sorted_tasks:
            remaining = available_minutes - minutes_used
            if task.duration_minutes <= remaining:
                block = self._make_block(task, current_time)
                daily_plan.blocks.append(block)
                # Advance the clock cursor
                current_time = block.end_time  # type: ignore[assignment]
                minutes_used += task.duration_minutes
            else:
                daily_plan.notes.append(
                    f"Skipped '{task.title}' for {pet.name} - "
                    f"not enough time remaining "
                    f"({remaining} min left, needs {task.duration_minutes} min)"
                )

        return daily_plan
