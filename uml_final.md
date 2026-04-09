# PawPal+ — Final System Architecture (UML)

Paste the block below into [mermaid.live](https://mermaid.live) to render the diagram,
or view it directly in VS Code with the Mermaid Preview extension.

```mermaid
classDiagram
    class Owner {
        +name: str
        +preferences: dict
        +pets: list~Pet~
        +get_all_tasks() list~Task~
        +get_all_pending_tasks() list~Task~
    }

    class Pet {
        +name: str
        +species: str
        +tasks: list~Task~
        +add_task(task: Task) None
        +pending_tasks() list~Task~
        +mark_task_complete(task: Task) None
    }

    class Task {
        +title: str
        +duration_minutes: int
        +priority: str
        +frequency: str
        +completed: bool
        +due_date: date | None
        +mark_complete() Task | None
        +validate() None
    }

    class ScheduledBlock {
        +task: Task
        +pet: Pet | None
        +start_time: time | None
        +end_time: time | None
        +reasons: list~str~
    }

    class DailyPlan {
        +blocks: list~ScheduledBlock~
        +notes: list~str~
        +conflicts: list~str~
        +total_scheduled_minutes() int
        +sort_by_time() list~ScheduledBlock~
        +filter_by_pet(name: str) list~ScheduledBlock~
        +filter_by_status(completed: bool) list~ScheduledBlock~
    }

    class Scheduler {
        +plan(owner, pet, tasks, available_minutes) DailyPlan
        +detect_conflicts(blocks) list~str~
        -_sort_tasks(tasks) list~Task~
        -_make_block(task, pet, start) ScheduledBlock
    }

    Owner        "1" --> "0..*" Pet          : owns
    Pet          "1" --> "0..*" Task         : has tasks
    Task         ..>            Task         : mark_complete returns follow-up
    Scheduler    ..>            DailyPlan    : produces
    DailyPlan    "1" --> "0..*" ScheduledBlock : contains
    ScheduledBlock "1" --> "1"  Task         : references
    ScheduledBlock "1" --> "0..1" Pet        : belongs to
```

## Changes from initial design

| Area | Initial | Final |
|------|---------|-------|
| `Task` fields | title, duration, priority | + `frequency`, `completed`, `due_date` |
| `Task` methods | `validate()` | + `mark_complete()` returning a follow-up Task |
| `Pet` methods | `add_task()`, `pending_tasks()` | + `mark_task_complete()` for recurrence |
| `ScheduledBlock` | task, start, end, reasons | + `pet` field for multi-pet filtering |
| `DailyPlan` | blocks, notes, `total_scheduled_minutes()` | + `conflicts` list, `sort_by_time()`, `filter_by_pet()`, `filter_by_status()` |
| `Scheduler` | `plan()`, `_sort_tasks()`, `_make_block()` | + `detect_conflicts()` |
