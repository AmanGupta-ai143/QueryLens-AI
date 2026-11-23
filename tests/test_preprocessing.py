import unittest

from errors import ValidationError
from nlp.preprocessing import STOPWORDS, clean_text, preprocess, remove_stopwords, validate_question
from nlp.tokenizer import stem, tokenize


class PreprocessingTests(unittest.TestCase):
    def test_lowercase(self):
        self.assertEqual(clean_text("HOW Can I APPLY"), "how can i apply")

    def test_punctuation_and_special_characters_removed(self):
        self.assertEqual(clean_text("Fees?? (B.Tech) @ #Nova!!"), "fees b tech nova")

    def test_extra_whitespace_collapsed(self):
        self.assertEqual(clean_text("  how   can \t i\n apply  "), "how can i apply")

    def test_possessive_and_apostrophes(self):
        self.assertEqual(clean_text("the university's portal, don't"), "the university portal dont")

    def test_urls_removed(self):
        self.assertEqual(clean_text("see https://example.com/x now"), "see now")

    def test_none_and_empty(self):
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text("   "), "")

    def test_tokenization(self):
        self.assertEqual(tokenize("how can i apply"), ["how", "can", "i", "apply"])
        self.assertEqual(tokenize(""), [])

    def test_stopword_removal(self):
        tokens = tokenize("how can i apply for admission")
        self.assertEqual(remove_stopwords(tokens), ["apply", "admission"])
        self.assertIn("the", STOPWORDS)
        self.assertNotIn("not", STOPWORDS)  # negations are kept

    def test_stemming_groups_word_forms(self):
        self.assertEqual(stem("fees"), stem("fee"))
        self.assertEqual(stem("exams"), stem("exam"))
        self.assertEqual(stem("applying"), stem("applied"))
        self.assertEqual(stem("2024"), "2024")

    def test_full_pipeline(self):
        r = preprocess("  I want to know the ADMISSION application   process!! ")
        self.assertEqual(r.cleaned, "i want to know the admission application process")
        self.assertEqual(r.tokens_no_stopwords, ["admission", "application", "process"])
        self.assertEqual(len(r.stems), 3)

    def test_validate_question(self):
        self.assertEqual(validate_question("  hello   world "), "hello world")
        for bad in ["", "   ", None, 42, "?!?!", "x" * 501]:
            with self.assertRaises(ValidationError):
                validate_question(bad)


if __name__ == "__main__":
    unittest.main()
