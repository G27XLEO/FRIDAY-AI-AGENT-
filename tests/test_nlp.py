import unittest

from friday_agent.nlp import analyze, build_context


class NLPTests(unittest.TestCase):
    def test_intent_and_urgency(self) -> None:
        result = analyze("FRIDAY, check the GitHub repository urgently")
        self.assertEqual(result.intent, "code")
        self.assertEqual(result.urgency, "high")
        self.assertIn("GitHub", result.entities)

    def test_url_entity(self) -> None:
        result = analyze("open https://github.com/G27XLEO/FRIDAY-AI-AGENT-")
        self.assertEqual(result.intent, "web")
        self.assertTrue(any(entity.startswith("https://") for entity in result.entities))

    def test_context_is_compact(self) -> None:
        context = build_context("what is the system status?")
        self.assertIn("intent=status", context)
        self.assertIn("normalized_request=what is the system status?", context)


if __name__ == "__main__":
    unittest.main()
