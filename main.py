"""main.py — Demo that exercises sorting, filtering, recurring tasks, and conflict detection."""

from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "=" * 54

# ── Setup ─────────────────────────────────────────────────────────────────
owner = Owner(name="Alex")

dog = Pet(name="Buddy", species="Dog")
cat = Pet(name="Whiskers", species="Cat")

# Tasks added deliberately OUT OF PRIORITY ORDER to show sorting
dog.add_task(Task("Bath time",      duration_minutes=45, priority="low",    frequency="weekly"))
dog.add_task(Task("Morning walk",   duration_minutes=30, priority="high"))
dog.add_task(Task("Feed breakfast", duration_minutes=10, priority="high"))

cat.add_task(Task("Brush fur",        duration_minutes=15, priority="low",    frequency="weekly"))
cat.add_task(Task("Playtime",         duration_minutes=20, priority="medium"))
cat.add_task(Task("Litter box clean", duration_minutes=10, priority="high"))

owner.pets.append(dog)
owner.pets.append(cat)

scheduler = Scheduler()

# ── Section 1: Sorting demo ───────────────────────────────────────────────
print(SEP)
print("  SECTION 1 - SORT BY PRIORITY THEN TIME")
print(SEP)

for pet in owner.pets:
    plan = scheduler.plan(owner, pet, pet.pending_tasks(), available_minutes=60)
    sorted_blocks = plan.sort_by_time()
    print(f"\n{pet.name} ({pet.species}) - sorted schedule:")
    for block in sorted_blocks:
        start = block.start_time.strftime("%I:%M %p")
        end   = block.end_time.strftime("%I:%M %p")
        print(f"  {start} -> {end}  [{block.task.priority:6}]  {block.task.title}")
    if plan.notes:
        for note in plan.notes:
            print(f"  ! {note}")

# ── Section 2: Filtering demo ─────────────────────────────────────────────
print()
print(SEP)
print("  SECTION 2 - FILTERING")
print(SEP)

# Build a combined plan for both pets so we can filter across them
all_tasks = owner.get_all_pending_tasks()
combined_plan = scheduler.plan(owner, dog, all_tasks, available_minutes=120)

print("\nFilter: only Buddy's blocks")
for b in combined_plan.filter_by_pet("Buddy"):
    print(f"  {b.task.title}")

print("\nFilter: incomplete tasks only (should be all of them)")
incomplete = combined_plan.filter_by_status(completed=False)
print(f"  {len(incomplete)} incomplete block(s) found")

# ── Section 3: Recurring task demo ───────────────────────────────────────
print()
print(SEP)
print("  SECTION 3 - RECURRING TASKS")
print(SEP)

walk = dog.tasks[1]   # "Morning walk" - daily
print(f"\nBefore completion: '{walk.title}' completed={walk.completed}")
print(f"Buddy's task count before: {len(dog.tasks)}")

dog.mark_task_complete(walk)

print(f"After completion:  '{walk.title}' completed={walk.completed}")
print(f"Buddy's task count after:  {len(dog.tasks)}  (follow-up appended)")
new_task = dog.tasks[-1]
print(f"New task: '{new_task.title}' due={new_task.due_date}  completed={new_task.completed}")

bath = dog.tasks[0]   # "Bath time" - weekly
dog.mark_task_complete(bath)
print(f"\nWeekly 'Bath time' completed -> follow-up due: {dog.tasks[-1].due_date}")

# ── Section 4: Conflict detection demo ───────────────────────────────────
print()
print(SEP)
print("  SECTION 4 - CONFLICT DETECTION")
print(SEP)

# Force two tasks with identical start times to trigger a conflict
from datetime import time
from pawpal_system import ScheduledBlock, DailyPlan, Task as T

conflict_plan = DailyPlan()
t1 = T("Vet appointment", 30, "high")
t2 = T("Grooming",        20, "high")

# Manually create blocks that start at the same time
from datetime import datetime, timedelta
start = time(9, 0)
dt = datetime.combine(datetime.today(), start)

conflict_plan.blocks.append(ScheduledBlock(
    task=t1, pet=dog,
    start_time=time(9, 0), end_time=time(9, 30),
    reasons=["manually placed"]
))
conflict_plan.blocks.append(ScheduledBlock(
    task=t2, pet=dog,
    start_time=time(9, 15), end_time=time(9, 35),   # overlaps with t1
    reasons=["manually placed"]
))

conflicts = scheduler.detect_conflicts(conflict_plan.blocks)
print()
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts found.")

# ── Section 5: All pending tasks summary ─────────────────────────────────
print()
print(SEP)
print("  ALL PENDING TASKS (after completions)")
print(SEP)
for task in owner.get_all_pending_tasks():
    due = f"  due {task.due_date}" if task.due_date else ""
    print(f"  [ ]  [{task.priority:6}]  {task.title} ({task.duration_minutes} min){due}")
print(SEP)
