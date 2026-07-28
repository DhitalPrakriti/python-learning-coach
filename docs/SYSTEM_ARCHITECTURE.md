# Python Learning Coach — System Architecture

Complete technical reference for the Python Learning Coach: a multi-agent Python
tutor built on Flask and Google Gemini.

- **Repository:** `DhitalPrakriti/python-learning-coach`
- **Branch:** `main` (commit `72192d6`)
- **Stack:** Python 3.11 · Flask 3 · `google-genai` 2.x · Gemini 2.5 · Cloud Run
- **Scale:** ~1,650 lines of application code, 49 tests
- **Document date:** 28 July 2026

### How to read this document

Part I explains what the system is and how it is shaped. Part II is a
module-by-module reference. Part III documents each subsystem in depth. Part IV
covers operations. The appendices are lookup tables.

Every table, signature, and schema in this document was extracted from the
running code, not written from memory.

---

# Part I — Overview

## 1. What the system does

A learner sends a message. The system decides which of five specialist agents
should answer, gives that agent the conversation so far plus what it knows about
the learner, and returns the answer along with updated learner state.

It is deliberately **not** a general chatbot. Each agent has one job, a narrow
toolset, and its own prompt:

| Agent | Responsibility | Typical trigger |
| --- | --- | --- |
| **Assessment** | Determine skill level and learning style | "assess me", a bare greeting |
| **Curriculum** | Build a multi-week roadmap | "give me a plan" |
| **Teaching** | Explain one concept with analogy and examples | "explain loops" |
| **Practice** | Set an exercise, withhold the solution | "give me an exercise" |
| **Progress** | Report actual work done, award badges | "show my progress" |

## 2. Design philosophy

Three decisions shape everything else.

### Domain knowledge lives in Python, not in prompts

Each agent's subject-matter content is an ordinary Python function returning a
dictionary. `teach_python_concept("loops")` is a dictionary lookup that returns
an explanation, an analogy, code examples, and common mistakes. The model's job
is to *call the function and narrate the result*, not to be the source of truth.

This buys three things: content is reviewable in code review, it is unit
testable, and — most importantly — it still works with no model at all, which is
what makes local mode possible.

### The model is a renderer, the coordinator is the authority

Learner state (level, topics, counters) is computed by the coordinator from
observable facts. The model never decides what the learner has accomplished. The
one exception is the assessed skill level, and even there the agent must emit a
machine-readable marker line rather than have its prose interpreted.

### Every failure has a defined answer

There is no code path where the learner gets nothing. If Gemini is unavailable,
the same tool functions serve deterministic content, and the response says why it
degraded. This is a product decision as much as an engineering one: a tutor that
says "I can't help right now" has failed at its only job.

## 3. Architecture at a glance

```
                          ┌──────────────────────────────┐
                          │  Browser                     │
                          │  templates/index.html        │
                          │  static/app.js  (chat state, │
                          │      context panel, banner)  │
                          └──────────────┬───────────────┘
                                         │ POST /chat {message, user_id}
                                         ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  main.py — Flask application                                           │
  │                                                                        │
  │   validate (400 empty / 413 too long)                                  │
  │             │                                                          │
  │             ▼                                                          │
  │   determine_agent(message, user_id) ─── pure function, no I/O           │
  │      INTENT_KEYWORDS · SIMPLIFY_SIGNALS · HELP_SIGNALS · GREETING_TERMS │
  └─────────────────────────────┬──────────────────────────────────────────┘
                                │ agent name
                                ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  agents/coordinator.py — LearningCoachCoordinator                      │
  │                                                                        │
  │   ┌───────────────┐   ┌──────────────────┐   ┌──────────────────────┐  │
  │   │ learner       │   │ retry policy     │   │ circuit breaker      │  │
  │   │ memory        │   │ + retry hints    │   │ (quota / auth)       │  │
  │   └───────┬───────┘   └────────┬─────────┘   └──────────┬───────────┘  │
  │           │                    │                        │              │
  │           └────────────┬───────┴────────────────────────┘              │
  │                        ▼                                               │
  │            history (8 turns) + profile note                            │
  └────────────────────────┬───────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
  ┌───────────────────────┐   ┌──────────────────────────────┐
  │ agents/base_agent.py  │   │  _local_fallback()           │
  │ BaseGenAIAgent.query  │   │  deterministic content from  │
  │  · build_contents     │   │  the same tool functions     │
  │  · model fallback     │   │  source = local | fallback   │
  │  · classify_error     │   └──────────────────────────────┘
  └───────────┬───────────┘
              ▼
  ┌───────────────────────────────────────────────┐
  │  Gemini API  (models.generate_content)        │
  │  Automatic Function Calling, max 4 hops       │
  │                                               │
  │  tool functions execute LOCALLY in-process:   │
  │   teach_python_concept, generate_python_…      │
  └───────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────┐
  │  storage/firestore_store.py  (optional)       │
  │  users/{user_id}  ← best-effort persistence   │
  └───────────────────────────────────────────────┘
```

### Layer responsibilities

| Layer | Owns | Does not know about |
| --- | --- | --- |
| `main.py` | HTTP, validation, routing decision | Gemini, retries, memory internals |
| `coordinator.py` | Learner memory, retry policy, fallback | How an API call is constructed |
| `base_agent.py` | One API call, error classification, model choice | Learners, routing, persistence |
| `*_agent.py` | Subject-matter content and tool wiring | HTTP, retries, memory |
| `firestore_store.py` | Serialising context | Everything else |

The dependency direction is strictly downward. `base_agent.py` imports nothing
from the coordinator, which is why the retry tests can drive it with a fake.

---

# Part II — Module reference

## 4. File inventory

### Application code

| File | Lines | Responsibility |
| --- | --- | --- |
| `main.py` | 312 | Flask app, 6 routes, the intent router |
| `agents/coordinator.py` | 728 | Orchestration, memory, retry policy, local fallback |
| `agents/base_agent.py` | 207 | Gemini call layer, error taxonomy, model fallback |
| `agents/prompts.py` | 92 | All five system instructions |
| `agents/teaching_agent.py` | 149 | Lesson content + teaching agent |
| `agents/practice_agent.py` | 157 | Exercise bank + practice agent |
| `agents/progress_agent.py` | 150 | Progress analytics + progress agent |
| `agents/assessment_agent.py` | 108 | Level detection + assessment agent |
| `agents/curriculum_agent.py` | 98 | Roadmaps + curriculum agent |
| `config/settings.py` | 81 | All environment configuration |
| `api/google_client.py` | 39 | Standalone Gemini helper for scripts |
| `storage/firestore_store.py` | 33 | Optional persistence |

### Frontend

| File | Responsibility |
| --- | --- |
| `templates/index.html` | Three-panel shell: profile, chat, session inspector |
| `static/app.js` | Chat state, `localStorage` history, context rendering, degraded banner |
| `static/styles.css` | Grid layout, panels, message bubbles, banner |

### Tests

| File | Lines | Contents |
| --- | --- | --- |
| `tests/test_app_local.py` | 260 | 4 suites: endpoints, router, context tracking, fallbacks |
| `tests/test_error_handling.py` | 226 | 5 suites: error classification, contents, retry policy, prompt wiring, migration |

### Operational scripts

| File | Purpose |
| --- | --- |
| `agent_health_check.py` | Drives a running instance, verifies routing per agent |
| `client.py` | Interactive terminal chat client |
| `auto_demo.py` | Scripted demo conversation |
| `list_models.py` | Enumerate models the credentials can reach |
| `check_models.py` | Probe specific models for availability |
| `diagnostics_import_check.py` | Import/path troubleshooting |
| `tools/md_to_docx.py` | Render these docs to Word |

### Deployment

| File | Purpose |
| --- | --- |
| `Dockerfile` | `python:3.11-slim`, non-root, gunicorn |
| `deploy.sh` | Cloud Build → Artifact Registry → Cloud Run |
| `.agent_engine_config.json` | Instance and resource limits |
| `.github/workflows/docker-image.yml` | Build image on push/PR to `main` |

## 5. Class reference

### `BaseGenAIAgent` — `agents/base_agent.py`

The shared body of all five agents. Subclasses set only three attributes.

```python
class BaseGenAIAgent:
    name: str                      # "teaching"
    tools: Sequence[Callable]       # [teach_python_concept]
    system_instruction: str         # AGENT_PROMPTS["teaching"]

    def __init__(self, client: genai.Client, model_id: Optional[str] = None)
    def query(self, message: str,
              history: Optional[Sequence[dict]] = None,
              profile_note: str = "") -> str        # raises AgentCallError
```

Instance state: `model_id`, `fallback_models`, and `last_model_used` — set after
a successful call so the coordinator can report which model actually answered.

### `AgentCallError` — `agents/base_agent.py`

```python
class AgentCallError(RuntimeError):
    kind: str                # quota_exhausted | rate_limit | auth_error | ...
    retry_after: float|None  # parsed from the server's retryDelay
    retryable: bool          # property — is a retry capable of helping?
    try_other_model: bool    # property — might a different model succeed?
```

Carrying a machine-readable `kind` is the point. The original code returned
`"Agent Error: …"` strings, so the caller had to parse prose to decide what to
do — and therefore retried errors that no retry could fix.

### `LearningCoachCoordinator` — `agents/coordinator.py`

| Group | Methods |
| --- | --- |
| Lifecycle | `initialize_agents` |
| Memory | `get_user_context`, `update_context`, `reset_user_context`, `get_public_context`, `_normalize_context`, `_save_context`, `_append_history` |
| Derivation | `_extract_topic`, `_parse_skill_level`, `_profile_note`, `_history_for_model`, `_record_response_context` |
| Execution | `process_with_agent` (async), `_rewrite_message` |
| Resilience | `_breaker_open`, `_note_failure`, `_note_success`, `health_snapshot`, `_degraded_notice` |
| Fallback | `_local_fallback`, `_pick_difficulty` |

Instance state: `client`, `agents`, `user_contexts`, `store`, `mode`,
`model_id`, `fallback_models`, `last_error`, `_consecutive_hard_failures`,
`_breaker_open_until`.

### `FirestoreStore` — `storage/firestore_store.py`

```python
class FirestoreStore:
    def get_user_context(self, user_id: str) -> Dict[str, Any] | None
    def save_user_context(self, user_id: str, context: Dict[str, Any]) -> None
```

Writes to `users/{user_id}` with `merge=True`, truncating history to 50 turns.
Import failure raises at construction, which the coordinator catches — so a
missing dependency disables persistence instead of breaking startup.

---

# Part III — Subsystems

## 6. Tool function catalog

These ten functions are the system's actual knowledge. Gemini's Automatic
Function Calling executes them **in-process** — no separate tool server. The same
functions serve local mode directly.

### Assessment tools

```python
assess_learning_profile(experience: str,
                        learning_style: str = "adaptive",
                        subject: str = "python") -> dict
```
Returns `experience_level`, `learning_style`, `subject`, `recommended_pace`,
`learning_depth`, `assessment_score` (1–3), `recommended_topics` (4),
`next_steps`.

```python
analyze_student_input(student_input: str) -> dict
```
Returns `detected_experience`, `detected_learning_style`, `analysis_complete`.
Keyword heuristics: `expert|advanced|senior|years of` → advanced;
`intermediate|some experience|basic knowledge` → intermediate; else beginner.

```python
assess_with_code_sample(code_sample: str) -> dict
```
Returns `assessed_level`, `code_complexity`, `has_code_sample`. Counts markers:
≥2 advanced indicators (`async def`, `yield`, `@`, `lambda`) → advanced;
≥3 intermediate (`def`, `class`, `import`, `self.`) → intermediate.

### Curriculum tool

```python
generate_python_curriculum(experience_level: str,
                           learning_goals: str = "general Python proficiency",
                           focus_areas: str = None) -> dict
```
Returns `curriculum_title`, `description`, `experience_level`, `learning_goals`,
`focus_areas`, `weekly_plan`, `recommended_resources`, `recommended_pace`,
`key_milestones`. Each `weekly_plan` entry: `{week, topic, lessons, practice}`.

### Teaching tool

```python
teach_python_concept(topic: str,
                     level: str = "beginner",
                     learning_style: str = "adaptive") -> dict
```
Returns 13 keys: `topic`, `level`, `learning_style`, `explanation`,
`code_examples`, `real_world_analogy`, `common_mistakes`, `practice_exercise`,
`level_guidance`, `style_suggestion`, `next_steps`, `key_takeaways`,
`additional_resources`.

### Practice tool

```python
generate_python_exercise(topic: str,
                         level: str = "beginner",
                         difficulty: str = "easy") -> dict
```
Returns 11 keys including `problem_statement`, `hints`, `solution_code`,
`test_cases`, `success_criteria`, `estimated_time`, `bonus_challenges`.

The prompt instructs the agent not to reveal `solution_code` until the learner
has attempted the problem. **This is a prompt-level constraint, not enforced in
code** — see §19.

### Progress tools

```python
track_learning_progress(user_id, topics_learned: str, exercises_completed: int,
                        current_level: str, goals: str = "...") -> dict
```
Returns `user_id`, `date`, `metrics{topics, exercises, level, progress}`,
`gamification{achievement, badge, velocity}`,
`insights{strengths, recommendations, next_topics}`.

```python
generate_progress_report(user_id, topics_learned: str,
                         exercises_completed: int, days_active: int = 7) -> dict
```
Returns `report_date`, `summary{topics_count, exercises_total, days_active,
avg_daily}`, `analysis{pace, milestone_status, topics_covered}`.

```python
suggest_next_steps(current_level: str, topics_mastered: str) -> dict
```
Returns `level`, `pathway{focus, steps, resources}`, `skill_gaps`, `motivation`.

Note that these tools take `topics_learned` as a **comma-separated string**, not
a list — a Gemini function-declaration constraint that the coordinator satisfies
by joining before the call.

### Badge thresholds

Driven solely by `exercises_completed`:

| Exercises | Badge | Achievement | Velocity |
| --- | --- | --- | --- |
| 0–4 | 🌱 Python Starter | Beginner | Getting started. |
| 5–9 | 🎯 Python Learner | Intermediate | Steady progress. |
| 10–14 | ⭐ Python Pro | Advanced | Fast learner! |
| 15+ | 🏆 Python Master | Expert | Fast learner! |

`progress` percentage is `min(exercises_completed / 20 × 100, 100)`.

## 7. Content inventory

How much material is actually authored — worth knowing, because the gap is
filled by generic placeholders:

| Content | Coverage |
| --- | --- |
| Teaching lessons | **7 topics**: variables, functions, loops, lists, dictionaries, classes, conditionals |
| Exercises | **5 topics × 3 difficulties = 15**: variables, functions, loops, lists, dictionaries |
| Curricula | **3**: beginner (6 weeks), intermediate (8 weeks), advanced (6 weeks) |
| Recognised topics (`TOPIC_ALIASES`) | **13** |
| Declared topics (`CORE_PYTHON_TOPICS`) | **15** |

The asymmetry matters. The router and topic tracker recognise 13 topics, but only
7 have authored lessons and 5 have exercises. Asking about tuples or inheritance
is recognised and tracked, then answered from a generic template. In live mode
the model compensates; **in local mode there is nothing to compensate**, so the
learner gets a placeholder. Closing this gap is the highest-value content work.

## 8. Request lifecycle

```
Browser                main.py            Coordinator        BaseGenAIAgent      Gemini
   │                      │                    │                   │               │
   │─ POST /chat ────────►│                    │                   │               │
   │                      │                    │                   │               │
   │                 ┌────┴────┐               │                   │               │
   │                 │validate │ 400 empty     │                   │               │
   │                 │         │ 413 too long  │                   │               │
   │                 └────┬────┘               │                   │               │
   │                      │                    │                   │               │
   │              determine_agent()            │                   │               │
   │                      │                    │                   │               │
   │                      │─ process_with_agent(agent, msg, uid) ──►│               │
   │                      │                    │                   │               │
   │                      │            get_user_context ────────────┼──► Firestore  │
   │                      │            append user turn             │    (optional) │
   │                      │            _rewrite_message             │               │
   │                      │            _profile_note                │               │
   │                      │            _history_for_model           │               │
   │                      │                    │                   │               │
   │                      │                    │── query(msg, history, profile) ───►│
   │                      │                    │                   │               │
   │                      │                    │                   │─ generate ───►│
   │                      │                    │                   │  ◄─ tool call │
   │                      │                    │                   │  (executes    │
   │                      │                    │                   │   locally)    │
   │                      │                    │                   │─ result ─────►│
   │                      │                    │◄── narrated text ─┤◄── text ──────┤
   │                      │                    │                   │               │
   │                      │            _record_response_context     │               │
   │                      │              · skill level              │               │
   │                      │              · topics, counters         │               │
   │                      │              · append coach turn        │               │
   │                      │◄── response text ──┤                   │               │
   │◄── JSON ─────────────┤                    │                   │               │
```

On failure the `query` step raises `AgentCallError`; the coordinator applies the
retry matrix (§12) and, if nothing works, substitutes `_local_fallback` output
with `source = "fallback"`.

### Runtime modes

Resolved once at startup by `initialize_agents()`:

| Mode | Condition | Client | Agents |
| --- | --- | --- | --- |
| `local` | `LOCAL_ONLY=1`, or no credentials | none | five `None` placeholders |
| `vertex_ai` | `GOOGLE_GENAI_USE_VERTEXAI=1` | `genai.Client(vertexai=True, …)` | five live agents |
| `gemini_api_key` | `GEMINI_API_KEY` set | `genai.Client(api_key=…)` | five live agents |

**Vertex is checked before the API key.** A developer's stale `GEMINI_API_KEY`
in `.env` must not silently override a Cloud Run deployment that is meant to use
workload identity. `api/google_client.py` follows the same precedence so the two
entry points cannot disagree.

Local mode keeps all five dictionary keys so routing, `/health`, and `/status`
behave identically to live mode — which is why the test suite can exercise the
whole HTTP surface with no credentials.

## 9. The routing subsystem

`determine_agent(message, user_id)` is a pure function of the message and the
learner's stored context. No I/O, which is why all 12 router tests are instant.

### Rule order

```
1. SIMPLIFY_SIGNALS present?           → teaching
2. INTENT_KEYWORDS match?              → practice | curriculum | progress
                                         | teaching | assessment   (table order)
3. HELP_SIGNALS present?               → teaching
4. Message is only a greeting?         → assessment
5. "start/begin/learn" + "python"?     → curriculum
6. skill_level unknown AND turns < 4?  → assessment
7. turns < 6 ? teaching : practice
```

### Keyword tables

Evaluated in this order; first agent with a hit wins.

| Agent | Terms |
| --- | --- |
| **practice** (9) | practice, exercise, exercises, challenge, challenges, quiz, problem set, give me a task, drill |
| **curriculum** (9) | plan, roadmap, curriculum, syllabus, learning path, study path, schedule, week plan, weekly plan |
| **progress** (8) | progress, badge, badges, achievement, achievements, report, how am i doing, streak |
| **teaching** (25) | explain, explanation, teach, tutorial, what is, what are, how do i, how to, define, definition, meaning, basics, fundamentals, difference between, example of, show me how, what topic, which topic, what were we, what did we, what have we, what was i, remind me, recap, so far |
| **assessment** (8) | assess, assessment, evaluate, my level, skill level, test me, where do i stand, how good am i |

### Matching algorithm

```python
def _contains_term(msg: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", msg) is not None
```

Word-boundary matching on **both** sides. This is load-bearing:

| Message | Naive substring | Correct |
| --- | --- | --- |
| "give me an **explanation**" | curriculum — `"explanation"` ⊃ `"plan"` | teaching |
| "I want to multi**task**" | practice — `"multitask"` ⊃ `"task"` | teaching |

### Greeting detection

`is_greeting_only()` strips every greeting term, then every word in
`GREETING_FILLER` (33 words: *there, coach, python, please, thanks, how, are,
you…*). If nothing remains, the message was a bare greeting.

This exists because rule ordering alone is not enough. "hello, give me a practice
exercise on loops" contains a greeting *and* a request; checking greetings first
answered it with an assessment and silently discarded the request. Now greetings
are checked at rule 4, after explicit requests at rule 2.

### Why rule 6 is gated on turn count

An unknown skill level used to route *every* unmatched message to assessment. A
learner who never described themselves therefore got assessment after assessment.
The `turns < 4` gate bounds onboarding to the start of a session.

### Known limits

This is a keyword router, not an intent classifier:

- **No negation handling.** "I *don't* want practice" routes to practice.
- **Ambiguity resolves by table order**, not by emphasis. "explain loops then
  give me an exercise" routes to practice, because practice is checked first.
- **No confidence signal.** The router cannot say "I'm unsure", so it cannot ask.

The 12 router tests pin current behaviour precisely enough that swapping in a
classifier — or a cheap model call for routing — is a contained change.

## 10. Learner memory

### Schema

In `coordinator.user_contexts[user_id]`, optionally mirrored to Firestore:

```python
{
  "skill_level":    "unknown" | "beginner" | "intermediate" | "advanced",
  "learning_style": "adaptive" | "visual" | "auditory" | "kinesthetic",

  "history": [                       # both sides, capped at 50 turns
      {"role": "user" | "coach", "text": str, "agent": str}
  ],

  "last_agent":    str,              # which specialist answered last
  "last_topic":    str,              # anchors "explain that again"
  "last_exercise": str,              # open exercise, ≤1200 chars, for "I'm stuck"
  "last_model":    str,              # which model actually answered
  "last_response_source": "gemini" | "local" | "fallback",

  "progress": {
      "topics_learned":      [str],
      "exercises_delivered": int,    # handed out
      "exercises_completed": int,    # learner said they finished
      "interactions":        int,
  },
}
```

`get_public_context()` projects a UI-safe subset — notably dropping
`last_exercise`, so answer text is never echoed into the context payload.

### What the model receives

Two things, assembled per call:

1. **`history`** — the last 8 exchanges, converted by `build_contents()` into
   alternating `types.Content` turns with `role` mapped `coach → model`. Each
   turn is truncated to 4,000 characters.
2. **`profile_note`** — a rendered summary appended to the system instruction:

```
Learner profile:
- Assessed skill level: beginner
- Learning style: adaptive
- Topics studied so far: loops, functions
- Exercises delivered: 2
- Exercises completed: 1
- Turns so far: 7
- Most recent topic: loops
- Exercise currently open with the learner:
  <first 800 chars>
```

Bounding both keeps token cost per turn roughly constant regardless of session
length. Without them each turn was answered cold, which is precisely why
"explain that again" used to restart on an unrelated topic.

### Derivation rules

Four rules, each correcting a way state was previously misreported.

**Skill level — explicit marker first.** The assessment agent must end with
`Skill Level: <level>`, matched by:

```python
r"skill\s*level\s*[:\-]\s*\**\s*(beginner|intermediate|advanced|unknown)"
```

The **last** match wins. If the marker is absent, the learner's own
self-description is parsed instead, and only when they actually described
themselves — otherwise the level stays `unknown`.

> Reading the level out of prose fails because assessment replies normally name
> all three levels while explaining them. Scanning for the first occurrence
> classified *every* learner as `beginner`, including one who said "I'm an expert
> with 10 years of Python".

**Topics — learner-driven, teaching and practice only.** The topic comes from
the learner's message; only if that yields nothing do teaching and practice
replies get scanned. A topic is added to `topics_learned` **only** on a teaching
or practice turn.

> Harvesting topics from any reply meant a roadmap that merely *recommended*
> loops marked loops as studied, and an assessment listing four recommended
> topics marked all four.

**Exercises — delivered and completed are different facts.**
`exercises_delivered` increments when practice hands one out.
`exercises_completed` increments only when the learner signals completion — one
of 11 phrases (`i solved`, `finished it`, `here is my code`, `that worked`, …) —
at which point `last_exercise` is cleared.

**Topic aliases — bounded on both sides.** 13 topics with inflections. A leading
boundary alone let `listen` match `list` and `classify` match `class`. Bare
`set` is deliberately excluded: "set up a variable" is not a lesson about sets.

### Skill level transitions

```
        ┌──────────────────────────────────────────┐
        │              unknown                     │
        └───┬──────────────────┬───────────────────┘
            │ marker line      │ self-description
            │ from assessment  │ ("never programmed",
            │                  │  "10 years of…")
            ▼                  ▼
   ┌──────────┐  ┌──────────────┐  ┌──────────┐
   │ beginner │  │ intermediate │  │ advanced │
   └──────────┘  └──────────────┘  └──────────┘
        ▲                 ▲               ▲
        └─── any later assessment turn ───┘
                    (freely re-assignable)

   reset_user_context()  ──►  back to unknown
```

Level is not monotonic — a later assessment can lower it. There is no
promotion-on-achievement path; level changes only through assessment.

### Schema migration

`_normalize_context()` upgrades documents written by older versions:

- Missing progress counters are defaulted, not assumed.
- Legacy history entries `{agent, message}` become `{role: "user", text, agent}`.
- Non-dict and unparseable entries are dropped rather than raising.

A malformed stored turn must never cost the learner a reply, so every path here
degrades rather than throws.

## 11. Gemini integration

### Model resolution

```python
resolve_model_id()  = ADK_MODEL or GEMINI_MODEL or "gemini-2.5-flash"
```

`or` chaining, not `os.getenv(a, os.getenv(b, c))` — the latter evaluates its
default eagerly, so an empty `ADK_MODEL=""` would win over a set `GEMINI_MODEL`.

Fallback chain from `GEMINI_FALLBACK_MODELS`, default
`gemini-2.5-flash-lite,gemini-2.0-flash-lite`, with the primary filtered out.

### Call construction

```python
types.GenerateContentConfig(
    tools = [<the agent's tool functions>],
    system_instruction = AGENT_PROMPTS[name] + "\n\nLearner profile:\n" + note,
    automatic_function_calling = types.AutomaticFunctionCallingConfig(
        maximum_remote_calls = 4
    ),
)
```

Raw Python callables are passed as `tools`; the SDK derives function
declarations from signatures and type hints — which is why the tool functions
have complete annotations and single-line docstrings.

Automatic Function Calling is left **enabled** so the SDK completes the
tool-call loop and returns prose. Disabling it would hand back a raw function
call for the coordinator to execute and re-submit. The 4-hop cap bounds a
pathological loop.

### Model fallback chain

`query()` walks `[primary] + fallback_models`:

```
for model in models:
    try:  response = generate_content(model=model, …)
    except:
        err = classify_error(exc)
        if not err.try_other_model:  raise      # auth errors: stop
        continue                                # quota/404/5xx: next model
    if not response.text:
        err = empty_response;  continue         # blank bubble = failure
    last_model_used = model;  return text
```

Free-tier quota is metered **per model**, which is what makes this effective.
Verified live: `gemini-2.5-flash` → `429`, `gemini-2.5-flash-lite` → `200`,
inside a single request.

An empty response is treated as a failure. A tool call that produces no narration
leaves the learner with an empty chat bubble, which reads as a crash.

## 12. Failure handling

### Background

Every failure was retried three times with 0.6 / 1.2 / 2.4 s backoff —
regardless of whether a retry could help — and each attempt consumed real API
quota. One learner message therefore cost three requests, so the Gemini free
tier (~20 requests/day/model) was exhausted in roughly six messages. Meanwhile
the server was replying *"Please retry in 16.2s"* and the code retried after
0.6 s. The resulting `429` was then replaced with the string "Gemini is
unavailable right now", making the cause invisible from outside.

The failure mode was self-reinforcing: quota errors caused more quota errors.

### Error taxonomy

`classify_error()` reads the status from the exception (or its message, since the
SDK embeds it) and splits daily quota from per-minute limiting — the two need
opposite handling.

| `kind` | Detected from | Retry | Other model | Rationale |
| --- | --- | --- | --- | --- |
| `quota_exhausted` | 429 + `PerDay` / `free_tier_requests` | No | Yes | Daily cap won't clear inside a request |
| `rate_limit` | 429 without daily markers | Once | Yes | Per-minute limit does clear |
| `auth_error` | 401, 403, `PERMISSION_DENIED`, `API_KEY_INVALID` | No | No | Another model is rejected identically |
| `model_not_found` | 404, `NOT_FOUND` | No | Yes | Configured model is simply wrong |
| `bad_request` | 400 | No | No | Malformed request; retrying is pointless |
| `server_error` | ≥500 | Once | Yes | Genuinely transient |
| `timeout` | "timeout" / "deadline" | Once | Yes | Transient |
| `empty_response` | 200 with no text | — | Yes | Blank bubble reads as a crash |
| `unknown` | anything else | No | No | Fail safe, don't spend quota guessing |

`retry_after` is parsed from either `retry in 12.3s` or `'retryDelay': '16s'`.

### Retry policy

At most **two attempts**, and the second only for `retryable` kinds:

```
attempt 1 ──► AgentCallError
                 │
                 ├─ not retryable ─────────────────────► fallback
                 ├─ retry_after > 5s ──────────────────► fallback
                 └─ retryable, wait ≤ 5s ─► attempt 2 ─► fallback if it fails
```

Two deliberate choices:

**Honour the server's own hint.** Retrying sooner than the API asks guarantees
another refusal *and* spends quota to earn it.

**Cap the wait at 5 seconds.** A learner is watching a spinner. A 45-second
server cooldown is not something to wait out inside a request.

### Circuit breaker

```
BREAKER_THRESHOLD  = 2 consecutive quota_exhausted or auth_error
BREAKER_COOLDOWN_S = 120
```

While open, `process_with_agent` skips the API entirely. Any success resets the
counter; a non-quota, non-auth failure also resets it, so transient blips don't
accumulate toward the trip.

Without this, every learner turn spends one more request against a quota already
known to be dead.

### Degraded mode

When the API cannot answer, `_local_fallback()` serves deterministic content from
the same tool functions — so the coach still teaches, sets exercises, and reports
progress. The difference from before is that it **says why**, in four places:

| Surface | Field |
| --- | --- |
| `/chat` | `degraded: true`, `degraded_reason: "quota_exhausted"` |
| `/health`, `/status` | `degraded`, `api_paused`, `last_error{kind, message, retry_after}` |
| Answer text | A `Note:` paragraph naming the cause and the remedy |
| Web UI | Amber banner above the chat log |

`/health` deliberately returns **200 while degraded**. A 503 would make Cloud Run
recycle the instance, and restarting an instance cannot refill an API quota.
`status` in the body carries the distinction instead.

### Fallback content is real

Every branch reads actual learner state:

| Agent | Local behaviour |
| --- | --- |
| assessment | Analyses the message, emits a `Skill Level:` marker |
| teaching | `_extract_topic(message)` → `last_topic` → `"variables"` |
| practice | Topic as above; difficulty from `_pick_difficulty(level, progress)` |
| curriculum | Roadmap for the assessed level |
| progress | Real topics, delivered/completed counts, badge, pace |

`_pick_difficulty`: advanced → hard; intermediate → medium, hard after 5
completed; beginner → easy, medium after 3.

> The progress report previously hard-coded `topics_learned="variables, loops"`,
> `exercises_completed=3`, `days_active=7` and reported those numbers to every
> learner regardless of what they had done. The teaching fallback defaulted to
> `"variables"` on any unrecognised topic, so "explain that again" silently
> changed subject.

## 13. HTTP API

### `POST /chat`

Request:

```json
{ "message": "Explain Python dictionaries", "user_id": "demo" }
```

Response `200`:

```json
{
  "response": "Okay, let's dive into Python dictionaries! …",
  "agent_used": "teaching",
  "source": "gemini",
  "model": "gemini-2.5-flash-lite",
  "user_id": "demo",
  "context": {
    "skill_level": "beginner",
    "learning_style": "adaptive",
    "last_agent": "teaching",
    "last_topic": "dictionaries",
    "last_response_source": "gemini",
    "last_model": "gemini-2.5-flash-lite",
    "history_count": 4,
    "progress": {
      "topics_learned": ["dictionaries"],
      "exercises_delivered": 0,
      "exercises_completed": 0,
      "interactions": 2
    }
  },
  "status": "success"
}
```

Degraded responses add `"degraded": true` and `"degraded_reason": "<kind>"`.

| Status | Condition |
| --- | --- |
| `200` | Answered — from Gemini or from local content |
| `400` | `message` missing or whitespace only |
| `413` | `message` longer than `MAX_MESSAGE_CHARS` (default 4000) |
| `500` | Unexpected internal error — generic text, detail logged only |

`source` values: `gemini` (live), `local` (local mode), `fallback` (live mode,
API failed).

### Other endpoints

| Method | Path | Returns |
| --- | --- | --- |
| `GET` | `/` | The web UI |
| `GET` | `/health` | `status`, `mode`, `model`, `fallback_models`, `agents_count`, `active_users`, `degraded`, `api_paused`, `last_error` |
| `GET` | `/status` | The health snapshot plus `service` and `agents` |
| `GET` | `/context/<user_id>` | `{status, user_id, context}` |
| `POST` | `/reset` | Clears one learner's context, returns the fresh one |

### Input handling

- `user_id` defaults to `default_user` and is truncated to 64 characters.
- `request.get_json(silent=True) or {}` — malformed JSON becomes an empty body
  and a clean `400`, not a Flask error page.
- Message length is capped **before** any API call, so an oversized paste cannot
  consume the request budget.
- Internal exception text is never returned to the browser; it is logged and
  replaced with a generic message.

## 14. Frontend

Single page, three panels, no build step and no framework.

| Panel | Contents |
| --- | --- |
| Sidebar | Learner ID, level, style, turn count, practice `done/given`, five agent shortcut chips, reset |
| Coach | Degraded banner, chat log, typing indicator, composer |
| Inspector | Tracked topics, three follow-up shortcuts (Simplify / Challenge / Plan) |

State model:

```javascript
state = { status, context, history }
```

- `history` persists to `localStorage` under `plc_history_<user_id>`, capped at
  100 entries. This is a **client-side convenience, independent of server
  memory** — clearing the browser does not reset learner state, and `/reset`
  does not clear another browser's view.
- Switching the learner ID reloads both local history and server context.
- Every coach message is labelled `agent - source - model`, making a degraded
  answer visibly different from a poor one.

**All rendering uses `textContent`, never `innerHTML`.** Model output is
untrusted text; this is the boundary that keeps it from becoming markup. It also
means Markdown in model replies renders literally — a deliberate trade of
prettiness for safety.

## 15. Persistence

Off by default. With `FIRESTORE_ENABLED=1`, contexts live at `users/{user_id}`.

Best-effort throughout — reads and writes are individually wrapped, logged, and
swallowed. Losing Firestore degrades the coach to in-memory sessions rather than
taking it down.

Writes happen on every context mutation: after appending a turn, after recording
a response, on reset. This is chatty. A single write per request, or a periodic
flush, would be the obvious optimisation if write costs became relevant.

Without Firestore, memory is **per-process**. Two Cloud Run instances give one
learner two different memories, and any restart loses everything.

## 16. Testing

49 tests, no credentials required, ~0.1 s total.

| Suite | Tests | Protects |
| --- | --- | --- |
| `LocalAppTests` | 6 | Endpoints, health shape, 400/413 validation |
| `RouterTests` | 12 | Every rule; the `explanation`/`plan` and `multitask`/`task` bugs |
| `ContextTrackingTests` | 8 | Level parsing, topic attribution, counter split |
| `LocalFallbackTests` | 5 | Fallbacks reflect real state, not hard-coded values |
| `ClassifyErrorTests` | 6 | Each error kind and its retry decision |
| `BuildContentsTests` | 2 | History conversion, malformed entries skipped |
| `RetryPolicyTests` | 8 | Retry counts, breaker, memory passed to agents |
| `PromptWiringTests` | 1 | Every agent uses the shared prompt table |
| `ContextMigrationTests` | 1 | Old Firestore documents still load |

Two design choices keep it fast and free:

**`LOCAL_ONLY=1`** at import time, so the app initialises with no client.

**`FakeAgent`** — a stub whose `query()` raises a chosen `AgentCallError` and
records what it received. This is what makes retry counts, breaker thresholds,
and "was history actually passed?" testable without a network call or a cent of
quota:

```python
def test_quota_error_is_not_retried(self):
    agent = FakeAgent(error=classify_error(Exception(QUOTA_MESSAGE)))
    self.coord.agents["teaching"] = agent
    text = self._run("teaching", "explain loops")
    self.assertEqual(agent.calls, 1)          # not 3
    self.assertIn("quota", text.lower())      # reason reaches the learner
```

`QUOTA_MESSAGE` is a real captured 429 payload, so the classifier is tested
against the wire format rather than an idealised one.

```bash
LOCAL_ONLY=1 python -m unittest discover -s tests -t .
```

---

# Part IV — Operations

## 17. Deployment

### Container

`python:3.11-slim`, non-root `appuser` (UID 1000), gunicorn:

```
gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 120 \
         --graceful-timeout 30 --worker-tmp-dir /dev/shm --access-logfile - main:app
```

| Choice | Reason |
| --- | --- |
| `--timeout 120`, not `0` | Unbounded lets a hung model call pin a worker forever |
| 2 workers × 4 threads | Workload is I/O-bound on the API; threads are the cheap axis |
| `--worker-tmp-dir /dev/shm` | Cloud Run's filesystem is slow for gunicorn heartbeats |
| No `build-essential` | Every dependency ships a wheel; it added ~400 MB |
| Non-root | Standard container hardening |

`HEALTHCHECK` curls `/health` on `$PORT` every 30 s (10 s start period, 3
retries). It is kept on one line so linters don't read its `CMD` as a second
container `CMD`.

### Cloud Run

`deploy.sh` enables the required APIs, ensures the Artifact Registry repo,
builds via Cloud Build, and deploys with:

```
FIRESTORE_ENABLED=1
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=<project>
GOOGLE_CLOUD_LOCATION=northamerica-northeast1
```

Service region `northamerica-northeast2`, Vertex region
`northamerica-northeast1` — deliberately different, because Gemini model
availability and Cloud Run availability are not the same map.

**No API key is deployed.** Vertex mode uses the service account, which needs
`roles/datastore.user` for Firestore.

`.agent_engine_config.json`: 0–2 instances, 2 CPU, 4 GiB.

CI (`.github/workflows/docker-image.yml`) builds the image on every push and PR
to `main`. It does **not** run the test suite — an obvious gap, and a two-line
addition.

### Observability

`/health` is the primary signal. `last_error.kind` distinguishes the failures
that look identical from the outside:

| `kind` | Meaning | Action |
| --- | --- | --- |
| `quota_exhausted` | Free tier used up | Wait for reset, change model, or enable billing |
| `auth_error` | Bad key or missing IAM | Check `GEMINI_API_KEY` / service account |
| `model_not_found` | `GEMINI_MODEL` unavailable | Run `list_models.py` |
| `rate_limit` | Too many requests/minute | Usually self-clearing |

`httpx`, `httpcore`, `google_genai.models`, and `urllib3` are pinned to
`WARNING` regardless of `DEBUG`. Their DEBUG output logs full request and
response bodies, which put learner messages and auth headers into Cloud Run
logs — unreadable and a genuine disclosure risk.

## 18. Operational runbook

**All answers look canned.** Check `/health` → `last_error.kind`, then the table
above. Confirm with `source` in a `/chat` response: `fallback` means live mode
tried and failed; `local` means the process never had credentials.

**Routing is wrong.** Edit `INTENT_KEYWORDS` in `main.py` and add a case to
`RouterTests`. Remember that table order breaks ties.

**Answers ignore context.** Check `history_count` in the response — if it is not
growing, context is being lost (likely a changed `user_id`, or a fresh instance
without Firestore).

**Level stuck on `unknown`.** The assessment agent is not emitting the
`Skill Level:` marker. Check the tail of its reply; the prompt in
`agents/prompts.py` requires it as the final line.

**Verify a deployment.**

```bash
python agent_health_check.py --base-url https://<service>.a.run.app
```

Seeds an assessment, then checks that four probe messages reach the right agents.
It warns rather than fails when the service is degraded, since routing is still
verifiable but model behaviour is not.

## 19. Security

| Area | Current state |
| --- | --- |
| **Authentication** | **None.** `user_id` is client-supplied, so any caller can read or reset any learner's context. |
| Secrets | `.env` is gitignored; Cloud Run uses the service account, no key deployed. |
| XSS | All rendering via `textContent`. Model output cannot inject markup. |
| Input limits | Messages capped at 4000 chars (413); `user_id` truncated to 64. |
| Error disclosure | Internal exception text logged, never returned to the browser. |
| Log hygiene | HTTP wire logging pinned to `WARNING` to keep messages and headers out of logs. |
| Container | Non-root, no compiler, slim base. |
| Prompt injection | **Unmitigated.** Learner text reaches the model directly and could try to override instructions. Blast radius is small — the tools only read static content — but a learner can talk an agent out of its role. |
| Code execution | None. Submitted code is never run, so there is no sandbox to escape. |

The authentication gap is the one that matters. `user_id` as the only identifier
is fine for a single-user demo and wrong for anything shared.

## 20. Limitations and next steps

Ordered by what I would fix first.

1. **No authentication** (§19). Any caller can read or reset any learner's
   context. Blocks multi-user use entirely.
2. **Free-tier quota is the binding constraint.** ~20 requests/day/model. A few
   conversations exhaust it. The app degrades honestly, but sustained use needs
   billing. This is an account limit, not a code defect.
3. **Content gap** (§7). 13 topics recognised, 7 with lessons, 5 with exercises.
   In local mode the uncovered topics yield placeholders.
4. **Per-instance memory** without Firestore (§15). Two instances, two
   memories.
5. **Keyword routing ceiling** (§9). No negation, no confidence, ties by table
   order.
6. **Completion is self-reported.** `exercises_completed` trusts phrases like "I
   solved it". Submitted code is never executed or checked, so the progress
   signal is soft.
7. **CI does not run the tests** (§17) — 49 tests exist and nothing gates on
   them.
8. **Chatty Firestore writes** (§15) — several per request.

Items 1 and 7 are small and high-value. Items 3 and 6 are the ones that would
most change how good the product actually feels.

---

# Appendices

## Appendix A — Configuration reference

| Variable | Default | Effect |
| --- | --- | --- |
| `LOCAL_ONLY` | unset | `1` forces deterministic mode, no API calls |
| `GEMINI_API_KEY` | — | Enables direct API mode |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Primary model |
| `ADK_MODEL` | — | Legacy alias, takes precedence over `GEMINI_MODEL` |
| `GEMINI_FALLBACK_MODELS` | `gemini-2.5-flash-lite,gemini-2.0-flash-lite` | Tried on quota exhaustion |
| `GOOGLE_GENAI_USE_VERTEXAI` | unset | `1` enables Vertex; **outranks the API key** |
| `GOOGLE_CLOUD_PROJECT` | — | Required for Vertex |
| `GOOGLE_CLOUD_LOCATION` | `northamerica-northeast1` | Vertex region |
| `FIRESTORE_ENABLED` | unset | `1` enables persistence |
| `MAX_MESSAGE_CHARS` | `4000` | Longer messages get 413 |
| `PORT` | `8080` | Provided by Cloud Run |
| `HOST` | `0.0.0.0` | Bind address |
| `DEBUG` | `False` | `true` raises app log level to DEBUG |

Internal constants:

| Constant | Value | Location |
| --- | --- | --- |
| `HISTORY_TURNS` | 8 | `base_agent.py` — exchanges sent to the model |
| `MAX_HISTORY_TURNS` | 50 | `coordinator.py` — turns retained |
| `MAX_RETRY_WAIT_S` | 5.0 | `coordinator.py` — longest in-request wait |
| `BREAKER_THRESHOLD` | 2 | `coordinator.py` — failures before pausing |
| `BREAKER_COOLDOWN_S` | 120 | `coordinator.py` — pause duration |
| `maximum_remote_calls` | 4 | `base_agent.py` — tool-call hop cap |
| `MAX_USER_ID_CHARS` | 64 | `settings.py` |

## Appendix B — Where to change things

| To change… | Edit |
| --- | --- |
| Which agent handles a phrase | `INTENT_KEYWORDS` — `main.py` |
| Greeting detection | `GREETING_TERMS`, `GREETING_FILLER` — `main.py` |
| An agent's behaviour or tone | `AGENT_PROMPTS` — `agents/prompts.py` |
| Lesson content | `teaching_materials` — `agents/teaching_agent.py` |
| Exercises | `exercises` — `agents/practice_agent.py` |
| Roadmaps | `python_curricula` — `agents/curriculum_agent.py` |
| Badge thresholds | `track_learning_progress` — `agents/progress_agent.py` |
| Recognised topics | `TOPIC_ALIASES` — `agents/coordinator.py` |
| Completion phrases | `_COMPLETION_SIGNALS` — `agents/coordinator.py` |
| Retry / breaker behaviour | `MAX_RETRY_WAIT_S`, `BREAKER_*` — `agents/coordinator.py` |
| History depth sent to the model | `HISTORY_TURNS` — `agents/base_agent.py` |
| Error classification | `classify_error` — `agents/base_agent.py` |
| Difficulty progression | `_pick_difficulty` — `agents/coordinator.py` |

## Appendix C — Glossary

| Term | Meaning |
| --- | --- |
| **Agent** | One specialist: a prompt, a toolset, and a `query()` method |
| **Tool function** | Plain Python function the model may call; runs in-process |
| **AFC** | Automatic Function Calling — the SDK running the tool loop for you |
| **Coordinator** | `LearningCoachCoordinator`: memory, retry policy, fallback |
| **Context** | One learner's stored state (level, style, history, progress) |
| **Profile note** | Rendered context summary appended to the system instruction |
| **Source** | Where an answer came from: `gemini`, `local`, or `fallback` |
| **Degraded** | Live mode, but answers are coming from local content |
| **Local mode** | No credentials or `LOCAL_ONLY=1`; deterministic content only |
| **Circuit breaker** | Pauses API calls after repeated quota/auth failures |
| **Marker line** | `Skill Level: <level>` — machine-readable assessment output |

## Appendix D — Project tree

```
python_learning_coach_deploy/
├── main.py                       Flask app, routes, intent router
├── Dockerfile                    Container build
├── deploy.sh                     Cloud Run deployment
├── requirements.txt              Runtime dependencies
├── requirements-dev.txt          + pytest, python-docx
├── .env.example                  Documented configuration template
├── .agent_engine_config.json     Instance/resource limits
│
├── agents/
│   ├── base_agent.py             Gemini call layer, error taxonomy, fallback
│   ├── coordinator.py            Orchestration, memory, resilience
│   ├── prompts.py                All five system instructions
│   ├── assessment_agent.py       ┐
│   ├── curriculum_agent.py       │ tool functions
│   ├── teaching_agent.py         │ + agent class
│   ├── practice_agent.py         │ + factory
│   └── progress_agent.py         ┘
│
├── api/google_client.py          Standalone Gemini helper
├── config/settings.py            Environment configuration
├── storage/firestore_store.py    Optional persistence
│
├── templates/index.html          UI shell
├── static/{app.js,styles.css}    UI behaviour and styling
│
├── tests/
│   ├── test_app_local.py         Endpoints, router, context, fallbacks
│   └── test_error_handling.py    Classification, retry, breaker, migration
│
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md    This document
│   └── ARCHITECTURE.md           Shorter overview
│
├── tools/md_to_docx.py           Markdown → Word renderer
├── agent_health_check.py         Deployment verification
├── client.py                     Terminal chat client
├── auto_demo.py                  Scripted demo
└── list_models.py, check_models.py, diagnostics_import_check.py
```
