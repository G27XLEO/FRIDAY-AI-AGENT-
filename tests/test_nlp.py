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

    def test_word_boundary_matching(self) -> None:
        """Verify keyword matching uses word boundaries to avoid partial matches."""
        # "understanding" should NOT match "status" keyword
        result = analyze("help me understand this")
        self.assertNotEqual(result.intent, "status")
        
        # But "status" alone should match
        result = analyze("check status")
        self.assertEqual(result.intent, "status")

    def test_empty_input_handling(self) -> None:
        """Verify empty/whitespace input is handled gracefully."""
        result = analyze("")
        self.assertEqual(result.text, "")
        self.assertEqual(result.normalized, "")
        self.assertEqual(result.intent, "general")
        self.assertEqual(result.urgency, "normal")
        self.assertEqual(result.entities, ())

    def test_whitespace_only_input(self) -> None:
        """Verify whitespace-only input is handled gracefully."""
        result = analyze("   \t\n  ")
        self.assertEqual(result.text, "")
        self.assertEqual(result.normalized, "")
        self.assertEqual(result.intent, "general")

    def test_url_boundary_checking(self) -> None:
        """Verify URL pattern doesn't capture trailing punctuation."""
        result = analyze("Check this (https://github.com/test) site")
        urls = [e for e in result.entities if e.startswith("https://")]
        self.assertEqual(len(urls), 1)
        # URL should not include the closing parenthesis
        self.assertFalse(urls[0].endswith(")"))

    def test_context_formatting(self) -> None:
        """Verify build_context produces valid structured output."""
        context = build_context("urgent status check")
        lines = context.split("\n")
        self.assertEqual(lines[0], "NLP CONTEXT")
        self.assertTrue(any("intent=" in line for line in lines))
        self.assertTrue(any("urgency=" in line for line in lines))
        self.assertTrue(any("entities=" in line for line in lines))
        self.assertTrue(any("normalized_request=" in line for line in lines))

    def test_multiple_urgent_keywords(self) -> None:
        """Verify urgency detection works with various keywords."""
        for urgent_word in ["urgent", "asap", "immediately", "critical", "emergency"]:
            result = analyze(f"please {urgent_word} do this")
            self.assertEqual(result.urgency, "high", f"Failed for word: {urgent_word}")

    def test_entity_limit(self) -> None:
        """Verify entity extraction respects 12-item limit."""
        # Build a string with many URLs
        urls = [f"https://example{i}.com" for i in range(20)]
        text = " ".join(urls)
        result = analyze(text)
        self.assertLessEqual(len(result.entities), 12)


if __name__ == "__main__":
    unittest.main()
