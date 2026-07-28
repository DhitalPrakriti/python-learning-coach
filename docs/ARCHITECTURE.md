# Python Learning Coach — Architecture

A multi-agent Python tutor built on Flask and Google Gemini. Five specialist
agents share one model client and one per-learner memory, and a keyword router
decides which specialist answers each turn.

- **Repository:** `DhitalPrakriti/python-learning-coach`
- **Branch documented:** `dev` (merged to `main` via PR #1)
- **Runtime:** Python 3.11, Flask, `google-genai` 2.x
- **Document date:** 28 July 2026

---

## 1. What this project is

The coach is deliberately not a general chatbot. A learner's message is routed to
one of five agents, each with a narrow job and its own tools:

| Agent | Job | Tools it can call |
| --- | --- | --- |
| **Assessment** | Work out the learner's level and learning style | `analyze_student_input`, `assess_with_code_sample`, `assess_learning_profile` |
| **Curriculum** | Build a multi-week roadmap from that level | `generate_python_curriculum` |
| **Teaching** | Explain one concept with analogy and examples | `teach_python_concept` |
| **Practice** | Produce an exercise with hints, withholding the solution | `generate_python_exercise` |
| **Progress** | Report what has actually been done, with badges | `track_learning_progress`, `generate_progress_report`, `suggest_next_steps` |

Three learner levels drive nearly all behaviour: `beginner`, `intermediate`,
`advanced` (plus `unknown` before assessment).

The design idea worth naming: **each agent's domain knowledge lives in a plain
Python function, not in the prompt.** `teach_python_concept` is an ordinary
dictionary lookup returning explanations, analogies, examples, and common
mistakes. The model's job is to call it and narrate the result. This is what
makes the local deterministic mode possible — the same functions serve content
with no model involved.

---

## 2. Component layout

```
main.py                  Flask app, HTTP routes, the intent router
config/settings.py       All environment configuration, one place
agents/
  coordinator.py         Orchestrator: agent lifecycle, memory, retries, fallback
  base_agent.py          Shared Gemini call layer + error classification
  prompts.py             All five system instructions (single source of truth)
  assessment_agent.py    Tool functions + agent class, one file per specialist
  curriculum_agent.py
  teaching_agent.py
  practice_agent.py
  progress_agent.py
storage/firestore_store.py   Optional cross-restart persistence
templates/index.html     Web UI shell
static/app.js            Chat state, context panel, degraded banner
static/styles.css
tests/                   49 tests, all runnable with no credentials
```

Frontend and backend are served by the same Flask process. There is no separate
API tier.

### Layering

```
Browser (static/app.js)
        │  POST /chat
        ▼
main.py ─── determine_agent()          pure function, no I/O
        │
        ▼
LearningCoachCoordinator                memory, retry policy, fallback
        │
        ▼
BaseGenAIAgent.query()                  Gemini call, model fallback chain
        │
        ├──► Gemini API ──► tool functions (executed locally by the SDK)
        │
        └──► on failure: deterministic local content from the same functions
```

Each layer has one responsibility, and the boundaries matter:

- `determine_agent()` is a pure function of `(message, context)`. It makes no
  network calls, which is why every routing rule is directly unit-testable.
- The **coordinator** owns policy — what to retry, what to remember, when to
  give up. It never talks to the API itself.
- `BaseGenAIAgent` owns the **mechanics** of one API call and knows nothing about
  learners.

---

## 3. Request lifecycle

A single `POST /chat` turn:

1. **Validate.** Reject empty messages (400) and messages over
   `MAX_MESSAGE_CHARS` (413). The cap exists so one oversized paste cannot
   consume the API budget.
2. **Route.** `determine_agent()` picks a specialist (§4).
3. **Load memory.** The coordinator fetches or creates the learner context,
   from Firestore if enabled.
4. **Append the turn** to the transcript.
5. **Rewrite if needed.** Terse follow-ups are made self-contained — "simpler"
   becomes "Explain `<last_topic>` again in simpler terms…".
6. **Call the model** with the message, the last 8 exchanges, and a compact
   learner profile. Retry policy per §6.
7. **Update state** — level, topics, counters, transcript (§5).
8. **Respond** with the answer, which agent handled it, the source
   (`gemini` / `local` / `fallback`), the model used, and the public context.

### Runtime modes

| Mode | Trigger | Behaviour |
| --- | --- | --- |
| `local` | `LOCAL_ONLY=1`, or no credentials | Deterministic content from the tool functions. No network. Powers the test suite. |
| `vertex_ai` | `GOOGLE_GENAI_USE_VERTEXAI=1` | Vertex client. Checked **before** the API key so a stale local `.env` cannot override a deployment. |
| `gemini_api_key` | `GEMINI_API_KEY` set | Direct Gemini API client. |

---

## 4. The router

`determine_agent()` checks rules in order; first match wins:

1. Rephrase signals ("simpler", "explain again") → **teaching**
2. Explicit keyword request → **practice / curriculum / progress / teaching / assessment**
3. Stuck signals ("I don't know", "confused") → **teaching**
4. Bare greeting with no request → **assessment**
5. "I want to start learning Python" → **curriculum**
6. Unknown level in the first few turns → **assessment**
7. Otherwise → **teaching** early, **practice** once ground is covered

Two properties of this ordering are load-bearing:

**Keywords match on word boundaries.** Plain substring matching sent "give me an
explanation" to the curriculum agent, because `"explanation"` contains `"plan"`.
Likewise `"multitask"` contained `"task"` and routed to practice.

**An explicit request outranks a greeting.** Checking the greeting first meant
"hello, give me a practice exercise on loops" was treated as a bare hello and
answered with an assessment, silently discarding the request.

Rule 6 is gated on conversation length. Without that gate, a learner whose level
was never established had every unmatched question turned into yet another
assessment.

### Known limits

This is a keyword router, not an intent classifier. It cannot handle negation
("I *don't* want practice"), and a message that matches two agents resolves by
table order rather than by what the learner emphasised. A classifier — or a
small model call for routing — is the natural next step. The tests document the
current behaviour precisely enough to make that swap safely.

---

## 5. Learner memory

Held in `coordinator.user_contexts`, keyed by user ID, optionally mirrored to
Firestore under `users/{user_id}`:

```python
{
  "skill_level":    "beginner|intermediate|advanced|unknown",
  "learning_style": "visual|auditory|kinesthetic|adaptive",
  "history":        [{"role": "user|coach", "text": str, "agent": str}],  # max 50
  "last_agent":     str,
  "last_topic":     str,
  "last_exercise":  str,   # the open exercise, for "I'm stuck"
  "last_model":     str,
  "progress": {
      "topics_learned":      [str],
      "exercises_delivered": int,
      "exercises_completed": int,
      "interactions":        int,
  },
}
```

What is sent to the model each turn: the **last 8 exchanges** plus a rendered
profile summary. Bounding it keeps token cost predictable while still supporting
real follow-ups. Without this, each turn was answered cold — the reason
"explain that again" used to restart from a different topic.

Four rules govern how state is derived, each one correcting a way the original
version misrepresented the learner:

**Level comes from an explicit marker.** The assessment agent ends its reply with
`Skill Level: <level>`. Scanning the prose instead is unreliable because an
assessment reply normally names all three levels — so a learner saying "I'm an
expert with 10 years" was classified `beginner`. If the marker is missing, the
learner's own self-description is parsed as a fallback.

**Topics come from what the learner asked**, and only teaching and practice turns
count as studying. Harvesting topics from any reply meant a roadmap that merely
*recommended* loops marked loops as learned.

**Delivered and completed exercises are separate.** `exercises_delivered`
increments when the coach hands one out; `exercises_completed` only when the
learner says they finished. One counter conflated work offered with work done.

**Topic aliases match on both boundaries.** A leading boundary alone let "listen"
match `list` and "classify" match `class`.

Persistence is best-effort throughout: Firestore read and write failures are
logged and swallowed, so losing the database degrades the coach to in-memory
sessions rather than taking it down.

---

## 6. Failure handling

This is the part that most affected perceived quality, so it is worth stating
plainly what went wrong. Every failure was retried three times with 0.6/1.2/2.4s
backoff, **including errors no retry can fix**, and each attempt spent real API
quota. One learner message therefore cost three requests, and the Gemini free
tier — roughly 20 requests per day per model — was exhausted in about six
messages. The server was answering `"Please retry in 16.2s"` while the code
retried after 0.6s. The resulting `429` was then replaced with the generic string
"Gemini is unavailable right now", so the cause was invisible.

Errors are now classified before anything is decided:

| Kind | Retry? | Try another model? | Rationale |
| --- | --- | --- | --- |
| `quota_exhausted` | No | Yes | A daily cap will not clear inside a request. |
| `rate_limit` | Once | Yes | A per-minute limit does clear. |
| `auth_error` | No | No | A different model will be rejected identically. |
| `model_not_found` | No | Yes | The configured model is simply wrong. |
| `server_error` (5xx) | Once | Yes | Genuinely transient. |
| `empty_response` | — | Yes | A tool call with no narration is a blank bubble. |

Three mechanisms follow from that classification:

**Honour the server's own retry hint.** Retrying sooner than the API asks
guarantees another refusal *and* spends quota doing it. Hints longer than 5
seconds skip the wait entirely — a learner is watching a spinner.

**Model fallback chain.** Free-tier quota is metered *per model*, so an exhausted
`gemini-2.5-flash` transparently retries on `gemini-2.5-flash-lite`. Verified
live: `429` on the primary, `200` on the fallback, within one request.

**Circuit breaker.** Two consecutive quota or auth failures pause API calls for
120 seconds. Without it, every turn spends another request against a quota
already known to be dead.

### Degrading honestly

When Gemini cannot answer, the same tool functions serve deterministic content —
so the coach still teaches, still sets exercises, still reports progress. The
difference from before is that it says **why**:

- `/chat` → `degraded: true`, `degraded_reason: "quota_exhausted"`
- `/health` → `degraded`, `api_paused`, `last_error`
- The UI shows a banner explaining the cause and the remedy

`/health` deliberately stays `200` while degraded. Returning `503` would make
Cloud Run recycle the instance, and restarting an instance cannot refill an API
quota.

The fallback content reads real learner state. Previously the progress report
hard-coded `topics_learned="variables, loops"`, `exercises_completed=3`,
`days_active=7` and reported those numbers to every learner regardless of what
they had done.

---

## 7. HTTP interface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Web UI |
| `POST` | `/chat` | Main entry point. `{message, user_id}` |
| `GET` | `/health` | Liveness + degradation detail |
| `GET` | `/status` | Mode, model, agent list, for the UI badges |
| `GET` | `/context/<user_id>` | Public learner state |
| `POST` | `/reset` | Clear one learner's context |

`/chat` response:

```json
{
  "response": "...",
  "agent_used": "teaching",
  "source": "gemini",
  "model": "gemini-2.5-flash-lite",
  "user_id": "demo",
  "context": { "skill_level": "beginner", "progress": { } },
  "status": "success"
}
```

Internal exception text is never returned to the browser; it is logged and
replaced with a generic message.

---

## 8. Frontend

A single page with three panels: learner profile and agent shortcuts, the chat
column, and a session inspector showing tracked topics.

- Chat history is kept in `localStorage`, per learner ID — a client-side
  convenience that is independent of server-side memory.
- All message rendering uses `textContent`, never `innerHTML`, so model output
  cannot inject markup.
- Every response is labelled with the agent, the source, and the model, which
  makes a degraded answer obvious rather than looking like a poor reply.

---

## 9. Testing

49 tests, grouped by the behaviour they protect:

| Suite | Covers |
| --- | --- |
| `LocalAppTests` | Endpoints, health, validation, the 413 cap |
| `RouterTests` | Every routing rule and each substring bug |
| `ContextTrackingTests` | Level parsing, topic attribution, counters |
| `LocalFallbackTests` | Fallbacks reflect real state |
| `ClassifyErrorTests` | Each error kind and its retry decision |
| `RetryPolicyTests` | Retry counts, breaker, memory passed to agents |
| `PromptWiringTests` | Every agent uses the shared prompt table |
| `ContextMigrationTests` | Old Firestore documents still load |

Two properties make the suite cheap to run: `LOCAL_ONLY=1` needs no credentials,
and `RetryPolicyTests` injects a `FakeAgent` that raises chosen errors, so retry
and breaker behaviour is tested without touching the network or spending quota.

```bash
LOCAL_ONLY=1 python -m unittest discover -s tests -t .
```

---

## 10. Deployment

`Dockerfile` → `python:3.11-slim`, non-root user, gunicorn with 2 workers × 4
threads. Two choices worth noting: the request timeout is 120s rather than
unbounded, because a hung model call would otherwise pin a worker forever; and
no compiler is installed, since every dependency ships a wheel and
`build-essential` added roughly 400MB.

`deploy.sh` builds via Cloud Build, pushes to Artifact Registry, and deploys to
Cloud Run with `GOOGLE_GENAI_USE_VERTEXAI=1`. On Cloud Run, Vertex AI
credentials come from the service account, so no API key is deployed.

`.github/workflows/docker-image.yml` builds the image on every push and PR to
`main`.

---

## 11. Honest limitations

Worth knowing before building on this:

1. **Free-tier quota is the binding constraint.** ~20 requests/day per model
   means a handful of conversations exhausts it. The app degrades gracefully and
   explains itself, but sustained use needs billing enabled.
2. **In-memory context is per-instance.** Without Firestore, two Cloud Run
   instances give one learner two different memories. Firestore fixes this and is
   off by default.
3. **Keyword routing has a ceiling.** See §4.
4. **Teaching content is a fixed dictionary.** Roughly seven topics have authored
   material; anything else gets a generic placeholder from the tool and relies on
   the model to compensate — and in local mode there is no model to compensate.
5. **No authentication.** `user_id` is client-supplied, so any caller can read or
   reset any learner's context. Fine for a demo, not for real users.
6. **Completion detection is heuristic.** `exercises_completed` relies on phrases
   like "I solved it". Submitted code is never executed or checked.

Items 5 and 6 are the ones to address first if this becomes more than a
portfolio project.

---

## Appendix A — Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `LOCAL_ONLY` | unset | Deterministic mode, no API calls |
| `GEMINI_API_KEY` | — | Direct API mode |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Primary model |
| `GEMINI_FALLBACK_MODELS` | `gemini-2.5-flash-lite,gemini-2.0-flash-lite` | Tried on quota exhaustion |
| `GOOGLE_GENAI_USE_VERTEXAI` | unset | Vertex mode; outranks the API key |
| `GOOGLE_CLOUD_PROJECT` / `_LOCATION` | — | Required for Vertex |
| `FIRESTORE_ENABLED` | unset | Cross-restart persistence |
| `MAX_MESSAGE_CHARS` | `4000` | Reject longer messages with 413 |
| `PORT` / `HOST` / `DEBUG` | `8080` / `0.0.0.0` / `False` | Flask |

## Appendix B — Tuning points

| To change… | Edit |
| --- | --- |
| Which agent handles a phrase | `INTENT_KEYWORDS` in `main.py` |
| An agent's behaviour | `AGENT_PROMPTS` in `agents/prompts.py` |
| Lesson or exercise content | the tool function in the relevant agent file |
| Retry aggressiveness | `MAX_RETRY_WAIT_S`, `BREAKER_*` in `coordinator.py` |
| How much history the model sees | `HISTORY_TURNS` in `base_agent.py` |
| Recognised topics | `TOPIC_ALIASES` in `coordinator.py` |
