# Python Learning Coach (Multi-Agent)

A multi-agent Python tutor that routes user messages to specialized agents
(assessment, teaching, practice, curriculum, progress). Includes a simple web
UI, context memory, and optional Firestore persistence.

---

## Features

- 5 specialized agents: assessment, teaching, practice, curriculum, progress
- Smart routing based on user message intent (word-boundary keyword matching)
- Real conversation memory: prior turns and the learner profile are sent to the
  model, so follow-ups like "explain that again, simpler" work
- Automatic model fallback when the primary model is out of quota
- Local deterministic mode for demos/tests without Gemini
- Graceful degradation that tells you *why* it degraded, instead of silently
  serving canned content
- Optional persistence with Firestore
- Web UI with chat bubbles, typing indicator, and a degraded-state banner
- Cloud Run deployment script

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - full architecture: component
  layout, request lifecycle, routing rules, memory model, failure handling, and
  known limitations.
- `docs/Python_Learning_Coach_Architecture.docx` - the same document as Word.
  Regenerate after editing the Markdown:

  ```bash
  pip install -r requirements-dev.txt
  python tools/md_to_docx.py docs/ARCHITECTURE.md docs/Python_Learning_Coach_Architecture.docx
  ```

---

## Project Structure

- `main.py` - Flask app + intent router
- `agents/` - Agent implementations and tool functions
  - `base_agent.py` - shared Gemini call layer, error classification, model fallback
  - `coordinator.py` - orchestration, learner memory, retry policy, local fallback
  - `prompts.py` - all five system instructions
- `config/settings.py` - environment configuration
- `templates/` - Web UI HTML
- `static/` - Web UI CSS and JS
- `storage/` - Firestore persistence layer
- `tests/` - test suite (runs with no credentials)
- `tools/` - repo tooling (docs generation)
- `deploy.sh` - Cloud Run deployment script
- `agent_health_check.py` - Agent routing verification

---

## Requirements

- Python 3.11+
- Google GenAI (Gemini) credentials
- (Optional) Firestore enabled in GCP project

---

## Environment Variables

- `GEMINI_API_KEY` (local API key usage)
- `GEMINI_MODEL` (defaults to `gemini-2.5-flash`)
- `GEMINI_FALLBACK_MODELS` (comma-separated; tried when the primary model is out
  of quota. Defaults to `gemini-2.5-flash-lite,gemini-2.0-flash-lite`)
- `LOCAL_ONLY=1` (run deterministic local agent content without Gemini)
- `GOOGLE_GENAI_USE_VERTEXAI=1` (Cloud Run usage; takes precedence over
  `GEMINI_API_KEY` so a stale local key cannot override a deployment)
- `GOOGLE_CLOUD_PROJECT` (GCP project ID)
- `GOOGLE_CLOUD_LOCATION` (Vertex AI location, e.g. `northamerica-northeast1`)
- `FIRESTORE_ENABLED=1` (optional persistence)
- `MAX_MESSAGE_CHARS` (default 4000; longer messages are rejected with 413)
- `PORT=8080`

---

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

Open: `http://localhost:8080`

---

## Endpoints

- `GET /` - Web UI
- `GET /status` - JSON status
- `GET /health` - Health check
- `POST /chat` - Main chat endpoint
- `POST /reset` - Reset one user's learning context

### Example `POST /chat`

```bash
curl -i http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Explain Python variables\",\"user_id\":\"demo\"}"
```

---

## Routing Logic

Checked in this order, first match wins:

1. "simpler / explain again / rephrase" -> teaching
2. Explicit keyword request -> practice, curriculum, progress, teaching, assessment
3. "I don't know / stuck / confused" -> teaching
4. Bare greeting with no request -> assessment
5. "I want to start learning Python" -> curriculum
6. Unknown skill level in the first few turns -> assessment
7. Otherwise -> teaching early on, practice once some ground is covered

Keywords match on **word boundaries**. Plain substring matching used to send
"give me an explanation" to the curriculum agent, because `"explanation"`
contains `"plan"`. An explicit request also outranks a greeting prefix, so
"hello, give me a practice exercise" routes to practice rather than assessment.

---

## Context Memory

The coordinator stores per-user context:

- `skill_level`, `learning_style`
- `history` - the full transcript, both learner and coach turns
- `last_agent`, `last_topic`, `last_exercise`, `last_model`
- `progress.topics_learned`, `progress.exercises_delivered`,
  `progress.exercises_completed`, `progress.interactions`

The last 8 exchanges plus a compact learner profile are sent with every model
call, which is what makes follow-ups work:

- "Explain in simpler terms" -> re-explains the same topic with a fresh analogy
- "I don't know" after an exercise -> step-by-step teaching + code
- "What were we discussing?" -> answered from the transcript

`exercises_delivered` counts exercises handed out; `exercises_completed` only
increments when the learner says they finished one.

---

## Degraded Mode

When Gemini cannot answer, the coach serves deterministic local content and says
why. The reason appears in the `/chat` response (`degraded_reason`), in
`/health` (`last_error`), and as a banner in the web UI.

Failure handling depends on the error:

| Error | Behaviour |
| --- | --- |
| Daily quota exhausted (429) | No retry. Try the fallback models, then local content. |
| Rate limited (429) | Retried once, honouring the server's `retryDelay`. |
| Bad credentials (401/403) | No retry, no model switch. Local content. |
| Model not found (404) | Try the fallback models. |
| Server error (5xx) | Retried once, then the fallback models. |

Two consecutive quota or auth failures open a circuit breaker that pauses API
calls for 120 seconds. Without it, every learner turn spends another request of
an already-exhausted quota.

---

## Firestore Persistence

Enable Firestore to persist user context across restarts:

1) Create Firestore in Native mode in your GCP project.
2) Grant your Cloud Run service account the role:
   **Cloud Datastore User** (`roles/datastore.user`)
3) Set `FIRESTORE_ENABLED=1`

Contexts are stored under `users/{user_id}`.

---

## Deploy to Cloud Run

`deploy.sh` builds the Docker image and deploys to Cloud Run.

```bash
./deploy.sh
```

The script sets:

- `GOOGLE_GENAI_USE_VERTEXAI=1`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION` (defaults to `northamerica-northeast1`)
- `FIRESTORE_ENABLED=1`

---

## Health Check

Verify all agents:

```bash
python agent_health_check.py --base-url http://localhost:8080
```

Run the test suite:

```bash
pip install -r requirements-dev.txt
LOCAL_ONLY=1 python -m unittest discover -s tests -t .
```

On Windows PowerShell:

```powershell
$env:LOCAL_ONLY="1"
python -m unittest discover -s tests -t .
```

Or Cloud Run:

```bash
python agent_health_check.py --base-url https://<your-service>.a.run.app
```

---

## Troubleshooting

- **Every answer looks canned / "built-in lesson library"**: the coach is in
  degraded mode. Check `GET /health` -> `last_error.kind`:
  - `quota_exhausted` - the free tier is used up. The Gemini free tier allows
    only ~20 requests/day per model, so a handful of conversations exhausts it.
    Wait for the reset, point `GEMINI_MODEL` at a model with quota left, or
    enable billing.
  - `auth_error` - bad `GEMINI_API_KEY` or missing Vertex AI permissions.
  - `model_not_found` - `GEMINI_MODEL` is not available to this project.
    Run `python list_models.py` to see what is.
- **400 FAILED_PRECONDITION**: Check `GOOGLE_CLOUD_LOCATION`
  (use `northamerica-northeast1` or `global` for Gemini).
- **No persistence**: ensure Firestore is enabled and IAM role is set.
- **Wrong agent responses**: adjust `INTENT_KEYWORDS` in `main.py`.
- **Need offline demo mode**: set `LOCAL_ONLY=1`.

---

## Notes

- The UI stores chat history in browser `localStorage` (client-side).
- Practice agent only returns solutions if explicitly asked.
- Teaching agent includes examples and analogies by default.
