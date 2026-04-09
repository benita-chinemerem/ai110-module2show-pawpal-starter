# PawPal+ Project Reflection


## 1. System Design
PawPal+ supports three main things an owner does in the app:

1. **Profile** — Enter or update basic owner and pet information so plans have the right context.
2. **Tasks** — Add or edit care tasks (for example walks or feeding), including duration and priority.
3. **Plan** — Generate a daily schedule from available time and priorities, view it clearly, and read why the app ordered or skipped tasks.

---

**a. Initial design**

My initial UML centered on four domain types plus a scheduling service, matching how the app flows: profile (who), tasks (what), plan (output), and an engine that builds the plan.

- **Owner** — Stores the human's **name** and **preferences** (for example quiet hours or preferred walk times once the scheduler uses them). In the diagram, an owner *owns* one or more pets.
- **Pet** — Stores the animal's **name** and **species** so the plan and explanations can refer to the right pet.
- **Task** — One care item (**title**, **duration_minutes**, **priority**). Tasks are what get sorted and packed into the day. **validate()** will enforce sensible inputs (for example positive duration) before scheduling.
- **DailyPlan** — The result of planning: **blocks** (ordered placements) and **notes** for anything that did not fit or needs a global explanation. **total_scheduled_minutes()** will sum scheduled time for checks and display.
- **ScheduledBlock** — One row of the plan: the **Task**, optional **start_time** / **end_time**, and **reasons** (short strings) so the UI can explain *why* something was placed or ordered as it was.
- **Scheduler** — Stateless service with **plan(owner, pet, tasks, available_minutes)** that reads context and returns a **DailyPlan**. Time available for the day is a parameter here so **Owner** / **Pet** stay about identity, not "today's minutes."

Associations in the model: **Owner → Pet** (owns), **Pet → Task** (the pet's care needs; in the app the task list is often passed into **plan** alongside **Pet** so Streamlit can keep a simple list). **DailyPlan** references **Task** through each **ScheduledBlock**.

**b. Design changes**

Yes. After reviewing `pawpal_system.py`, I made one structural tweak and noted a few items for later.

- **Change:** Added **`pets: list[Pet]`** on **Owner** (with `default_factory=list`) so the code matches the UML **"Owner owns Pet(s)"** relationship instead of only having two disconnected datatypes. The UI can append the current **Pet** when the user saves profile data, which keeps the object graph aligned with the diagram.
- **Not changed (intentionally):** Tasks are still passed as **`tasks: list[Task]`** into **`Scheduler.plan`** rather than embedded only on **Pet**, so the Streamlit session can keep one flat task list without duplicating storage; the **Pet** instance remains the contextual "who this plan is for."
- **Later additions:** `Task` gained `frequency`, `completed`, and `due_date`. `ScheduledBlock` gained a `pet` reference for filtering. `DailyPlan` gained `conflicts`, `sort_by_time()`, and the two filter methods. `Scheduler` gained `detect_conflicts()`. All of these grew naturally from the original four-class skeleton without requiring a redesign.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Time budget** (`available_minutes`) — the single hardest constraint. A task that does not fit is skipped entirely; there is no splitting or partial scheduling.
2. **Priority** (`high / medium / low`) — tasks are sorted high → medium → low before the greedy fit loop. This means a high-priority task is always placed before a low-priority one even if adding the low-priority task first would theoretically "fit more" overall. The owner's intent (what matters most) was judged more important than mathematical packing efficiency.
3. **Completion status** — only `pending_tasks()` are passed to `plan()`, so already-completed tasks are never re-scheduled.

`preferences: dict` exists on `Owner` but is not yet read by the scheduler — it is a placeholder for future constraints such as "no tasks before 9 AM" or "prefer walks in the morning."

**b. Tradeoffs**

**Tradeoff: overlap detection checks every pair of blocks (O(n²)) instead of a sorted sweep.**

`detect_conflicts` compares every pair of blocks with a nested loop. A more efficient approach would sort blocks by start time first and then only compare each block against its immediate neighbors — reducing work from O(n²) to O(n log n). The nested-loop version was kept because a typical daily pet care plan has fewer than 20 tasks: at that scale the two approaches are indistinguishable in speed, and the pair-comparison logic (`a.start < b.end AND b.start < a.end`) reads almost like plain English, making it easy to verify correctness at a glance. The tradeoff is reasonable here because clarity and correctness matter more than micro-performance for a small personal scheduling app. If the scheduler were extended to handle dozens of pets or bulk-import hundreds of tasks, switching to a sweep-line algorithm would be worth the added complexity.

**Tradeoff: greedy priority-first packing does not find the globally optimal schedule.**

The greedy algorithm picks the highest-priority task first and fits it if it can. This means a schedule with 60 minutes available might schedule one 55-minute high-priority task and skip three 15-minute medium-priority tasks — even though dropping the long task would allow all three medium ones to fit. The tradeoff was accepted because: (a) for pet care, doing the most important thing first is the right behavior even if it means fewer total tasks; (b) the full optimal-packing problem (0/1 knapsack) is NP-hard and far more complex to implement and explain; and (c) the skip notes in the UI tell the owner exactly what was left out, so they can adjust the time budget manually.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase of the project, but with a different purpose at each stage:

- **Design brainstorming** — In Phase 1, AI helped evaluate whether `tasks` should live on `Pet` or be passed separately to `Scheduler.plan()`. The AI presented both options; the decision to keep tasks as a parameter (not stored on `Pet`) was made by reasoning about how Streamlit's session state works — the AI provided the tradeoffs, the human made the call.
- **Incremental implementation** — Each class was stubbed first, then fleshed out with AI assistance. This kept the AI from generating large blocks of code that would be hard to review. Asking "implement just `Task.mark_complete()` with recurrence logic" produced a focused, reviewable result rather than a full rewrite.
- **Test generation** — AI suggested test cases for edge cases (pet with no tasks, `as-needed` tasks returning `None`, back-to-back blocks not flagging a false conflict). These were the most valuable suggestions because edge cases are easy to overlook when you wrote the code yourself.
- **Documentation** — AI drafted the NumPy-style docstrings for algorithmic methods, which were then reviewed and adjusted to match the actual behavior and include accurate complexity notes.

The most effective prompt pattern was: *"Given this specific method and its docstring, what are the edge cases a test suite should cover?"* This kept the AI focused on a narrow, well-defined task and produced directly usable output.

**b. Judgment and verification**

One AI suggestion was modified before use: when asked to implement `detect_conflicts`, the AI initially suggested raising a `ValueError` when a conflict was found. This was changed to returning a list of warning strings instead.

The reasoning: raising an exception on a conflict would crash `Scheduler.plan()` and prevent the `DailyPlan` from being returned at all. In a Streamlit app where the user is building their schedule interactively, that would mean the entire schedule disappears the moment any two tasks overlap — even if the user only wants to see the warning and decide what to do. A warning list separates detection from enforcement: the plan still renders, the conflict is visible at the top of the schedule, and the owner can decide whether to fix it. The AI's version was technically correct; this version was more appropriate for the actual use case.

Verification: a dedicated test (`test_detect_conflicts_no_false_positives`) confirmed that the warning-based approach also does not over-report — sequential blocks that share a boundary are not flagged.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers 15 behaviors across five categories:

| Category | Tests | Why important |
|----------|-------|---------------|
| Basic class behavior | `mark_complete` flips flag; `add_task` grows list | Foundation — if these break, everything else is suspect |
| Sorting | Chronological order; `None` times sink last | Incorrect sort would display the schedule in the wrong order |
| Recurrence | Daily (+1 day), weekly (+7 days), as-needed (None) | Missed recurrence means a pet's routine permanently disappears |
| Conflict detection | Overlap flagged; sequential blocks not flagged | False negatives hide real double-bookings; false positives break valid schedules |
| Scheduler logic | Empty pet plan; budget overflow skip; validation guards | Edge cases that are silent in normal use but cause confusing behavior when hit |

**b. Confidence**

★★★★☆ (4 / 5)

All 15 unit tests pass. The core logic — priority sorting, greedy packing, conflict detection, and recurrence — is exercised by at least one happy-path and one edge-case test each.

The remaining 1-star gap: the Streamlit UI layer (`app.py`) is not covered by automated tests. The `session_state` persistence pattern, the mark-complete UI interaction, and the filter radio button all require a browser-level test (Playwright or Streamlit `AppTest`) to verify end-to-end. If given more time, those would be the next tests to write.

---

## 5. Reflection

**a. What went well**

The class hierarchy held up without redesign through all five phases. The initial decision to make `Scheduler` stateless (no stored state, just `plan()` taking parameters) made testing trivial — every test can create a fresh `Scheduler()` with no setup overhead. The `ScheduledBlock.reasons` list, which was added during the initial design, turned out to be exactly what the UI needed to explain each placement, with no retrofitting required.

**b. What you would improve**

`Owner.preferences` is a plain `dict` that is never read by the scheduler. In a next iteration this would be replaced with a typed `Preferences` dataclass containing fields like `earliest_start_time: time` and `preferred_priority_cutoff: str`. That would let the scheduler actually apply owner preferences to the plan instead of just carrying them as inert data.

The greedy scheduler also does not handle the case where a task has a `due_date` of today — those tasks are not prioritized above other pending tasks. Adding a "due today" boost to the priority sort would make recurring tasks feel more integrated with the scheduling logic.

**c. Key takeaway**

The most important thing learned: **AI is most valuable when you already have a clear structure to fill in, not when you are trying to generate structure from scratch.**

When the classes were well-defined stubs with docstrings, asking AI to implement a single method produced immediately usable code. When the problem was open-ended ("design a scheduling system"), AI suggestions required significant filtering and judgment before any of them could be used. The lead-architect role is not about writing every line — it is about defining the contracts (class names, method signatures, expected behavior) clearly enough that both AI tools and future contributors can fill them in correctly. The discipline of writing class stubs and docstrings first, then implementing, made every subsequent AI interaction faster and more reliable.
