"""Tests for the Gemini failure handling that made the coach look broken.

The original code retried every error three times with a sub-second backoff and
then replaced the reason with "Gemini is unavailable right now". Each retry spent
real free-tier quota, so a quota error caused more quota errors.
"""

import asyncio
import os
import unittest

os.environ["LOCAL_ONLY"] = "1"

from agents.base_agent import AgentCallError, build_contents, classify_error
from agents.coordinator import LearningCoachCoordinator

QUOTA_MESSAGE = (
    "429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'You exceeded your "
    "current quota. Quota exceeded for metric: "
    "generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 20, "
    "model: gemini-2.5-flash Please retry in 16.244761397s.', "
    "'status': 'RESOURCE_EXHAUSTED', 'details': [{'@type': "
    "'type.googleapis.com/google.rpc.QuotaFailure', 'violations': [{'quotaId': "
    "'GenerateRequestsPerDayPerProjectPerModel-FreeTier'}]}]}}"
)


class ClassifyErrorTests(unittest.TestCase):
    def test_daily_quota_is_not_retryable(self):
        err = classify_error(Exception(QUOTA_MESSAGE))
        self.assertEqual(err.kind, "quota_exhausted")
        self.assertFalse(err.retryable)
        # Quota is metered per model, so another model is still worth trying.
        self.assertTrue(err.try_other_model)

    def test_retry_delay_is_read_from_the_server_response(self):
        err = classify_error(Exception(QUOTA_MESSAGE))
        self.assertAlmostEqual(err.retry_after, 16.244761397, places=3)

    def test_plain_rate_limit_is_retryable(self):
        err = classify_error(Exception("429 RESOURCE_EXHAUSTED: too many requests per minute"))
        self.assertEqual(err.kind, "rate_limit")
        self.assertTrue(err.retryable)

    def test_auth_errors_are_terminal(self):
        for message in ("403 PERMISSION_DENIED", "400 API_KEY_INVALID"):
            err = classify_error(Exception(message))
            self.assertEqual(err.kind, "auth_error", message)
            self.assertFalse(err.retryable)
            self.assertFalse(err.try_other_model)

    def test_missing_model_tries_another_model(self):
        err = classify_error(Exception("404 NOT_FOUND: model not found"))
        self.assertEqual(err.kind, "model_not_found")
        self.assertTrue(err.try_other_model)

    def test_server_errors_are_retryable(self):
        err = classify_error(Exception("503 Service Unavailable"))
        self.assertEqual(err.kind, "server_error")
        self.assertTrue(err.retryable)


class BuildContentsTests(unittest.TestCase):
    def test_history_becomes_alternating_turns(self):
        history = [
            {"role": "user", "text": "explain loops"},
            {"role": "coach", "text": "Loops repeat work"},
        ]
        contents = build_contents("simpler please", history)
        self.assertEqual([c.role for c in contents], ["user", "model", "user"])
        self.assertEqual(contents[-1].parts[0].text, "simpler please")

    def test_malformed_history_entries_are_skipped(self):
        contents = build_contents("hi", [None, {}, {"role": "user", "text": ""}, "junk"])
        self.assertEqual(len(contents), 1)


class FakeAgent:
    """Stands in for a Gemini-backed agent so no network call is made."""

    def __init__(self, error=None, reply="live reply"):
        self.error = error
        self.reply = reply
        self.calls = 0
        self.last_model_used = "gemini-test"
        self.received = []

    def query(self, message, history=None, profile_note=""):
        self.calls += 1
        self.received.append({"message": message, "history": history, "profile": profile_note})
        if self.error:
            raise self.error
        return self.reply


class RetryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.coord = LearningCoachCoordinator()
        self.coord.mode = "gemini_api_key"
        self.coord.agents = {name: None for name in self.coord._agent_names()}

    def _run(self, agent_name, message, user_id="retry_user"):
        return asyncio.run(self.coord.process_with_agent(agent_name, message, user_id))

    def test_quota_error_is_not_retried(self):
        agent = FakeAgent(error=classify_error(Exception(QUOTA_MESSAGE)))
        self.coord.agents["teaching"] = agent
        text = self._run("teaching", "explain loops")

        # One attempt only. Retrying spends quota on a call already refused.
        self.assertEqual(agent.calls, 1)
        self.assertEqual(self.coord.last_error["kind"], "quota_exhausted")
        # The learner is told why, instead of getting a bare "unavailable".
        self.assertIn("quota", text.lower())
        self.assertIn("Topic: loops", text)

    def test_long_server_retry_hint_skips_the_wait(self):
        agent = FakeAgent(
            error=AgentCallError("rate_limit", "429 slow down", retry_after=45.0)
        )
        self.coord.agents["teaching"] = agent
        self._run("teaching", "explain loops")
        # 45s is longer than a learner will wait, so fall back immediately.
        self.assertEqual(agent.calls, 1)

    def test_short_retry_hint_is_retried_once(self):
        agent = FakeAgent(error=AgentCallError("rate_limit", "429", retry_after=0.01))
        self.coord.agents["teaching"] = agent
        self._run("teaching", "explain loops")
        self.assertEqual(agent.calls, 2)

    def test_circuit_breaker_stops_calling_after_repeated_quota_errors(self):
        agent = FakeAgent(error=classify_error(Exception(QUOTA_MESSAGE)))
        self.coord.agents["teaching"] = agent

        for _ in range(4):
            self._run("teaching", "explain loops")

        # Threshold is 2, so calls stop after the breaker opens rather than
        # burning one request of quota per learner turn.
        self.assertEqual(agent.calls, 2)
        self.assertTrue(self.coord.health_snapshot()["api_paused"])
        self.assertTrue(self.coord.health_snapshot()["degraded"])

    def test_successful_call_clears_the_error_state(self):
        agent = FakeAgent()
        self.coord.agents["teaching"] = agent
        self.coord.last_error = {"kind": "quota_exhausted", "message": "old"}

        text = self._run("teaching", "explain loops")
        self.assertEqual(text, "live reply")
        self.assertIsNone(self.coord.last_error)
        self.assertFalse(self.coord.health_snapshot()["degraded"])

    def test_agent_receives_history_and_profile(self):
        agent = FakeAgent()
        self.coord.agents["teaching"] = agent
        self.coord.update_context("mem_user", {"skill_level": "intermediate"})

        self._run("teaching", "explain loops", user_id="mem_user")
        self._run("teaching", "now simpler", user_id="mem_user")

        second = agent.received[1]
        replayed = [turn["text"] for turn in second["history"]]
        self.assertIn("explain loops", replayed)
        self.assertIn("live reply", replayed)
        self.assertIn("intermediate", second["profile"])

    def test_simplify_followup_is_expanded_with_the_last_topic(self):
        agent = FakeAgent()
        self.coord.agents["teaching"] = agent
        self.coord.update_context("rw_user", {"last_topic": "dictionaries"})

        self._run("teaching", "explain that in simpler terms", user_id="rw_user")
        self.assertIn("dictionaries", agent.received[0]["message"])

    def test_unexpected_exception_still_returns_content(self):
        agent = FakeAgent(error=ValueError("boom"))
        self.coord.agents["teaching"] = agent
        text = self._run("teaching", "explain loops")
        self.assertIn("Topic: loops", text)
        self.assertEqual(self.coord.last_error["kind"], "unknown")


class PromptWiringTests(unittest.TestCase):
    """agents/prompts.py used to be dead code; editing it changed nothing."""

    def test_every_agent_uses_the_shared_prompt_table(self):
        from agents.assessment_agent import GenAIAssessmentAgent
        from agents.curriculum_agent import GenAICurriculumAgent
        from agents.practice_agent import GenAIPracticeAgent
        from agents.progress_agent import GenAIProgressAgent
        from agents.prompts import AGENT_PROMPTS
        from agents.teaching_agent import GenAITeachingAgent

        classes = [
            GenAIAssessmentAgent,
            GenAICurriculumAgent,
            GenAITeachingAgent,
            GenAIPracticeAgent,
            GenAIProgressAgent,
        ]
        self.assertEqual({c.name for c in classes}, set(AGENT_PROMPTS))
        for cls in classes:
            self.assertIs(cls.system_instruction, AGENT_PROMPTS[cls.name], cls.name)


class ContextMigrationTests(unittest.TestCase):
    def test_legacy_stored_context_is_upgraded(self):
        coord = LearningCoachCoordinator()
        legacy = {
            "skill_level": "beginner",
            "history": [{"agent": "teaching", "message": "explain loops"}],
            "progress": {"topics_learned": ["loops"], "exercises_completed": 2},
        }
        context = coord._normalize_context(legacy)

        self.assertEqual(context["history"][0]["role"], "user")
        self.assertEqual(context["history"][0]["text"], "explain loops")
        # Counter added after this document was written must default, not crash.
        self.assertEqual(context["progress"]["exercises_delivered"], 0)
        self.assertEqual(context["progress"]["exercises_completed"], 2)


if __name__ == "__main__":
    unittest.main()
