import unittest

import numpy as np

from nlp.chatbot_engine import ChatbotEngine, validate_threshold
from nlp.preprocessing import preprocess
from nlp.similarity import combine_scores, cosine_scores, top_k_indices
from nlp.vectorizer import FAQVectorizer
from errors import ValidationError
from tests.helpers import sample_faqs


class SimilarityTests(unittest.TestCase):
    def setUp(self):
        self.faqs = sample_faqs()
        docs = [preprocess(f"{f['question']} {f['keywords']}") for f in self.faqs]
        self.vec = FAQVectorizer().fit(docs)

    def test_identical_text_scores_close_to_one(self):
        q = preprocess(f"{self.faqs[0]['question']} {self.faqs[0]['keywords']}")
        w, c = self.vec.transform(q)
        self.assertAlmostEqual(cosine_scores(w, self.vec.word_matrix)[0], 1.0, places=5)
        self.assertAlmostEqual(cosine_scores(c, self.vec.char_matrix)[0], 1.0, places=5)

    def test_scores_are_between_zero_and_one(self):
        w, c = self.vec.transform(preprocess("library books borrow"))
        for s in (cosine_scores(w, self.vec.word_matrix), cosine_scores(c, self.vec.char_matrix)):
            self.assertTrue(((s >= 0) & (s <= 1.0000001)).all())

    def test_query_without_known_words_scores_zero_on_word_level(self):
        w, _ = self.vec.transform(preprocess("zzzz qqqq"))
        self.assertEqual(float(cosine_scores(w, self.vec.word_matrix).max()), 0.0)

    def test_combine_scores(self):
        out = combine_scores([0.5, 0.0], [0.5, 0.4], 0.6, 0.4)
        self.assertAlmostEqual(out[0], 0.5)
        self.assertAlmostEqual(out[1], 0.4 * 0.85)  # spelling-tolerance floor applies
        with self.assertRaises(ValueError):
            combine_scores([1], [1], 0, 0)

    def test_top_k_is_sorted_descending(self):
        idx = top_k_indices(np.array([0.1, 0.9, 0.5, 0.7]), 3)
        self.assertEqual(idx, [1, 3, 2])

    def test_engine_score_is_calculated_not_hardcoded(self):
        e = ChatbotEngine(self.faqs)
        exact = e.answer("How can I apply for admission?").score
        paraphrase = e.answer("I want to know the admission application process").score
        unrelated = e.answer("What is the weather like today").score
        self.assertGreater(exact, 0.5)
        self.assertGreater(paraphrase, 0.35)
        self.assertLess(unrelated, 0.2)

    def test_threshold_validation(self):
        self.assertEqual(validate_threshold("0.4"), 0.4)
        for bad in [-0.1, 1.5, "abc", None]:
            with self.assertRaises(ValidationError):
                validate_threshold(bad)


if __name__ == "__main__":
    unittest.main()
