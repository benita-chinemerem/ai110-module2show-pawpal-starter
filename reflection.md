# PawPal+ Project Reflection


## 1. System Design
PawPal+ supports three main things an owner does in the app:

1. **Profile** — Enter or update basic owner and pet information so plans have the right context.
2. **Tasks** — Add or edit care tasks (for example walks or feeding), including duration and priority.
3. **Plan** — Generate a daily schedule from available time and priorities, view it clearly, and read why the app ordered or skipped tasks.

---

**a. Initial design**

My initial UML centered on four domain types plus a scheduling service, matching how the app flows: profile (who), tasks (what), plan (output), and an engine that builds the plan.

- **Owner** — Stores the human’s **name** and **preferences** (for example quiet hours or preferred walk times once the scheduler uses them). In the diagram, an owner *owns* one or more pets.
- **Pet** — Stores the animal’s **name** and **species** so the plan and explanations can refer to the right pet.
- **Task** — One care item (**title**, **duration_minutes**, **priority**). Tasks are what get sorted and packed into the day. **validate()** will enforce sensible inputs (for example positive duration) before scheduling.
- **DailyPlan** — The result of planning: **blocks** (ordered placements) and **notes** for anything that did not fit or needs a global explanation. **total_scheduled_minutes()** will sum scheduled time for checks and display.
- **ScheduledBlock** — One row of the plan: the **Task**, optional **start_time** / **end_time**, and **reasons** (short strings) so the UI can explain *why* something was placed or ordered as it was. This type is not a separate box on my four-class sketch but it implements the “each block references a Task” part of **DailyPlan**.
- **Scheduler** — Stateless service with **plan(owner, pet, tasks, available_minutes)** that reads context and returns a **DailyPlan**. Time available for the day is a parameter here so **Owner** / **Pet** stay about identity, not “today’s minutes.”

Associations in the model: **Owner → Pet** (owns), **Pet → Task** (the pet’s care needs; in the app the task list is often passed into **plan** alongside **Pet** so Streamlit can keep a simple list). **DailyPlan** references **Task** through each **ScheduledBlock**.

**b. Design changes**

Yes. After reviewing `pawpal_system.py`
, I made one structural tweak and noted a few items for later.

- **Change:** Added **`pets: list[Pet]`** on **Owner** (with `default_factory=list`) so the code matches the UML **“Owner owns Pet(s)”** relationship instead of only having two disconnected datatypes. The UI can append the current **Pet** when the user saves profile data, which keeps the object graph aligned with the diagram.
- **Not changed (intentionally):** Tasks are still passed as **`tasks: list[Task]`** into **`Scheduler.plan`** rather than embedded only on **Pet**, so the Streamlit session can keep one flat task list without duplicating storage; the **Pet** instance remains the contextual “who this plan is for.”
- **Future / bottleneck note (no code change yet):** Putting sorting, packing, time arithmetic, and explanation strings all in **`Scheduler.plan`** could get large; if it does, I may split a small helper (for example building **reasons** or sorting keys) into private methods or a separate module. **`preferences: dict`** is flexible but untyped until I know exactly which keys the scheduler reads.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

**Tradeoff: overlap detection checks every pair of blocks (O(n²)) instead of a sorted sweep.**

`detect_conflicts` compares every pair of blocks with a nested loop. A more efficient approach would sort blocks by start time first and then only compare each block against its immediate neighbors — reducing work from O(n²) to O(n log n). The nested-loop version was kept because a typical daily pet care plan has fewer than 20 tasks: at that scale the two approaches are indistinguishable in speed, and the pair-comparison logic (`a.start < b.end AND b.start < a.end`) reads almost like plain English, making it easy to verify correctness at a glance. The tradeoff is reasonable here because clarity and correctness matter more than micro-performance for a small personal scheduling app. If the scheduler were extended to handle dozens of pets or bulk-import hundreds of tasks, switching to a sweep-line algorithm would be worth the added complexity.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
