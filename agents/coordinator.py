# agents/coordinator.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()  # ensures .env is loaded even if main.py didn't

import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from google import genai

# Optional persistent storage
from storage import FirestoreStore

from .base_agent import AgentCallError, resolve_fallback_models, resolve_model_id

# Import factory functions
from .assessment_agent import create_assessment_agent
from .curriculum_agent import create_curriculum_agent
from .teaching_agent import create_teaching_agent
from .practice_agent import create_practice_agent
from .progress_agent import create_progress_agent

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 50

# Don't sit on a request waiting out a long server-side cooldown - the learner
# is watching a spinner. Anything longer than this goes straight to fallback.
MAX_RETRY_WAIT_S = 5.0

# After this many consecutive quota/auth failures, stop calling the API for
# COOLDOWN_S. Without this the app spends its whole daily free-tier quota on
# calls it already knows will fail.
BREAKER_THRESHOLD = 2
BREAKER_COOLDOWN_S = 120.0

_SKILL_LINE_RE = re.compile(
    r"skill\s*level\s*[:\-]\s*\**\s*(beginner|intermediate|advanced|unknown)",
    re.IGNORECASE,
)

# Phrases that mean "I finished the exercise", used to separate exercises
# actually completed from exercises merely handed out.
_COMPLETION_SIGNALS = (
    "i solved",
    "solved it",
    "i finished",
    "finished it",
    "i did it",
    "got it working",
    "here is my code",
    "here's my code",
    "my solution",
    "it works now",
    "that worked",
)

_HELP_SIGNALS = ("i don't know", "dont know", "don't know", "stuck", "confused", "help me")
_SIMPLIFY_SIGNALS = ("simpler", "simple terms", "explain again", "rephrase", "don't get it", "dont get it")

TOPIC_ALIASES: Dict[str, List[str]] = {
    "variables": ["variable", "variables"],
    "data types": ["data type", "data types"],
    "operators": ["operator", "operators"],
    "conditionals": ["conditional", "conditionals", "if statement", "if/else", "if else"],
    "loops": ["loop", "loops", "for loop", "while loop", "iteration"],
    "functions": ["function", "functions", "def "],
    "lists": ["list", "lists"],
    "dictionaries": ["dictionary", "dictionaries", "dict"],
    "tuples": ["tuple", "tuples"],
    # No bare "set": "set up a variable" is not a lesson about sets.
    "sets": ["sets", "set data type", "set()"],
    "classes": ["class", "classes", "oop", "object oriented"],
    "error handling": ["error handling", "exception", "exceptions", "try/except"],
    "file handling": ["file handling", "file i/o", "reading files"],
}


class LearningCoachCoordinator:
    """
    Central orchestrator:
    - Initializes all 5 agents using one shared Gemini client
    - Maintains per-user learning context, including the conversation transcript
    - Executes agent.query() safely from Flask (async wrapper)
    - Retries only errors that a retry can actually fix, and falls back to
      deterministic local content otherwise so a demo never dead-ends
    """

    def __init__(self):
        self.client = None
        self.agents: Dict[str, Any] = {}
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        self.store = None
        self.mode = "uninitialized"
        self.model_id = resolve_model_id()
        self.fallback_models = resolve_fallback_models(self.model_id)

        # Health/diagnostics. The original code hid API failures entirely, so
        # there was no way to tell a quota problem from a bad key.
        self.last_error: Optional[Dict[str, Any]] = None
        self._consecutive_hard_failures = 0
        self._breaker_open_until = 0.0

        if os.getenv("FIRESTORE_ENABLED", "").lower() in ("1", "true", "yes"):
            try:
                self.store = FirestoreStore()
            except Exception as e:
                logger.warning("Firestore disabled: %s", e)

    @staticmethod
    def _agent_names() -> List[str]:
        return ["assessment", "curriculum", "teaching", "practice", "progress"]

    @staticmethod
    def _fresh_context() -> Dict[str, Any]:
        return {
            "skill_level": "unknown",
            "learning_style": "adaptive",
            "history": [],
            "progress": {
                "topics_learned": [],
                "exercises_delivered": 0,
                "exercises_completed": 0,
                "interactions": 0,
            },
        }

    # ==========================================
    # 1. INITIALIZE ALL AGENTS
    # ==========================================
    def initialize_agents(self):
        """Create the GenAI client and initialize all agents."""
        api_key = os.getenv("GEMINI_API_KEY")
        local_only = os.getenv("LOCAL_ONLY", "").lower() in ("1", "true", "yes")
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")

        # Vertex is checked before the API key so that a stale GEMINI_API_KEY in
        # a developer's .env cannot silently override a Cloud Run deployment.
        if local_only:
            self.mode = "local"
        elif use_vertex:
            if not project or not location:
                raise RuntimeError(
                    "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set for Vertex AI."
                )
            self.mode = "vertex_ai"
            self.client = genai.Client(vertexai=True, project=project, location=location)
        elif api_key:
            self.mode = "gemini_api_key"
            self.client = genai.Client(api_key=api_key)
        else:
            self.mode = "local"
            logger.info("No Gemini credentials found; starting in local deterministic mode.")

        if self.client:
            self.agents = {
                "assessment": create_assessment_agent(self.client),
                "curriculum": create_curriculum_agent(self.client),
                "teaching": create_teaching_agent(self.client),
                "practice": create_practice_agent(self.client),
                "progress": create_progress_agent(self.client),
            }
        else:
            # Local mode still needs the five keys so routing and /health work.
            self.agents = {name: None for name in self._agent_names()}

        logger.info("All agents initialized in %s mode: %s", self.mode, list(self.agents.keys()))
        return self.agents

    # ==========================================
    # 2. USER CONTEXT MANAGEMENT
    # ==========================================
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Retrieve or create a user's learning context."""
        if user_id not in self.user_contexts:
            stored = None
            if self.store:
                try:
                    stored = self.store.get_user_context(user_id)
                except Exception as e:
                    logger.warning("Firestore read failed: %s", e)

            self.user_contexts[user_id] = self._normalize_context(stored) if stored else self._fresh_context()
        return self.user_contexts[user_id]

    def _normalize_context(self, stored: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in keys added after a context was first persisted.

        Firestore documents written by older versions lack the newer progress
        counters and store history as {agent, message}. Reading one of those
        must not crash or lose the transcript.
        """
        context = self._fresh_context()
        context.update(stored or {})

        progress = context.get("progress")
        if not isinstance(progress, dict):
            progress = {}
        fresh_progress = self._fresh_context()["progress"]
        fresh_progress.update(progress)
        context["progress"] = fresh_progress

        history = context.get("history")
        if not isinstance(history, list):
            history = []
        migrated: List[Dict[str, Any]] = []
        for turn in history:
            if not isinstance(turn, dict):
                continue
            if "text" in turn:
                migrated.append(turn)
            elif "message" in turn:  # legacy shape: user turns only
                migrated.append(
                    {"role": "user", "text": str(turn.get("message", "")), "agent": turn.get("agent")}
                )
        context["history"] = migrated[-MAX_HISTORY_TURNS:]
        return context

    def update_context(self, user_id: str, updates: Dict[str, Any]):
        """Safely update a user's context."""
        context = self.get_user_context(user_id)
        context.update(updates)
        self._save_context(user_id, context)
        return context

    def reset_user_context(self, user_id: str) -> Dict[str, Any]:
        """Reset a user context to a fresh learning profile."""
        self.user_contexts[user_id] = self._fresh_context()
        self._save_context(user_id, self.user_contexts[user_id])
        return self.user_contexts[user_id]

    def get_public_context(self, user_id: str) -> Dict[str, Any]:
        """UI-safe learner state, without full response bodies."""
        context = self.get_user_context(user_id)
        progress = context.get("progress", {})
        return {
            "skill_level": context.get("skill_level", "unknown"),
            "learning_style": context.get("learning_style", "adaptive"),
            "last_agent": context.get("last_agent"),
            "last_topic": context.get("last_topic"),
            "last_response_source": context.get("last_response_source"),
            "last_model": context.get("last_model"),
            "history_count": len(context.get("history", [])),
            "progress": {
                "topics_learned": progress.get("topics_learned", []),
                "exercises_delivered": progress.get("exercises_delivered", 0),
                "exercises_completed": progress.get("exercises_completed", 0),
                "interactions": progress.get("interactions", 0),
            },
        }

    def _save_context(self, user_id: str, context: Dict[str, Any]) -> None:
        if self.store:
            try:
                self.store.save_user_context(user_id, context)
            except Exception as e:
                logger.warning("Firestore write failed: %s", e)

    # ==========================================
    # 3. CONTEXT DERIVATION HELPERS
    # ==========================================
    def _extract_topic(self, text: str) -> Optional[str]:
        """Find the Python topic a piece of text is about.

        Aliases are matched on word boundaries so that "listen" does not count
        as "lists" and "classify" does not count as "classes".
        """
        if not text:
            return None
        msg = text.lower()
        for topic, aliases in TOPIC_ALIASES.items():
            for alias in aliases:
                # Boundaries on both sides: a leading \b alone let "listen"
                # match "list" and "classify" match "class".
                if re.search(rf"(?<!\w){re.escape(alias.strip())}(?!\w)", msg):
                    return topic
        return None

    def _parse_skill_level(self, response_text: str, message: str) -> Optional[str]:
        """Read the assessed level, preferring the agent's explicit marker.

        The original code scanned the whole response for the first of
        "beginner"/"intermediate"/"advanced". Assessment replies normally name
        all three, so every learner came out "beginner". The explicit
        "Skill Level: x" line is checked first, and only if it is missing does
        this fall back to what the learner said about themselves - which is far
        more reliable than the wording of the reply.
        """
        matches = _SKILL_LINE_RE.findall(response_text or "")
        if matches:
            level = matches[-1].lower()
            return None if level == "unknown" else level

        from .assessment_agent import analyze_student_input

        low = (message or "").lower()
        if not low.strip():
            return None
        detected = analyze_student_input(message)["detected_experience"]
        # Only trust self-description when the learner actually described
        # themselves; otherwise analyze_student_input just returns its default.
        described = any(
            w in low
            for w in (
                "beginner", "never", "new to", "no experience", "just starting", "started",
                "intermediate", "some experience", "basic knowledge",
                "advanced", "expert", "senior", "years of", "years",
            )
        )
        return detected if described else None

    def _profile_note(self, context: Dict[str, Any]) -> str:
        """Compact learner state handed to the model as part of its instruction."""
        progress = context.get("progress", {})
        topics = progress.get("topics_learned", []) or []
        lines = [
            f"- Assessed skill level: {context.get('skill_level', 'unknown')}",
            f"- Learning style: {context.get('learning_style', 'adaptive')}",
            f"- Topics studied so far: {', '.join(topics) if topics else 'none yet'}",
            f"- Exercises delivered: {progress.get('exercises_delivered', 0)}",
            f"- Exercises completed: {progress.get('exercises_completed', 0)}",
            f"- Turns so far: {progress.get('interactions', 0)}",
        ]
        if context.get("last_topic"):
            lines.append(f"- Most recent topic: {context['last_topic']}")
        if context.get("last_exercise"):
            lines.append(
                "- Exercise currently open with the learner:\n"
                f"{context['last_exercise'][:800]}"
            )
        return "\n".join(lines)

    def _history_for_model(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prior turns to replay, excluding the turn being answered now."""
        return list(context.get("history", []))[:-1]

    def _record_response_context(
        self,
        user_id: str,
        context: Dict[str, Any],
        agent_name: str,
        message: str,
        response_text: str,
        source: str,
        model: Optional[str] = None,
    ) -> None:
        """Update learner state from one completed exchange."""
        if agent_name == "assessment":
            level = self._parse_skill_level(response_text, message)
            if level:
                context["skill_level"] = level

        # Learning style comes from what the learner says, not from the reply.
        if message:
            from .assessment_agent import analyze_student_input

            style = analyze_student_input(message)["detected_learning_style"]
            if style != "adaptive":
                context["learning_style"] = style

        progress = context.setdefault("progress", {})
        progress["interactions"] = int(progress.get("interactions", 0)) + 1

        context["last_agent"] = agent_name
        context["last_response_source"] = source
        if model:
            context["last_model"] = model

        # Topic tracking is driven by what the learner asked about. Scanning the
        # whole reply used to mark a topic as "learned" merely because the agent
        # listed it as a recommendation.
        topic = self._extract_topic(message)
        if not topic and agent_name in ("teaching", "practice"):
            topic = self._extract_topic(response_text or "")
        if not topic and any(s in (message or "").lower() for s in _SIMPLIFY_SIGNALS + _HELP_SIGNALS):
            topic = context.get("last_topic")

        if topic:
            context["last_topic"] = topic
            # Only teaching and practice constitute studying a topic; asking for
            # a roadmap that mentions loops is not learning loops.
            if agent_name in ("teaching", "practice"):
                topics = progress.setdefault("topics_learned", [])
                if topic not in topics:
                    topics.append(topic)

        if agent_name == "practice" and response_text:
            context["last_exercise"] = response_text[:1200]
            progress["exercises_delivered"] = int(progress.get("exercises_delivered", 0)) + 1

        # An exercise counts as completed when the learner says they finished
        # it, not when the coach hands one out.
        low = (message or "").lower()
        if context.get("last_exercise") and any(sig in low for sig in _COMPLETION_SIGNALS):
            progress["exercises_completed"] = int(progress.get("exercises_completed", 0)) + 1
            context.pop("last_exercise", None)

        self._append_history(context, "coach", response_text, agent_name)
        self._save_context(user_id, context)

    @staticmethod
    def _append_history(
        context: Dict[str, Any], role: str, text: str, agent_name: Optional[str] = None
    ) -> None:
        history = context.setdefault("history", [])
        history.append({"role": role, "text": (text or "")[:4000], "agent": agent_name})
        if len(history) > MAX_HISTORY_TURNS:
            del history[:-MAX_HISTORY_TURNS]

    # ==========================================
    # 4. CORE ROUTING / EXECUTION
    # ==========================================
    def _breaker_open(self) -> bool:
        return time.monotonic() < self._breaker_open_until

    def _note_failure(self, err: AgentCallError) -> None:
        self.last_error = {
            "kind": err.kind,
            "message": str(err)[:500],
            "retry_after": err.retry_after,
        }
        # Quota and auth failures will not fix themselves within a request, so
        # they are the ones worth tripping the breaker over.
        if err.kind in ("quota_exhausted", "auth_error"):
            self._consecutive_hard_failures += 1
            if self._consecutive_hard_failures >= BREAKER_THRESHOLD:
                self._breaker_open_until = time.monotonic() + BREAKER_COOLDOWN_S
                logger.error(
                    "Pausing Gemini calls for %.0fs after %d consecutive %s failures. "
                    "Serving local content until then.",
                    BREAKER_COOLDOWN_S,
                    self._consecutive_hard_failures,
                    err.kind,
                )
        else:
            self._consecutive_hard_failures = 0

    def _note_success(self) -> None:
        self.last_error = None
        self._consecutive_hard_failures = 0
        self._breaker_open_until = 0.0

    def health_snapshot(self) -> Dict[str, Any]:
        """Diagnostics for /health and /status."""
        degraded = self.mode != "local" and (self._breaker_open() or self.last_error is not None)
        return {
            "mode": self.mode,
            "model": self.model_id,
            "fallback_models": self.fallback_models,
            "agents_count": len(self.agents),
            "active_users": len(self.user_contexts),
            "degraded": degraded,
            "api_paused": self._breaker_open(),
            "last_error": self.last_error,
        }

    def _rewrite_message(self, agent_name: str, message: str, context: Dict[str, Any]) -> str:
        """Make terse follow-ups self-contained before they reach the model."""
        low = (message or "").lower()
        if agent_name != "teaching":
            return message

        if any(w in low for w in _SIMPLIFY_SIGNALS) and context.get("last_topic"):
            return (
                f"Explain {context['last_topic']} again in simpler terms, with a "
                f"fresh analogy and a smaller first example. Student said: {message}"
            )
        if any(w in low for w in _HELP_SIGNALS) and context.get("last_exercise"):
            return (
                "The student is stuck on the exercise below. Explain the approach "
                "step-by-step, then show working code.\n\n"
                f"{context['last_exercise']}\n\nStudent message: {message}"
            )
        return message

    async def process_with_agent(self, agent_name: str, message: str, user_id: str) -> str:
        """Run one learner turn through an agent, with retries and fallback."""
        if agent_name not in self.agents:
            return f"Unknown agent: {agent_name}"

        agent = self.agents[agent_name]
        context = self.get_user_context(user_id)

        self._append_history(context, "user", message, agent_name)
        self._save_context(user_id, context)

        if self.mode == "local" or agent is None:
            response_text = self._local_fallback(agent_name, message, user_id, context)
            self._record_response_context(
                user_id, context, agent_name, message, response_text, "local"
            )
            return response_text

        if self._breaker_open():
            response_text = self._local_fallback(
                agent_name, message, user_id, context, notice=self._degraded_notice()
            )
            self._record_response_context(
                user_id, context, agent_name, message, response_text, "fallback"
            )
            return response_text

        msg = self._rewrite_message(agent_name, message, context)
        history = self._history_for_model(context)
        profile_note = self._profile_note(context)

        last_err: Optional[AgentCallError] = None
        loop = asyncio.get_running_loop()

        # Two attempts, not three: each attempt costs real quota, and the third
        # attempt in the original code never once turned a failure into success.
        for attempt in range(2):
            try:
                response_text = await loop.run_in_executor(
                    None, lambda: agent.query(msg, history=history, profile_note=profile_note)
                )
            except AgentCallError as err:
                last_err = err
                logger.warning(
                    "Agent %s attempt %d failed (%s): %s",
                    agent_name, attempt + 1, err.kind, str(err)[:300],
                )
                if not err.retryable or attempt == 1:
                    break
                # Honour the server's own retry hint. Retrying sooner than it
                # asks just spends quota on a call that is going to be refused.
                wait = err.retry_after if err.retry_after else 0.8 * (2 ** attempt)
                if wait > MAX_RETRY_WAIT_S:
                    logger.warning(
                        "Server asked to retry in %.1fs; falling back locally instead.", wait
                    )
                    break
                await asyncio.sleep(wait)
                continue
            except Exception as err:  # unexpected, still must not 500 the app
                last_err = AgentCallError("unknown", str(err))
                logger.exception("Agent %s raised an unexpected error", agent_name)
                break

            self._note_success()
            self._record_response_context(
                user_id, context, agent_name, message, response_text, "gemini",
                model=getattr(agent, "last_model_used", None),
            )
            return response_text

        if last_err is not None:
            self._note_failure(last_err)
        response_text = self._local_fallback(
            agent_name, message, user_id, context, notice=self._degraded_notice(last_err)
        )
        self._record_response_context(
            user_id, context, agent_name, message, response_text, "fallback"
        )
        return response_text

    def _degraded_notice(self, err: Optional[AgentCallError] = None) -> str:
        """Explain *why* the answer is local content instead of hiding it."""
        kind = err.kind if err else (self.last_error or {}).get("kind", "unknown")
        reasons = {
            "quota_exhausted": (
                "The Gemini free-tier quota for this model is used up, so this answer "
                "comes from the built-in lesson library. It will work again once the "
                "quota resets, or set GEMINI_MODEL to a model with quota left."
            ),
            "rate_limit": (
                "Gemini is rate-limiting requests right now, so this answer comes from "
                "the built-in lesson library. Try again in a moment."
            ),
            "auth_error": (
                "Gemini rejected the credentials, so this answer comes from the built-in "
                "lesson library. Check GEMINI_API_KEY or the Vertex AI permissions."
            ),
            "model_not_found": (
                f"The configured model '{self.model_id}' is not available to this project, "
                "so this answer comes from the built-in lesson library."
            ),
        }
        detail = reasons.get(
            kind,
            "Gemini could not be reached, so this answer comes from the built-in lesson library.",
        )
        return f"Note: {detail}\n\n"

    # ==========================================
    # 5. LOCAL FALLBACKS (DEMO NEVER BREAKS)
    # ==========================================
    def _local_fallback(
        self,
        agent_name: str,
        message: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        notice: str = "",
    ) -> str:
        """Deterministic local content, driven by the learner's real context.

        Every branch here now reads the learner's actual level, topic and
        counters. Previously these were hard-coded, so the progress report
        cheerfully invented topics and exercise counts.
        """
        context = context if context is not None else self.get_user_context(user_id)
        progress = context.get("progress", {})
        level = context.get("skill_level", "unknown")
        if level == "unknown":
            level = "beginner"
        style = context.get("learning_style", "adaptive")
        prefix = notice

        if agent_name == "assessment":
            from .assessment_agent import analyze_student_input, assess_learning_profile

            analysis = analyze_student_input(message)
            detected = self._parse_skill_level("", message) or analysis["detected_experience"]
            plan = assess_learning_profile(detected, analysis["detected_learning_style"], "python")
            return (
                prefix
                + f"Detected level: {detected}\n"
                f"Learning style: {analysis['detected_learning_style']}\n"
                f"Recommended pace: {plan['recommended_pace']}\n"
                f"Next steps: {plan['next_steps']}\n"
                f"Recommended topics: {', '.join(plan['recommended_topics'])}\n\n"
                f"Skill Level: {detected}\n"
            )

        if agent_name == "teaching":
            from .teaching_agent import teach_python_concept

            # Fall back to the topic already under discussion before defaulting,
            # so "explain that again" does not silently become a variables lesson.
            topic = self._extract_topic(message) or context.get("last_topic") or "variables"
            lesson = teach_python_concept(topic=topic, level=level, learning_style=style)
            examples = "\n".join(lesson["code_examples"])
            mistakes = ", ".join(lesson["common_mistakes"])
            return (
                prefix
                + f"Topic: {lesson['topic']}\n\n"
                f"{lesson['explanation']}\n\n"
                f"Analogy: {lesson['real_world_analogy']}\n\n"
                f"Example(s):\n{examples}\n\n"
                f"Common mistakes: {mistakes}\n\n"
                f"Practice: {lesson['practice_exercise']}\n"
            )

        if agent_name == "practice":
            from .practice_agent import generate_python_exercise

            topic = self._extract_topic(message) or context.get("last_topic") or "variables"
            difficulty = self._pick_difficulty(level, progress)
            ex = generate_python_exercise(topic=topic, level=level, difficulty=difficulty)
            hints = "\n- " + "\n- ".join(ex["hints"])
            return (
                prefix
                + f"Exercise: {ex['topic']} ({ex['difficulty']})\n\n"
                f"Problem: {ex['problem_statement']}\n\n"
                f"Hints:{hints}\n\n"
                f"Success criteria: {', '.join(ex['success_criteria'])}\n\n"
                f"Estimated time: {ex['estimated_time']}\n"
            )

        if agent_name == "curriculum":
            from .curriculum_agent import generate_python_curriculum

            cur = generate_python_curriculum(level)
            weeks = "\n".join(
                f"Week {w['week']}: {w['topic']} -> Practice: {w['practice']}"
                for w in cur["weekly_plan"]
            )
            return (
                prefix
                + f"{cur['curriculum_title']}\n"
                f"{cur['description']}\n\n"
                f"{weeks}\n\n"
                f"Pace: {cur['recommended_pace']}\n"
                f"Resources: {', '.join(cur['recommended_resources'])}\n"
            )

        if agent_name == "progress":
            from .progress_agent import generate_progress_report, track_learning_progress

            topics = progress.get("topics_learned", []) or []
            completed = int(progress.get("exercises_completed", 0))
            delivered = int(progress.get("exercises_delivered", 0))
            topics_csv = ", ".join(topics)

            tracked = track_learning_progress(
                user_id=user_id,
                topics_learned=topics_csv,
                exercises_completed=completed,
                current_level=level,
            )
            rep = generate_progress_report(
                user_id=user_id,
                topics_learned=topics_csv,
                exercises_completed=completed,
                days_active=max(1, int(progress.get("interactions", 1)) // 5 or 1),
            )
            recommendations = "\n- " + "\n- ".join(tracked["insights"]["recommendations"])
            return (
                prefix
                + f"Report date: {rep['report_date']}\n"
                f"Level: {level}\n"
                f"Topics studied ({len(topics)}): {topics_csv or 'none yet'}\n"
                f"Exercises delivered: {delivered}\n"
                f"Exercises completed: {completed}\n"
                f"Badge: {tracked['gamification']['badge']} ({tracked['gamification']['achievement']})\n"
                f"Pace: {rep['analysis']['pace']}\n"
                f"Recommendations:{recommendations}\n"
            )

        return f"{prefix}Please try again."

    @staticmethod
    def _pick_difficulty(level: str, progress: Dict[str, Any]) -> str:
        """Step difficulty up as the learner completes work, instead of always 'easy'."""
        completed = int(progress.get("exercises_completed", 0))
        if level == "advanced":
            return "hard"
        if level == "intermediate":
            return "hard" if completed >= 5 else "medium"
        return "medium" if completed >= 3 else "easy"
