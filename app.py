"""app.py — PawPal+ Streamlit UI, connected to pawpal_system.py."""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="*", layout="centered")
st.title("PawPal+")
st.caption("A smart daily care planner for your pet.")

# ---------------------------------------------------------------------------
# Session-state vault — objects survive Streamlit reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

# ---------------------------------------------------------------------------
# Section 1 — Owner & Pet Setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner & Pet Setup")

with st.form("setup_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name   = st.text_input("Pet name",   value="Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "other"])
    submitted  = st.form_submit_button("Save owner & pet")

if submitted:
    owner = Owner(name=owner_name)
    pet   = Pet(name=pet_name, species=species)
    owner.pets.append(pet)
    st.session_state.owner     = owner
    st.session_state.pet       = pet
    st.session_state.last_plan = None   # reset plan when profile changes
    st.success(f"Saved: {owner_name} owns {pet_name} ({species})")

if st.session_state.owner:
    st.caption(
        f"Active: **{st.session_state.owner.name}** / "
        f"**{st.session_state.pet.name}** ({st.session_state.pet.species})"
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add Tasks
# ---------------------------------------------------------------------------
st.subheader("2. Add Tasks")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

if st.button("Add task"):
    if st.session_state.pet is None:
        st.warning("Save an owner & pet first (Step 1).")
    else:
        try:
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
            )
            st.session_state.pet.add_task(new_task)
            st.success(f"Added: '{task_title}' ({priority} priority, {frequency})")
        except ValueError as exc:
            st.error(f"Invalid task: {exc}")

# Task table — live view of the Pet object
if st.session_state.pet and st.session_state.pet.tasks:
    pet = st.session_state.pet
    pending = pet.pending_tasks()
    done    = [t for t in pet.tasks if t.completed]

    st.write(f"Tasks for **{pet.name}** — {len(pending)} pending, {len(done)} done")
    st.table(
        [
            {
                "Title":     t.title,
                "Min":       t.duration_minutes,
                "Priority":  t.priority,
                "Frequency": t.frequency,
                "Done":      "Yes" if t.completed else "No",
                "Due":       str(t.due_date) if t.due_date else "-",
            }
            for t in pet.tasks
        ]
    )

    # Mark-complete UI — pick a pending task to complete
    if pending:
        st.markdown("**Mark a task complete:**")
        task_to_complete = st.selectbox(
            "Select task", [t.title for t in pending], label_visibility="collapsed"
        )
        if st.button("Mark complete"):
            target = next(t for t in pending if t.title == task_to_complete)
            pet.mark_task_complete(target)
            follow_up = pet.tasks[-1] if not pet.tasks[-1].completed else None
            if follow_up and follow_up is not target:
                st.success(
                    f"'{target.title}' done! Next occurrence added — "
                    f"due {follow_up.due_date}."
                )
            else:
                st.success(f"'{target.title}' marked complete.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Build Schedule
# ---------------------------------------------------------------------------
st.subheader("3. Build Schedule")

available_minutes = st.number_input(
    "How many minutes do you have today?",
    min_value=5, max_value=480, value=60
)

if st.button("Generate schedule"):
    if st.session_state.pet is None:
        st.warning("Save an owner & pet first (Step 1).")
    elif not st.session_state.pet.pending_tasks():
        st.warning("Add at least one pending task before scheduling.")
    else:
        scheduler = Scheduler()
        plan = scheduler.plan(
            owner=st.session_state.owner,
            pet=st.session_state.pet,
            tasks=st.session_state.pet.pending_tasks(),
            available_minutes=int(available_minutes),
        )
        st.session_state.last_plan = plan

# Render the stored plan (persists across reruns)
plan = st.session_state.last_plan
if plan:
    pet = st.session_state.pet

    # ── Conflict warnings — shown at the top so they're impossible to miss ──
    if plan.conflicts:
        for warning in plan.conflicts:
            st.warning(f"Schedule conflict: {warning}")
    else:
        st.success(
            f"Schedule ready — {len(plan.blocks)} task(s), "
            f"{plan.total_scheduled_minutes()} min total. No conflicts."
        )

    # ── Sorted schedule blocks ────────────────────────────────────────────
    sorted_blocks = plan.sort_by_time()
    if sorted_blocks:
        st.markdown("#### Today's schedule (sorted by time)")
        for block in sorted_blocks:
            start = block.start_time.strftime("%I:%M %p")
            end   = block.end_time.strftime("%I:%M %p")

            # Color-code by priority
            if block.task.priority == "high":
                icon = "🔴"
            elif block.task.priority == "medium":
                icon = "🟡"
            else:
                icon = "🟢"

            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(
                        f"{icon} **{block.task.title}**  "
                        f"`{start}` → `{end}`"
                    )
                with col_b:
                    st.caption(f"{block.task.frequency}")
                for reason in block.reasons:
                    st.caption(f"- {reason}")

    # ── Skipped tasks ─────────────────────────────────────────────────────
    if plan.notes:
        with st.expander(f"Skipped tasks ({len(plan.notes)})", expanded=True):
            for note in plan.notes:
                st.caption(f"- {note}")

    # ── Filter panel ──────────────────────────────────────────────────────
    st.markdown("#### Filter schedule")
    show_filter = st.radio(
        "Show blocks for:", ["All", "Pending only", "Completed only"],
        horizontal=True, label_visibility="collapsed"
    )
    if show_filter == "Pending only":
        filtered = plan.filter_by_status(completed=False)
    elif show_filter == "Completed only":
        filtered = plan.filter_by_status(completed=True)
    else:
        filtered = plan.blocks

    if filtered:
        st.table(
            [
                {
                    "Task":     b.task.title,
                    "Start":    b.start_time.strftime("%I:%M %p") if b.start_time else "-",
                    "End":      b.end_time.strftime("%I:%M %p")   if b.end_time   else "-",
                    "Priority": b.task.priority,
                    "Done":     "Yes" if b.task.completed else "No",
                }
                for b in filtered
            ]
        )
    else:
        st.info("No blocks match the selected filter.")
