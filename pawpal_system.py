"""PawPal+ logic layer: domain models and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """One care item to possibly place on the daily plan."""

    title: str
    duration_minutes: int
    priority: str
    frequency: str = "daily"       # "daily" | "weekly" | "as-needed"
    completed: bool = False
    due_date: date | None = None   # next occurrence date (None = always due)

    # ------------------------------------------------------------------
    # Completion & recurrence  (Step 3)
    # ------------------------------------------------------------------

    def mark_complete(self) -> Task | None:
        """Mark this task as completed and optionally create the next recurrence.

        Recurrence rules
        ----------------
        ``"daily"``
            The follow-up task is due ``today + 1 day`` (tomorrow).
        ``"weekly"``
            The follow-up task is due ``today + 7 days``.
        ``"as-needed"``
            No follow-up is created; the method returns ``None``.

        The follow-up is a brand-new ``Task`` instance that copies all fields
        from this task (title, duration, priority, frequency) but starts with
        ``completed=False`` and its ``due_date`` set to the calculated next
        occurrence.  This task's ``completed`` flag is set to ``True`` before
        the follow-up is returned.

        Returns
        -------
        Task | None
            A fresh incomplete ``Task`` for the next occurrence, or ``None``
            for non-recurring tasks.

        Example
        -------
        >>> walk = Task("Morning walk", 30, "high", frequency="daily")
        >>> follow_up = walk.mark_complete()
        >>> walk.completed
        True
        >>> follow_up.due_date == date.today() + timedelta(days=1)
        True
        """
        self.completed = True

        today = date.today()
        if self.frequency == "daily":
            next_due = today + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = today + timedelta(weeks=1)
        else:
            return None   # "as-needed" — no automatic follow-up

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            due_date=next_due,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Ensure task fields are usable by the scheduler.

        Raises
        ------
        ValueError
            If any field contains an unusable value.
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

    def mark_task_complete(self, task: Task) -> None:
        """Mark *task* complete and auto-append the next recurrence if any.

        Step 3: after calling task.mark_complete() the returned follow-up
        Task (if recurring) is added directly to this pet's task list so
        it will appear in future pending_tasks() calls.
        """
        follow_up = task.mark_complete()
        if follow_up is not None:
            self.tasks.append(follow_up)


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
        """Flat list of every task across all owned pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Flat list of incomplete tasks across all owned pets."""
        return [task for pet in self.pets for task in pet.pending_tasks()]


# ---------------------------------------------------------------------------
# ScheduledBlock
# ---------------------------------------------------------------------------

@dataclass
class ScheduledBlock:
    """One placed task on the plan with optional clock times and reasons."""

    task: Task
    pet: Pet | None = None          # which pet this block belongs to
    start_time: time | None = None
    end_time: time | None = None
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    """Result of planning: ordered blocks plus notes."""

    blocks: list[ScheduledBlock] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)   # Step 4

    def total_scheduled_minutes(self) -> int:
        """Sum of durations for all scheduled blocks."""
        return sum(block.task.duration_minutes for block in self.blocks)

    # ------------------------------------------------------------------
    # Step 2a — sort blocks by start time
    # ------------------------------------------------------------------

    def sort_by_time(self) -> list[ScheduledBlock]:
        """Return a new list of blocks sorted by start_time, earliest first.

        Sorting key
        -----------
        A lambda extracts ``start_time`` from each block.  Because
        ``start_time`` may be ``None`` for blocks that were never given a
        clock position, ``None`` is substituted with ``time(23, 59)`` so
        those blocks sink to the end of the list rather than raising a
        ``TypeError`` during comparison.

        The original ``self.blocks`` list is not mutated; a new sorted list
        is returned so callers can choose whether to replace the plan's block
        order or just display a sorted view.

        Returns
        -------
        list[ScheduledBlock]
            Blocks in ascending start-time order, unscheduled blocks last.

        Example
        -------
        >>> plan.sort_by_time()[0].start_time
        datetime.time(8, 0)
        """
        return sorted(
            self.blocks,
            key=lambda b: b.start_time if b.start_time is not None else time(23, 59),
        )

    # ------------------------------------------------------------------
    # Step 2b — filter helpers
    # ------------------------------------------------------------------

    def filter_by_pet(self, pet_name: str) -> list[ScheduledBlock]:
        """Return only the scheduled blocks that belong to the named pet.

        Useful when a ``DailyPlan`` contains blocks for multiple pets (for
        example when an owner has a dog and a cat scheduled together) and the
        UI or caller wants to display one pet's tasks in isolation.

        Parameters
        ----------
        pet_name:
            The exact ``Pet.name`` string to match (case-sensitive).

        Returns
        -------
        list[ScheduledBlock]
            All blocks whose ``block.pet.name`` equals *pet_name*.
            Returns an empty list if no match is found or if no block has a
            pet attached.
        """
        return [b for b in self.blocks if b.pet and b.pet.name == pet_name]

    def filter_by_status(self, completed: bool) -> list[ScheduledBlock]:
        """Return blocks whose underlying task matches the given completion status.

        Parameters
        ----------
        completed:
            Pass ``True`` to get only finished tasks; ``False`` for pending.

        Returns
        -------
        list[ScheduledBlock]
            Blocks where ``block.task.completed == completed``.
        """
        return [b for b in self.blocks if b.task.completed == completed]


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

_PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}
_DAY_START = time(8, 0)


class Scheduler:
    """Builds a DailyPlan from owner/pet context, tasks, and a time budget."""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted high -> medium -> low priority."""
        return sorted(tasks, key=lambda t: _PRIORITY_ORDER.get(t.priority, 99))

    def _make_block(self, task: Task, pet: Pet, start: time) -> ScheduledBlock:
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
            pet=pet,
            start_time=dt_start.time(),
            end_time=dt_end.time(),
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Step 4 — conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, blocks: list[ScheduledBlock]) -> list[str]:
        """Scan a list of scheduled blocks and return overlap warning strings.

        Algorithm
        ---------
        Every ordered pair ``(i, j)`` where ``i < j`` is compared using the
        standard interval-overlap test::

            A overlaps B  iff  A.start < B.end  AND  B.start < A.end

        This single condition catches all overlap shapes: exact same start
        time, partial overlap, and one block fully contained inside another.

        Design choice — warnings, not exceptions
        -----------------------------------------
        The method returns a list of human-readable strings rather than
        raising an exception so the caller (UI, ``plan()``, tests) can decide
        how to handle conflicts: display a banner, log them, or block the save.
        An empty list means no conflicts were found.

        Complexity
        ----------
        O(n²) in the number of blocks.  Acceptable for typical daily plans
        (< 20 tasks); a sweep-line algorithm would be more efficient at scale.

        Parameters
        ----------
        blocks:
            The list of ``ScheduledBlock`` objects to check.  Blocks without
            a ``start_time`` or ``end_time`` are silently skipped.

        Returns
        -------
        list[str]
            One warning string per overlapping pair, or an empty list if
            no overlaps exist.
        """
        warnings: list[str] = []
        for i in range(len(blocks)):
            for j in range(i + 1, len(blocks)):
                a, b = blocks[i], blocks[j]
                if a.start_time is None or b.start_time is None:
                    continue
                # Overlap condition
                if a.start_time < b.end_time and b.start_time < a.end_time:
                    warnings.append(
                        f"CONFLICT: '{a.task.title}' "
                        f"({a.start_time.strftime('%I:%M %p')}-"
                        f"{a.end_time.strftime('%I:%M %p')}) overlaps "
                        f"'{b.task.title}' "
                        f"({b.start_time.strftime('%I:%M %p')}-"
                        f"{b.end_time.strftime('%I:%M %p')})"
                    )
        return warnings

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
        """Produce a DailyPlan for *pet* within *available_minutes*."""
        daily_plan = DailyPlan()
        valid_tasks: list[Task] = []

        # Validate — quarantine bad tasks with a note
        for task in tasks:
            try:
                task.validate()
                valid_tasks.append(task)
            except ValueError as exc:
                daily_plan.notes.append(
                    f"Skipped '{task.title}' for {pet.name} - invalid task: {exc}"
                )

        # Sort by priority
        sorted_tasks = self._sort_tasks(valid_tasks)

        # Greedy fit
        minutes_used = 0
        current_time = _DAY_START

        for task in sorted_tasks:
            remaining = available_minutes - minutes_used
            if task.duration_minutes <= remaining:
                block = self._make_block(task, pet, current_time)
                daily_plan.blocks.append(block)
                current_time = block.end_time  # type: ignore[assignment]
                minutes_used += task.duration_minutes
            else:
                daily_plan.notes.append(
                    f"Skipped '{task.title}' for {pet.name} - "
                    f"not enough time remaining "
                    f"({remaining} min left, needs {task.duration_minutes} min)"
                )

        # Conflict detection (Step 4) — run on all blocks after scheduling
        daily_plan.conflicts = self.detect_conflicts(daily_plan.blocks)

        return daily_plan
