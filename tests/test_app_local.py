import os
import unittest

os.environ["LOCAL_ONLY"] = "1"

from main import app, coordinator, determine_agent, is_greeting_only


class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_reports_local_mode(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["mode"], "local")
        self.assertEqual(data["agents_count"], 5)
        self.assertFalse(data["degraded"])

    def test_chat_routes_and_updates_context(self):
        response = self.client.post(
            "/chat",
            json={"message": "Give me a practice exercise on loops", "user_id": "unit_user"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["agent_used"], "practice")
        self.assertEqual(data["source"], "local")
        self.assertIn("Problem:", data["response"])
        self.assertEqual(data["context"]["last_agent"], "practice")
        self.assertEqual(data["context"]["progress"]["exercises_delivered"], 1)
        context = coordinator.get_user_context("unit_user")
        self.assertEqual(context["last_agent"], "practice")
        self.assertIn("last_exercise", context)

    def test_reset_clears_context(self):
        coordinator.update_context("reset_user", {"skill_level": "beginner"})
        response = self.client.post("/reset", json={"user_id": "reset_user"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["context"]["skill_level"], "unknown")
        self.assertEqual(data["context"]["history_count"], 0)

    def test_context_endpoint_returns_public_state(self):
        response = self.client.get("/context/unit_user")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("progress", data["context"])

    def test_empty_message_rejected(self):
        response = self.client.post("/chat", json={"message": "   "})
        self.assertEqual(response.status_code, 400)

    def test_oversized_message_rejected_before_api_call(self):
        response = self.client.post("/chat", json={"message": "x" * 5000})
        self.assertEqual(response.status_code, 413)
        self.assertIn("too long", response.get_json()["error"])


class RouterTests(unittest.TestCase):
    """Regression tests for the substring-matching router bugs."""

    def test_greeting_does_not_match_substrings(self):
        self.assertEqual(determine_agent("This is a dictionary question", "route_user"), "assessment")
        self.assertEqual(determine_agent("hi", "route_user"), "assessment")

    def test_explanation_is_not_a_curriculum_request(self):
        # "explanation" contains "plan", which used to route this to curriculum.
        for message in ("Give me an explanation of loops", "I need a clear explanation"):
            self.assertEqual(determine_agent(message, "route_user"), "teaching", message)

    def test_multitask_is_not_a_practice_request(self):
        # "multitask" contains "task", which used to route this to practice.
        self.assertNotEqual(determine_agent("I want to multitask", "route_user"), "practice")

    def test_explicit_request_beats_greeting_prefix(self):
        self.assertEqual(
            determine_agent("hello, give me a practice exercise on loops", "route_user"),
            "practice",
        )
        self.assertEqual(
            determine_agent("hi there, can you explain what a list is", "route_user"),
            "teaching",
        )

    def test_explicit_request_beats_help_phrasing(self):
        self.assertEqual(determine_agent("help me practice loops", "route_user"), "practice")

    def test_bare_help_routes_to_teaching(self):
        for message in ("I don't know", "I'm stuck", "I am confused"):
            self.assertEqual(determine_agent(message, "route_user"), "teaching", message)

    def test_simplify_routes_to_teaching(self):
        self.assertEqual(determine_agent("explain that in simpler terms", "route_user"), "teaching")

    def test_wanting_to_start_python_gets_a_roadmap(self):
        self.assertEqual(
            determine_agent("I want to start learning Python", "route_user"), "curriculum"
        )

    def test_keyword_routing_table(self):
        cases = [
            ("Show my progress and badges", "progress"),
            ("Create a 4-week roadmap", "curriculum"),
            ("What is a dictionary in Python?", "teaching"),
            ("Assess my skill level", "assessment"),
            ("Give me a challenge", "practice"),
        ]
        for message, expected in cases:
            self.assertEqual(determine_agent(message, "route_user"), expected, message)

    def test_conversation_recall_questions_go_to_teaching(self):
        for message in (
            "what topic have we been discussing?",
            "remind me what we covered",
            "recap what I have learned",
        ):
            self.assertEqual(determine_agent(message, "route_user"), "teaching", message)

    def test_unknown_level_stops_forcing_assessment_late_in_a_session(self):
        uid = "late_user"
        coordinator.reset_user_context(uid)
        context = coordinator.get_user_context(uid)
        # Several turns in, still unknown level: an unmatched message should not
        # loop back into another assessment.
        context["history"] = [{"role": "user", "text": "x"} for _ in range(6)]
        self.assertNotEqual(determine_agent("tell me something interesting", uid), "assessment")

    def test_greeting_only_detection(self):
        for message in ("hi", "hello there", "hey coach", "good morning!"):
            self.assertTrue(is_greeting_only(message), message)
        for message in ("hi, explain loops", "hello I need a roadmap", "what is a list"):
            self.assertFalse(is_greeting_only(message), message)


class ContextTrackingTests(unittest.TestCase):
    """Regression tests for the learner-state bugs."""

    def setUp(self):
        self.uid = f"ctx_{self._testMethodName}"
        coordinator.reset_user_context(self.uid)

    def _record(self, agent, message, response):
        context = coordinator.get_user_context(self.uid)
        coordinator._record_response_context(
            self.uid, context, agent, message, response, "local"
        )
        return context

    def test_skill_level_uses_explicit_marker_not_first_word(self):
        # The reply names all three levels; only the marker line counts.
        context = self._record(
            "assessment",
            "I have 10 years of Python experience",
            "Levels are beginner, intermediate, advanced.\nSkill Level: advanced",
        )
        self.assertEqual(context["skill_level"], "advanced")

    def test_skill_level_falls_back_to_self_description(self):
        context = self._record(
            "assessment",
            "I am an expert with years of experience",
            "Nice to meet you. Here are the levels: beginner, intermediate, advanced.",
        )
        self.assertEqual(context["skill_level"], "advanced")

    def test_skill_level_stays_unknown_without_evidence(self):
        context = self._record(
            "assessment",
            "hello",
            "Hi! Levels are beginner, intermediate, advanced. What is your experience?",
        )
        self.assertEqual(context["skill_level"], "unknown")

    def test_recommended_topics_are_not_marked_as_learned(self):
        # An assessment listing recommended topics is not the learner studying them.
        context = self._record(
            "assessment",
            "hello",
            "Recommended topics: variables, data types.\nSkill Level: unknown",
        )
        self.assertEqual(context["progress"]["topics_learned"], [])

    def test_taught_topic_is_marked_as_learned(self):
        context = self._record("teaching", "explain loops", "Loops repeat work...")
        self.assertIn("loops", context["progress"]["topics_learned"])

    def test_delivered_and_completed_exercises_are_counted_separately(self):
        context = self._record("practice", "give me an exercise on lists", "Problem: ...")
        self.assertEqual(context["progress"]["exercises_delivered"], 1)
        self.assertEqual(context["progress"]["exercises_completed"], 0)

        context = self._record("teaching", "I solved it, here is my code", "Nice work!")
        self.assertEqual(context["progress"]["exercises_completed"], 1)

    def test_topic_matching_ignores_unrelated_words(self):
        self.assertIsNone(coordinator._extract_topic("I like to listen to music"))
        self.assertIsNone(coordinator._extract_topic("please classify this"))
        self.assertEqual(coordinator._extract_topic("explain lists"), "lists")

    def test_history_records_both_sides_of_the_exchange(self):
        context = self._record("teaching", "explain loops", "Loops repeat work...")
        roles = [turn["role"] for turn in context["history"]]
        self.assertIn("coach", roles)


class LocalFallbackTests(unittest.TestCase):
    """The local content must reflect real learner state, not hard-coded values."""

    def setUp(self):
        self.uid = f"fb_{self._testMethodName}"
        coordinator.reset_user_context(self.uid)

    def test_progress_report_does_not_invent_activity(self):
        text = coordinator._local_fallback("progress", "show my progress", self.uid)
        self.assertIn("Topics studied (0)", text)
        self.assertIn("Exercises completed: 0", text)
        # The old hard-coded report always claimed these.
        self.assertNotIn("variables, loops", text)

    def test_progress_report_uses_real_counters(self):
        coordinator.update_context(
            self.uid,
            {
                "skill_level": "intermediate",
                "progress": {
                    "topics_learned": ["loops", "functions"],
                    "exercises_delivered": 4,
                    "exercises_completed": 3,
                    "interactions": 9,
                },
            },
        )
        text = coordinator._local_fallback("progress", "show my progress", self.uid)
        self.assertIn("Topics studied (2)", text)
        self.assertIn("loops, functions", text)
        self.assertIn("Exercises completed: 3", text)
        self.assertIn("Level: intermediate", text)

    def test_teaching_fallback_keeps_the_current_topic(self):
        coordinator.update_context(self.uid, {"last_topic": "dictionaries"})
        text = coordinator._local_fallback("teaching", "explain that again", self.uid)
        self.assertIn("Topic: dictionaries", text)

    def test_practice_difficulty_follows_level_and_history(self):
        coordinator.update_context(self.uid, {"skill_level": "advanced"})
        text = coordinator._local_fallback("practice", "exercise on loops", self.uid)
        self.assertIn("hard", text)

    def test_curriculum_fallback_uses_assessed_level(self):
        coordinator.update_context(self.uid, {"skill_level": "intermediate"})
        text = coordinator._local_fallback("curriculum", "make me a plan", self.uid)
        self.assertIn("Python Developer Path", text)


if __name__ == "__main__":
    unittest.main()
