"""TF-IDF vectorization.

Two TF-IDF representations are built over the FAQ corpus:

* word level  - stemmed, stop-word-free word uni/bi-grams (handles different
  word forms: "applying" / "application" / "applied");
* character level - 3-5 character n-grams inside words (tolerates spelling
  mistakes: "admision" still shares most n-grams with "admission").

They are combined later in ``similarity.py``. Both are *lexical* methods.
"""
from sklearn.feature_extraction.text import TfidfVectorizer

from nlp.preprocessing import PreprocessResult


def _split(text: str) -> list[str]:
    return text.split()


class FAQVectorizer:
    def __init__(self):
        self.word_vectorizer = TfidfVectorizer(
            tokenizer=_split, token_pattern=None, lowercase=False,
            ngram_range=(1, 2), sublinear_tf=True,
        )
        self.char_vectorizer = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True,
        )
        self.word_matrix = None
        self.char_matrix = None

    def fit(self, documents: list[PreprocessResult]) -> "FAQVectorizer":
        """Learn the vocabulary/IDF from the FAQ documents."""
        self.word_matrix = self.word_vectorizer.fit_transform(d.processed for d in documents)
        self.char_matrix = self.char_vectorizer.fit_transform(d.char_text for d in documents)
        return self

    def transform(self, query: PreprocessResult):
        """Return (word_vector, char_vector) for one preprocessed query."""
        return (
            self.word_vectorizer.transform([query.processed]),
            self.char_vectorizer.transform([query.char_text]),
        )

    def query_term_weights(self, query: PreprocessResult, limit: int = 15) -> list[tuple[str, float]]:
        """Non-zero word-level TF-IDF weights of the query (for explainability)."""
        vec = self.word_vectorizer.transform([query.processed])
        names = self.word_vectorizer.get_feature_names_out()
        row = vec.tocoo()
        pairs = sorted(((names[c], float(v)) for c, v in zip(row.col, row.data)),
                       key=lambda p: p[1], reverse=True)
        return pairs[:limit]

    @property
    def vocabulary_size(self) -> int:
        return len(self.word_vectorizer.vocabulary_)
