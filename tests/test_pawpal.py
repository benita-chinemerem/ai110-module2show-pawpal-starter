"""tests/test_pawpal.py — Automated test suite for PawPal+ core classes."""

import sys
import os
from datetime import date, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import (
    Task, Pet, Owner, Scheduler, DailyPlan, ScheduledBlock
)


# ===========================================================================
# Existing tests (Phase 3)
# ===========================================================================

def test_mark_complete_changes_status():
    """Calling mark_complete() must flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet must increase its task list length by 1."""
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Feed breakfast", duration_minutes=10, priority="high"))
    assert len(pet.tasks) == 1
    pet.add_task(Task(title="Evening walk", duration_minutes=20, priority="medium"))
    assert len(pet.tasks) == 2


# ===========================================================================
# Step 2a — Sorting correctness
# ===========================================================================

def test_sort_by_time_returns_chronological_order():
    """sort_by_time() must return blocks from earliest to latest start time."""
    owner = Owner(name="Alex")
    pet = Pet(name="Buddy", species="Dog")

    # Add tasks in reverse priority so the scheduler places them out of the
    # order we might naively expect — we want to verify sort_by_time, not the
    # scheduler's priority ordering.
    pet.add_task(Task("Late task",  duration_minutes=10, priority="low"))
    pet.add_task(Task("Early task", duration_minutes=10, priority="high"))
    owner.pets.append(pet)

    plan = Scheduler().plan(owner, pet, pet.pending_tasks(), available_minutes=60)
    sorted_blocks = plan.sort_by_time()

    # Extract start times in the order returned
    times = [b.start_time for b in sorted_blocks]
    assert times == sorted(times), (
        "sort_by_time() should return blocks in ascending start-time order."
    )


def test_sort_by_time_with_none_start_times_sinks_to_end():
    """Blocks with no start_time must appear after all timed blocks."""
    timed_block   = ScheduledBlock(
        task=Task("Walk", 20, "high"),
        start_time=time(8, 0),
        end_time=time(8, 20),
    )
    untimed_block = ScheduledBlock(
        task=Task("Groom", 15, "low"),
        start_time=None,
        end_time=None,
    )

    plan = DailyPlan(blocks=[untimed_block, timed_block])
    result = plan.sort_by_time()

    assert result[0].start_time == time(8, 0), "Timed block should come first."
    assert result[-1].start_time is None,       "Untimed block should sink last."


# ===========================================================================
# Step 2b — Recurrence logic
# ===========================================================================

def test_daily_recurrence_creates_task_due_tomorrow():
    """Completing a daily task must return a follow-up due the next day."""
    task = Task("Morning walk", 30, "high", frequency="daily")
    follow_up = task.mark_complete()

    assert task.completed is True,                   "Original task should be marked done."
    assert follow_up is not None,                    "Daily task must produce a follow-up."
    assert follow_up.completed is False,             "Follow-up starts incomplete."
    assert follow_up.due_date == date.today() + timedelta(days=1), (
        "Daily follow-up must be due tomorrow."
    )


def test_weekly_recurrence_creates_task_due_in_seven_days():
    """Completing a weekly task must return a follow-up due 7 days from today."""
    task = Task("Bath time", 45, "low", frequency="weekly")
    follow_up = task.mark_complete()

    assert follow_up is not None
    assert follow_up.due_date == date.today() + timedelta(weeks=1), (
        "Weekly follow-up must be due in 7 days."
    )


def test_as_needed_task_has_no_recurrence():
    """Completing an as-needed task must return None (no follow-up)."""
    task = Task("Vet visit", 60, "high", frequency="as-needed")
    follow_up = task.mark_complete()

    assert follow_up is None, "as-needed tasks must not generate a follow-up."


def test_pet_mark_task_complete_appends_followup():
    """Pet.mark_task_complete() must append the follow-up to pet.tasks."""
    pet = Pet(name="Mochi", species="Cat")
    pet.add_task(Task("Feeding", 10, "high", frequency="daily"))

    assert len(pet.tasks) == 1
    pet.mark_task_complete(pet.tasks[0])

    assert len(pet.tasks) == 2,              "Follow-up should be appended."
    assert pet.tasks[0].completed is True,   "Original task should be done."
    assert pet.tasks[1].completed is False,  "Follow-up should be pending."


# ===========================================================================
# Step 2c — Conflict detection
# ===========================================================================

def test_detect_conflicts_flags_overlapping_blocks():
    """detect_conflicts() must return a warning for two overlapping blocks."""
    scheduler = Scheduler()
    blocks = [
        ScheduledBlock(
            task=Task("Vet appointment", 30, "high"),
            start_time=time(9, 0),
            end_time=time(9, 30),
        ),
        ScheduledBlock(
            task=Task("Grooming", 20, "high"),
            start_time=time(9, 15),   # starts before Vet ends -> overlap
            end_time=time(9, 35),
        ),
    ]
    warnings = scheduler.detect_conflicts(blocks)

    assert len(warnings) == 1,           "Exactly one conflict pair should be found."
    assert "CONFLICT" in warnings[0],    "Warning message should contain 'CONFLICT'."


def test_detect_conflicts_no_false_positives():
    """detect_conflicts() must return nothing when blocks are sequential."""
    scheduler = Scheduler()
    blocks = [
        ScheduledBlock(
            task=Task("Walk", 30, "high"),
            start_time=time(8, 0),
            end_time=time(8, 30),
        ),
        ScheduledBlock(
            task=Task("Feed", 10, "high"),
            start_time=time(8, 30),   # starts exactly when Walk ends -> no overlap
            end_time=time(8, 40),
        ),
    ]
    warnings = scheduler.detect_conflicts(blocks)

    assert warnings == [], "Back-to-back blocks must not be flagged as conflicts."


# ===========================================================================
# Edge cases
# ===========================================================================

def test_scheduler_handles_pet_with_no_tasks():
    """Planning for a pet with zero tasks must return an empty, note-free plan."""
    owner = Owner(name="Sam")
    pet   = Pet(name="Ghost", species="Dog")
    owner.pets.append(pet)

    plan = Scheduler().plan(owner, pet, [], available_minutes=60)

    assert plan.blocks == [],  "No tasks -> no scheduled blocks."
    assert plan.notes  == [],  "No tasks -> no skip notes either."
    assert plan.total_scheduled_minutes() == 0


def test_task_validate_rejects_bad_priority():
    """validate() must raise ValueError for an unrecognised priority string."""
    import pytest
    task = Task("Walk", 30, priority="urgent")
    with pytest.raises(ValueError, match="priority"):
        task.validate()


def test_task_validate_rejects_zero_duration():
    """validate() must raise ValueError when duration_minutes is 0 or negative."""
    import pytest
    with pytest.raises(ValueError, match="duration_minutes"):
        Task("Walk", 0, "high").validate()


def test_filter_by_pet_isolates_correct_blocks():
    """filter_by_pet() must return only blocks assigned to the named pet."""
    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Mochi", species="Cat")

    b_dog = ScheduledBlock(task=Task("Walk", 30, "high"), pet=dog,
                           start_time=time(8, 0), end_time=time(8, 30))
    b_cat = ScheduledBlock(task=Task("Play", 20, "medium"), pet=cat,
                           start_time=time(8, 30), end_time=time(8, 50))

    plan = DailyPlan(blocks=[b_dog, b_cat])

    assert len(plan.filter_by_pet("Buddy")) == 1
    assert len(plan.filter_by_pet("Mochi")) == 1
    assert len(plan.filter_by_pet("Nobody")) == 0


def test_scheduler_skips_task_that_exceeds_budget():
    """A task longer than the remaining budget must appear in plan.notes, not blocks."""
    owner = Owner(name="Alex")
    pet   = Pet(name="Rex", species="Dog")
    pet.add_task(Task("Quick feed", 10, "high"))
    pet.add_task(Task("Long bath",  90, "low"))
    owner.pets.append(pet)

    plan = Scheduler().plan(owner, pet, pet.pending_tasks(), available_minutes=20)

    scheduled_titles = [b.task.title for b in plan.blocks]
    assert "Quick feed" in scheduled_titles, "Short task should be scheduled."
    assert "Long bath" not in scheduled_titles, "Task exceeding budget must be skipped."
    assert any("Long bath" in n for n in plan.notes), "Skipped task must appear in notes."
