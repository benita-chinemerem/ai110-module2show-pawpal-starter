# PawPal+

A smart daily care planner for pet owners — built with Python and Streamlit.

## Features

| Feature | Description |
|---------|-------------|
| **Owner & pet profiles** | Create an owner with one or more pets; data persists across UI interactions via `st.session_state` |
| **Task management** | Add tasks with title, duration, priority (`high/medium/low`), and frequency (`daily/weekly/as-needed`) |
| **Priority-first scheduling** | Greedy scheduler packs tasks high → medium → low within a configurable daily time budget |
| **Sorting by time** | `DailyPlan.sort_by_time()` displays the schedule in clock order using a lambda sort key |
| **Recurring tasks** | Completing a `daily` or `weekly` task auto-generates the next occurrence with a calculated `due_date` (`timedelta`) |
| **Conflict detection** | `Scheduler.detect_conflicts()` flags overlapping time blocks using the interval test `A.start < B.end AND B.start < A.end`; shown as prominent warnings in the UI |
| **Filtering** | Filter the displayed schedule by pet name or completion status without re-running the scheduler |
| **Reasoning display** | Each scheduled block shows why it was placed (priority, duration, frequency) |
| **Skip explanations** | Tasks that don't fit the time budget appear in a collapsible "Skipped tasks" section with exact remaining-time context |
| **Validation** | `Task.validate()` enforces non-empty titles, positive durations, and valid priority/frequency values before any task enters the system |

## Demo

*Run the app and take a screenshot, then embed it here:*

```
streamlit run app.py
```

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank">
  <img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' />
</a>

---

## System architecture

The final UML diagram (Mermaid source) is in `uml_final.md`. Paste the code block at [mermaid.live](https://mermaid.live) to render it.

**Six classes:**
- `Owner` → owns `Pet`(s)
- `Pet` → holds `Task`(s), handles recurrence via `mark_task_complete()`
- `Task` → validates itself, returns a follow-up on `mark_complete()`
- `Scheduler` → stateless service: `plan()` + `detect_conflicts()`
- `DailyPlan` → result with sorting, filtering, and conflict list
- `ScheduledBlock` → one placed task with clock times, pet reference, and reasons

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the basic greedy planner, PawPal+ includes four algorithmic features that make the schedule more useful in practice:

**Sorting by time**
`DailyPlan.sort_by_time()` returns blocks in ascending start-time order using Python's `sorted()` with a lambda key. Blocks that have no clock time (unscheduled) sink to the end automatically.

**Filtering**
Two filter methods on `DailyPlan` let you slice the plan without rebuilding it:
- `filter_by_pet(name)` — isolates one pet's blocks from a combined plan
- `filter_by_status(completed)` — separates finished tasks from pending ones

**Recurring tasks**
`Task.mark_complete()` returns a follow-up `Task` for recurring tasks instead of just flipping a flag. Daily tasks get a new `due_date` of today + 1 day; weekly tasks get today + 7 days (`timedelta`). `Pet.mark_task_complete()` calls this and automatically appends the follow-up to the pet's task list, so recurring care never falls off the schedule.

**Conflict detection**
`Scheduler.detect_conflicts(blocks)` scans every pair of blocks and flags overlaps using the interval test `A.start < B.end AND B.start < A.end`. It returns human-readable warning strings rather than raising an exception, so the UI can display the warning without crashing.

---

## Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

| # | Test | What it verifies |
|---|------|-----------------|
| 1 | `test_mark_complete_changes_status` | `mark_complete()` flips `completed` to `True` |
| 2 | `test_add_task_increases_pet_task_count` | `Pet.add_task()` grows the task list correctly |
| 3 | `test_sort_by_time_returns_chronological_order` | `DailyPlan.sort_by_time()` returns blocks earliest-first |
| 4 | `test_sort_by_time_with_none_start_times_sinks_to_end` | Unscheduled (None) blocks sort to the end |
| 5 | `test_daily_recurrence_creates_task_due_tomorrow` | Daily task produces follow-up due tomorrow |
| 6 | `test_weekly_recurrence_creates_task_due_in_seven_days` | Weekly task produces follow-up due in 7 days |
| 7 | `test_as_needed_task_has_no_recurrence` | `as-needed` task returns `None` follow-up |
| 8 | `test_pet_mark_task_complete_appends_followup` | `Pet.mark_task_complete()` appends the next recurrence |
| 9 | `test_detect_conflicts_flags_overlapping_blocks` | Overlapping blocks produce a `CONFLICT` warning |
| 10 | `test_detect_conflicts_no_false_positives` | Back-to-back (sequential) blocks are not flagged |
| 11 | `test_scheduler_handles_pet_with_no_tasks` | Empty task list yields an empty, note-free plan |
| 12 | `test_task_validate_rejects_bad_priority` | `validate()` raises `ValueError` for bad priority |
| 13 | `test_task_validate_rejects_zero_duration` | `validate()` raises `ValueError` for zero duration |
| 14 | `test_filter_by_pet_isolates_correct_blocks` | `filter_by_pet()` returns only the named pet's blocks |
| 15 | `test_scheduler_skips_task_that_exceeds_budget` | Tasks that exceed the time budget appear in notes, not blocks |

### Confidence level

★★★★☆ (4 / 5)

Happy paths and the most important edge cases are covered: sorting, all three recurrence branches, both conflict and no-conflict scenarios, validation guards, and the budget-overflow skip logic. The remaining gap is integration-level testing — verifying that the Streamlit `session_state` wiring in `app.py` behaves correctly end-to-end in a real browser session, which would require a UI testing tool such as Playwright or Streamlit's own `AppTest` API.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
