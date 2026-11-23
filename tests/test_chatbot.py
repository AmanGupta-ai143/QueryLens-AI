import unittest

from errors import ValidationError
from nlp.chatbot_engine import FALLBACK_MESSAGE, ChatbotEngine
from tests.helpers import sample_faqs

ADMISSION_Q = "How can I apply for admission?"


class ChatbotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.faqs = sample_faqs()
        cls.engine = ChatbotEngine(cls.faqs)
        cls.admission = next(f for f in cls.faqs if f["question"] == ADMISSION_Q)

    def assert_answers_admission(self, question):
        r = self.engine.answer(question)
        self.assertTrue(r.answered, f"{question!r} scored {r.score}")
        self.assertEqual(r.matched_faq["id"], self.admission["id"])
        self.assertEqual(r.response, self.admission["answer"])
        self.assertEqual(r.predicted_category, "Admissions")

    def test_1_exact_question(self):
        r = self.engine.answer(ADMISSION_Q)
        self.assertTrue(r.exact_match)
        self.assert_answers_admission(ADMISSION_Q)

    def test_2_different_wording(self):
        self.assert_answers_admission("I want to know the admission application process.")
        self.assert_answers_admission("How can I get admission to the college?")

    def test_3_spelling_mistakes(self):
        self.assert_answers_admission("adimssion aplication procces")

    def test_4_extra_spaces(self):
        self.assert_answers_admission("   How   can  I   apply    for   admission?   ")

    def test_5_different_capitalization(self):
        self.assert_answers_admission("hOw CaN i ApPlY fOr AdMiSsIoN")
        self.assertEqual(self.engine.answer("HOW CAN I APPLY FOR ADMISSION").score,
                         self.engine.answer("how can i apply for admission").score)

    def test_6_unrelated_question_is_not_forced(self):
        for q in ["What is the weather like today?", "who is the prime minister of india",
                  "best pizza near me", "bitcoin price"]:
            r = self.engine.answer(q)
            self.assertFalse(r.answered, q)
            self.assertEqual(r.response, FALLBACK_MESSAGE)
            self.assertIsNone(r.matched_faq)

    def test_7_empty_question(self):
        for q in ["", "   ", None]:
            with self.assertRaises(ValidationError):
                self.engine.answer(q)

    def test_only_stopwords_gets_fallback(self):
        r = self.engine.answer("how can i")
        self.assertFalse(r.answered)
        self.assertEqual(r.status, "no_terms")

    def test_other_categories_are_detected(self):
        cases = {
            "what is the minimum attendance for exams": "Attendance",
            "how do i download hall ticket": "Examinations",
            "i forgot my password": "Technical Support",
            "library timings": "Library",
            "tell me about hostel food": "Hostel",
        }
        for q, category in cases.items():
            r = self.engine.answer(q)
            self.assertTrue(r.answered, q)
            self.assertEqual(r.predicted_category, category, q)

    def test_threshold_is_configurable(self):
        q = "How can I get admission to the college?"
        self.assertTrue(self.engine.answer(q, threshold=0.2).answered)
        self.assertFalse(self.engine.answer(q, threshold=0.95).answered)

    def test_explainability_fields(self):
        r = self.engine.answer(ADMISSION_Q)
        self.assertEqual(len(r.candidates), 3)
        self.assertGreaterEqual(r.candidates[0].score, r.candidates[1].score)
        self.assertTrue(r.term_weights)
        self.assertIn("Admissions", r.category_scores)

    def test_empty_knowledge_base(self):
        r = ChatbotEngine([]).answer("anything")
        self.assertFalse(r.answered)
        self.assertEqual(r.status, "empty_kb")

    def test_engine_reload_picks_up_new_faq(self):
        engine = ChatbotEngine(self.faqs[:5])
        q = "what is the fine for late return of library books"
        self.assertFalse(engine.answer(q).answered)
        engine.load(self.faqs)
        self.assertTrue(engine.answer(q).answered)


if __name__ == "__main__":
    unittest.main()
