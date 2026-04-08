"""tests/test_pawpal.py — Simple unit tests for PawPal+ core classes."""

import sys
import os

# Make sure the project root is on the path so the import works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


# ---------------------------------------------------------------------------
# Test 1 — Task Completion
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() must flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")

    # Starts incomplete
    assert task.completed is False, "A new task should not be completed yet."

    task.mark_complete()

    # Must now be complete
    assert task.completed is True, "mark_complete() should set completed to True."


# ---------------------------------------------------------------------------
# Test 2 — Task Addition
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet must increase its task list length by 1."""
    pet = Pet(name="Buddy", species="Dog")

    # Starts with no tasks
    assert len(pet.tasks) == 0, "A new pet should have no tasks."

    pet.add_task(Task(title="Feed breakfast", duration_minutes=10, priority="high"))

    assert len(pet.tasks) == 1, "Pet should have exactly 1 task after add_task()."

    pet.add_task(Task(title="Evening walk", duration_minutes=20, priority="medium"))

    assert len(pet.tasks) == 2, "Pet should have exactly 2 tasks after a second add_task()."
