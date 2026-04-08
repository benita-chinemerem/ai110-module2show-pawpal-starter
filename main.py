"""main.py — Demo / testing ground for pawpal_system.py."""

from pawpal_system import Owner, Pet, Task, Scheduler

# ── 1. Create the owner ───────────────────────────────────────────────────
owner = Owner(name="Alex")

# ── 2. Create two pets ────────────────────────────────────────────────────
dog = Pet(name="Buddy", species="Dog")
cat = Pet(name="Whiskers", species="Cat")

# ── 3. Add tasks to Buddy (dog) ───────────────────────────────────────────
dog.add_task(Task(title="Morning walk",  duration_minutes=30, priority="high"))
dog.add_task(Task(title="Feed breakfast", duration_minutes=10, priority="high"))
dog.add_task(Task(title="Bath time",     duration_minutes=45, priority="low"))

# ── 4. Add tasks to Whiskers (cat) ────────────────────────────────────────
cat.add_task(Task(title="Litter box clean", duration_minutes=10, priority="high",  frequency="daily"))
cat.add_task(Task(title="Playtime",         duration_minutes=20, priority="medium", frequency="daily"))
cat.add_task(Task(title="Brush fur",        duration_minutes=15, priority="low",    frequency="weekly"))

# ── 5. Register pets with the owner ──────────────────────────────────────
owner.pets.append(dog)
owner.pets.append(cat)

# ── 6. Schedule each pet ─────────────────────────────────────────────────
scheduler = Scheduler()
available_minutes = 60   # owner has 60 min free today

print("=" * 52)
print("          PAWPAL+ - TODAY'S SCHEDULE")
print(f"          Owner : {owner.name}")
print(f"          Budget: {available_minutes} min")
print("=" * 52)

for pet in owner.pets:
    plan = scheduler.plan(owner, pet, pet.pending_tasks(), available_minutes)

    print(f"\n--- {pet.name} ({pet.species}) ---")

    if plan.blocks:
        for block in plan.blocks:
            start = block.start_time.strftime("%I:%M %p")
            end   = block.end_time.strftime("%I:%M %p")
            print(f"  {start} -> {end}  |  {block.task.title}")
            for reason in block.reasons:
                print(f"                     - {reason}")
    else:
        print("  (no tasks scheduled)")

    if plan.notes:
        print("  Skipped / Notes:")
        for note in plan.notes:
            print(f"    ! {note}")

    print(f"  Total scheduled: {plan.total_scheduled_minutes()} min")

print("\n" + "=" * 52)
print("  All pending tasks across all pets:")
for task in owner.get_all_pending_tasks():
    status = "[done]" if task.completed else "[ ]"
    print(f"  {status}  [{task.priority:6}]  {task.title} ({task.duration_minutes} min)")
print("=" * 52)
