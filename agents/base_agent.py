# agents/base_agent.py
"""Shared Gemini agent plumbing.

All five coach agents share the same call pattern: one client, a tool list, a
system instruction, and a query() that turns a learner turn into text. The only
differences are the tools and the instruction, so that is all a subclass sets.

Two things this module deliberately owns, because getting them wrong is what
made the coach feel broken:

1. Errors are raised as `AgentCallError` with a machine-readable `kind`, instead
   of being swallowed into a `"Agent Error: ..."` string. The coordinator needs
   the kind to decide whether a retry can possibly help.
2. `query()` accepts the conversation so far, so the model can answer follow-ups
   like "explain that again more simply" instead of seeing each turn cold.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Sequence

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"

# Tried in order when the primary model is out of quota. Free-tier quota is
# metered per model, so a smaller sibling is usually still available.
DEFAULT_FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]

# How many prior turns to replay to the model. Enough for real follow-ups,
# small enough to keep token cost predictable.
HISTORY_TURNS = 8


def resolve_model_id() -> str:
    """Model for every agent, from env, with ADK_MODEL kept for compatibility."""
    return os.getenv("ADK_MODEL") or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


def resolve_fallback_models(primary: str) -> List[str]:
    """Ordered fallback models, honouring GEMINI_FALLBACK_MODELS if set."""
    configured = os.getenv("GEMINI_FALLBACK_MODELS", "")
    candidates = (
        [m.strip() for m in configured.split(",") if m.strip()]
        if configured
        else list(DEFAULT_FALLBACK_MODELS)
    )
    return [m for m in candidates if m != primary]


class AgentCallError(RuntimeError):
    """A Gemini call failed, tagged with why so callers can react correctly."""

    def __init__(self, kind: str, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.kind = kind
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        """Only transient server-side conditions are worth trying again."""
        return self.kind in ("rate_limit", "server_error", "timeout")

    @property
    def try_other_model(self) -> bool:
        """Quota is metered per model, so another model may still answer."""
        return self.kind in ("quota_exhausted", "rate_limit", "model_not_found")


def classify_error(exc: BaseException) -> AgentCallError:
    """Turn an SDK exception into an AgentCallError with a usable `kind`.

    The google-genai SDK reports most failures as one exception type with the
    HTTP status embedded in the message, so the status is read back out of the
    text. Quota exhaustion is split out from ordinary rate limiting because the
    two need opposite handling: a per-minute limit clears on its own, a daily
    quota does not clear within a request.
    """
    text = str(exc)
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status is None:
        match = re.search(r"\b(4\d\d|5\d\d)\b", text)
        status = int(match.group(1)) if match else None

    retry_after = None
    delay = re.search(r"retry in ([\d.]+)s", text, re.IGNORECASE) or re.search(
        r"'retryDelay': '(\d+)s'", text
    )
    if delay:
        try:
            retry_after = float(delay.group(1))
        except ValueError:
            retry_after = None

    if status == 429 or "RESOURCE_EXHAUSTED" in text:
        per_day = "PerDay" in text or "generate_content_free_tier_requests" in text
        kind = "quota_exhausted" if per_day else "rate_limit"
        return AgentCallError(kind, text, retry_after)
    if status in (401, 403) or "PERMISSION_DENIED" in text or "API_KEY_INVALID" in text:
        return AgentCallError("auth_error", text)
    if status == 404 or "NOT_FOUND" in text:
        return AgentCallError("model_not_found", text)
    if status == 400:
        return AgentCallError("bad_request", text)
    if status is not None and status >= 500:
        return AgentCallError("server_error", text, retry_after)
    if "timeout" in text.lower() or "deadline" in text.lower():
        return AgentCallError("timeout", text)
    return AgentCallError("unknown", text)


def build_contents(message: str, history: Optional[Sequence[Dict[str, Any]]] = None) -> List[Any]:
    """Build a multi-turn `contents` list so the model can see the conversation.

    `history` is the coordinator's turn log: dicts with a `role` of "user" or
    "coach" and a `text` body. Anything unusable is skipped rather than raising,
    because a malformed stored turn should never cost the learner a reply.
    """
    contents: List[Any] = []
    for turn in list(history or [])[-HISTORY_TURNS * 2 :]:
        if not isinstance(turn, dict):
            continue
        text = str(turn.get("text") or "").strip()
        if not text:
            continue
        role = "model" if turn.get("role") in ("coach", "model", "assistant") else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=text[:4000])]))

    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


class BaseGenAIAgent:
    """One Gemini-backed coach agent.

    Subclasses set `name`, `tools`, and `system_instruction`.
    """

    name: str = "agent"
    tools: Sequence[Any] = ()
    system_instruction: str = ""

    def __init__(self, client: genai.Client, model_id: Optional[str] = None):
        self.client = client
        self.model_id = model_id or resolve_model_id()
        self.fallback_models = resolve_fallback_models(self.model_id)
        # Set after a successful call so the coordinator can report which model
        # actually answered when the primary one was out of quota.
        self.last_model_used: Optional[str] = None

    def _config(self, profile_note: str) -> types.GenerateContentConfig:
        instruction = self.system_instruction
        if profile_note:
            instruction = f"{instruction}\n\nLearner profile:\n{profile_note}"
        return types.GenerateContentConfig(
            tools=list(self.tools),
            system_instruction=instruction,
            # Tool results are meant to be narrated to the learner, so let the
            # SDK finish the loop and hand back prose rather than a raw call.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=4
            ),
        )

    def query(
        self,
        message: str,
        history: Optional[Sequence[Dict[str, Any]]] = None,
        profile_note: str = "",
    ) -> str:
        """Answer one learner turn.

        Raises AgentCallError on failure. Returning an error string instead
        would make the caller parse prose to find out what went wrong, which is
        exactly how the original code ended up retrying unretryable errors.
        """
        contents = build_contents(message, history)
        config = self._config(profile_note)

        models = [self.model_id] + self.fallback_models
        last_error: Optional[AgentCallError] = None

        for model in models:
            try:
                response = self.client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except Exception as exc:  # noqa: BLE001 - re-raised as AgentCallError
                last_error = classify_error(exc)
                if not last_error.try_other_model:
                    raise last_error
                continue

            text = (response.text or "").strip()
            if not text:
                # A tool call with no narration leaves the learner with a blank
                # bubble, which reads as a crash. Treat it as a failed attempt.
                last_error = AgentCallError("empty_response", f"{model} returned no text")
                continue

            self.last_model_used = model
            return text

        raise last_error or AgentCallError("unknown", "No model produced a response")
