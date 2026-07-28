import asyncio
import logging
import re

from flask import Flask, jsonify, render_template, request

from agents.coordinator import LearningCoachCoordinator
from config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# The HTTP stack under google-genai logs every request and response at DEBUG,
# including headers and bodies. That is both unreadable and a way for learner
# messages and auth headers to end up in Cloud Run logs, so pin these to
# WARNING regardless of our own log level.
for noisy in ("httpx", "httpcore", "google_genai.models", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# ==========================================
# 1. INITIALIZATION
# ==========================================
logger.info("Initializing Learning Coach Coordinator...")
coordinator = LearningCoachCoordinator()
coordinator.initialize_agents()
logger.info("Coordinator ready in %s mode with %d agents", coordinator.mode, len(coordinator.agents))


def run_async(coro):
    """Run async agent logic from Flask's synchronous request handlers."""
    return asyncio.run(coro)


# ==========================================
# 2. HEALTH / STATUS
# ==========================================
@app.route("/health", methods=["GET"])
def health():
    """Required for the Docker HEALTHCHECK and Cloud Run liveness probes.

    Stays 200 while degraded: the service is still serving useful answers from
    local content, and returning 503 would make Cloud Run cycle the instance for
    something an instance restart cannot fix (an exhausted API quota).
    """
    snapshot = coordinator.health_snapshot()
    return jsonify({"status": "degraded" if snapshot["degraded"] else "healthy", **snapshot}), 200


@app.route("/status", methods=["GET"])
def status():
    """Status page (JSON) used by the web UI badges."""
    snapshot = coordinator.health_snapshot()
    return jsonify(
        {
            "service": "Python Learning Coach AI",
            "status": "Online",
            "agents": list(coordinator.agents.keys()),
            **snapshot,
        }
    )


# ==========================================
# 3. INTELLIGENT ROUTER
# ==========================================
# Ordered so that the first agent with a keyword hit wins. Terms are matched on
# word boundaries: substring matching used to send "give me an explanation" to
# the curriculum agent, because "explanation" contains "plan".
INTENT_KEYWORDS = (
    (
        "practice",
        (
            "practice", "exercise", "exercises", "challenge", "challenges",
            "quiz", "problem set", "give me a task", "drill",
        ),
    ),
    (
        "curriculum",
        (
            "plan", "roadmap", "curriculum", "syllabus", "learning path",
            "study path", "schedule", "week plan", "weekly plan",
        ),
    ),
    (
        "progress",
        (
            "progress", "badge", "badges", "achievement", "achievements",
            "report", "how am i doing", "streak",
        ),
    ),
    (
        "teaching",
        (
            "explain", "explanation", "teach", "tutorial", "what is", "what are",
            "how do i", "how to", "define", "definition", "meaning",
            "basics", "fundamentals", "difference between", "example of",
            "show me how",
            # Questions about the conversation itself. Without these, "what
            # topic were we on?" fell through to the new-user assessment branch.
            "what topic", "which topic", "what were we", "what did we",
            "what have we", "what was i", "remind me", "recap", "so far",
        ),
    ),
    (
        "assessment",
        (
            "assess", "assessment", "evaluate", "my level", "skill level",
            "test me", "where do i stand", "how good am i",
        ),
    ),
)

# Follow-ups that only make sense against the previous turn.
SIMPLIFY_SIGNALS = (
    "simpler", "simple terms", "explain again", "explain it again", "rephrase",
    "say that again", "don't get it", "dont get it", "didn't understand",
    "didnt understand", "too complicated", "too hard to follow",
)
HELP_SIGNALS = (
    "i don't know", "i dont know", "don't know how", "dont know how",
    "i'm stuck", "im stuck", "stuck", "confused", "help me", "give me a hint",
    "i give up",
)

GREETING_TERMS = (
    "hi", "hello", "hey", "hiya", "yo", "howdy", "greetings", "good morning",
    "good afternoon", "good evening", "sup", "hola",
)
# Words that can pad a bare greeting without adding a request.
GREETING_FILLER = {
    "there", "coach", "python", "again", "everyone", "team", "im", "i'm",
    "please", "thanks", "thank", "you", "how", "are", "doing", "whats", "what's",
    "up", "and", "a", "the", "to", "me", "my", "is", "it", "ok", "okay",
}


def _contains_term(msg: str, term: str) -> bool:
    """Word-boundary containment, so 'task' does not match 'multitask'."""
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", msg) is not None


def _matches_any(msg: str, terms) -> bool:
    return any(_contains_term(msg, t) for t in terms)


def is_greeting_only(message: str) -> bool:
    """True when the message is a bare greeting with no actual request.

    "hi" should open with an assessment, but "hello, give me a practice exercise
    on loops" is a practice request that happens to start politely. The original
    router checked the greeting first and swallowed the request.
    """
    msg = (message or "").lower()
    if not _matches_any(msg, GREETING_TERMS):
        return False

    for term in sorted(GREETING_TERMS, key=len, reverse=True):
        msg = re.sub(rf"(?<!\w){re.escape(term)}(?!\w)", " ", msg)

    leftover = [w for w in re.findall(r"[a-z']+", msg) if w not in GREETING_FILLER]
    return not leftover


def determine_agent(message: str, user_id: str) -> str:
    """Route a learner turn to the right expert agent."""
    msg = (message or "").lower()
    context = coordinator.get_user_context(user_id)

    # 1. "Say that again, simpler" is always a teaching follow-up.
    if _matches_any(msg, SIMPLIFY_SIGNALS):
        return "teaching"

    # 2. An explicit request wins over everything else, including a greeting
    #    prefix and the learner's unknown skill level.
    for agent_name, terms in INTENT_KEYWORDS:
        if _matches_any(msg, terms):
            return agent_name

    # 3. Being stuck, with no explicit request, means the learner needs teaching.
    if _matches_any(msg, HELP_SIGNALS):
        return "teaching"

    # 4. Bare greeting: onboard with an assessment.
    if is_greeting_only(msg):
        return "assessment"

    # 5. "I want to start learning Python" is a roadmap request.
    if _matches_any(msg, ("start", "begin", "get started", "learn")) and _matches_any(
        msg, ("python", "programming", "coding", "code")
    ):
        return "curriculum"

    # 6. Onboard a brand-new learner with an assessment. Gated on being early
    #    in the conversation: an unknown skill level several turns in should not
    #    turn every unmatched question into another assessment.
    turns = len(context.get("history", []))
    if context.get("skill_level") == "unknown" and turns < 4:
        return "assessment"

    # 7. Default: keep teaching early on, shift to practice once they have
    #    covered some ground.
    return "teaching" if turns < 6 else "practice"


# ==========================================
# 4. API ENDPOINTS
# ==========================================
@app.route("/chat", methods=["POST"])
def chat():
    """Main entry point for the multi-agent coach."""
    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()
    user_id = str(data.get("user_id", settings.DEFAULT_USER_ID)).strip() or settings.DEFAULT_USER_ID

    if not user_message:
        return jsonify({"error": "Message is empty", "status": "error"}), 400

    # Cap the payload before it reaches a metered API. Without this a single
    # oversized paste can blow the request budget or be rejected downstream.
    if len(user_message) > settings.MAX_MESSAGE_CHARS:
        return (
            jsonify(
                {
                    "error": (
                        f"Message is too long ({len(user_message)} characters). "
                        f"Please keep it under {settings.MAX_MESSAGE_CHARS}."
                    ),
                    "status": "error",
                }
            ),
            413,
        )
    user_id = user_id[: settings.MAX_USER_ID_CHARS]

    try:
        agent_name = determine_agent(user_message, user_id)
        response = run_async(coordinator.process_with_agent(agent_name, user_message, user_id))
    except Exception as e:
        # The coordinator already falls back locally for API failures, so
        # reaching here means a genuine bug. Log the detail, return a generic
        # message rather than echoing internals to the browser.
        logger.exception("Unhandled error while processing chat for user %s", user_id)
        return (
            jsonify({"error": "The coach hit an internal error. Please try again.", "status": "error"}),
            500,
        )

    public_context = coordinator.get_public_context(user_id)
    source = public_context.get("last_response_source", "unknown")
    payload = {
        "response": response,
        "agent_used": agent_name,
        "source": source,
        "model": public_context.get("last_model"),
        "user_id": user_id,
        "context": public_context,
        "status": "success",
    }
    # Tell the UI why an answer is canned instead of letting it look like the
    # model simply gave a poor reply.
    if source == "fallback" and coordinator.last_error:
        payload["degraded"] = True
        payload["degraded_reason"] = coordinator.last_error.get("kind")
    return jsonify(payload)


@app.route("/", methods=["GET"])
def index():
    """Basic web UI."""
    return render_template("index.html")


@app.route("/context/<user_id>", methods=["GET"])
def context(user_id):
    """Current learner state, for the frontend."""
    user_id = (str(user_id).strip() or settings.DEFAULT_USER_ID)[: settings.MAX_USER_ID_CHARS]
    return jsonify(
        {
            "status": "success",
            "user_id": user_id,
            "context": coordinator.get_public_context(user_id),
        }
    )


@app.route("/reset", methods=["POST"])
def reset():
    """Reset one learner's context."""
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id", settings.DEFAULT_USER_ID)).strip() or settings.DEFAULT_USER_ID
    user_id = user_id[: settings.MAX_USER_ID_CHARS]
    coordinator.reset_user_context(user_id)
    return jsonify(
        {
            "status": "success",
            "user_id": user_id,
            "context": coordinator.get_public_context(user_id),
        }
    )


# ==========================================
# 5. SERVER RUN
# ==========================================
if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
