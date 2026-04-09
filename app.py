"""app.py — PawPal+ Streamlit UI, connected to pawpal_system.py."""

# ── Step 1: Import classes from the logic layer ───────────────────────────
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="*", layout="centered")
st.title("PawPal+")

# ── Step 2: Session-state "vault" — create objects once, persist forever ──
#
# Streamlit reruns the whole script on every interaction.
# We check whether the key already exists in st.session_state before
# creating a new object, so data is never wiped on a re-run.

if "owner" not in st.session_state:
    st.session_state.owner = None          # set properly when the form is submitted

if "pet" not in st.session_state:
    st.session_state.pet = None

# ── Owner & Pet setup form ────────────────────────────────────────────────
st.subheader("1. Owner & Pet Setup")

with st.form("setup_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name   = st.text_input("Pet name",   value="Mochi")
    species    = st.selectbox("Species", ["dog", "cat", "other"])
    submitted  = st.form_submit_button("Save owner & pet")

if submitted:
    # Build real domain objects and store them in the vault
    owner = Owner(name=owner_name)
    pet   = Pet(name=pet_name, species=species)
    owner.pets.append(pet)

    st.session_state.owner = owner
    st.session_state.pet   = pet
    st.success(f"Saved: {owner_name} owns {pet_name} ({species})")

# Show current owner/pet if already set
if st.session_state.owner:
    st.caption(
        f"Active: **{st.session_state.owner.name}** / "
        f"**{st.session_state.pet.name}** ({st.session_state.pet.species})"
    )

st.divider()

# ── Step 3: Wire "Add Task" to Pet.add_task() ─────────────────────────────
st.subheader("2. Add Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    if st.session_state.pet is None:
        st.warning("Save an owner & pet first (Step 1).")
    else:
        try:
            # ── Bridge: hand data from the UI straight to Pet.add_task() ──
            new_task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
            )
            st.session_state.pet.add_task(new_task)   # validate + append
            st.success(f"Added task: '{task_title}'")
        except ValueError as exc:
            st.error(f"Invalid task: {exc}")

# Display current task list pulled from the Pet object (single source of truth)
if st.session_state.pet and st.session_state.pet.tasks:
    st.write("Current tasks for", st.session_state.pet.name)
    st.table(
        [
            {
                "Title":    t.title,
                "Minutes":  t.duration_minutes,
                "Priority": t.priority,
                "Done":     t.completed,
            }
            for t in st.session_state.pet.tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ── Build Schedule ────────────────────────────────────────────────────────
st.subheader("3. Build Schedule")

available_minutes = st.number_input(
    "How many minutes do you have today?",
    min_value=5, max_value=480, value=60
)

if st.button("Generate schedule"):
    if st.session_state.pet is None:
        st.warning("Save an owner & pet first (Step 1).")
    elif not st.session_state.pet.pending_tasks():
        st.warning("Add at least one task before scheduling.")
    else:
        # ── Bridge: call Scheduler.plan() with live domain objects ────────
        scheduler = Scheduler()
        plan = scheduler.plan(
            owner=st.session_state.owner,
            pet=st.session_state.pet,
            tasks=st.session_state.pet.pending_tasks(),
            available_minutes=int(available_minutes),
        )

        st.success(
            f"Scheduled {len(plan.blocks)} task(s) — "
            f"{plan.total_scheduled_minutes()} min total."
        )

        # Display each block
        for block in plan.blocks:
            start = block.start_time.strftime("%I:%M %p")
            end   = block.end_time.strftime("%I:%M %p")
            with st.container(border=True):
                st.markdown(f"**{block.task.title}** &nbsp; {start} -> {end}")
                for reason in block.reasons:
                    st.caption(f"- {reason}")

        # Display any skip notes
        if plan.notes:
            st.warning("Skipped tasks:")
            for note in plan.notes:
                st.caption(f"- {note}")
