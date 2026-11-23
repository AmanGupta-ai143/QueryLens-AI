"""FAQ retrieval engine: question -> preprocessing -> TF-IDF -> cosine -> answer.

The engine is pure Python (no Streamlit, no database), so it can be unit-tested
and reused. Retrieval does not need any paid API. A future LLM or sentence-
embedding retriever only has to implement the same ``answer()`` contract.
"""
from dataclasses import asdict, dataclass, field

from config import CHAR_WEIGHT, DEFAULT_THRESHOLD, TOP_K, WORD_WEIGHT
from errors import ValidationError
from nlp.preprocessing import PreprocessResult, clean_text, preprocess, validate_question
from nlp.similarity import combine_scores, cosine_scores, top_k_indices
from nlp.vectorizer import FAQVectorizer

METHOD_NAME = "TF-IDF (word + character n-grams) + Cosine Similarity"

FALLBACK_MESSAGE = (
    "Sorry, I couldn't find a reliable answer to that in my FAQ knowledge base. "
    "Please try rephrasing your question. I've also saved it, so the administrator "
    "can review it and add an answer."
)
EMPTY_KB_MESSAGE = (
    "The FAQ knowledge base is empty, so I can't answer yet. "
    "Please ask the administrator to add some FAQs."
)


def validate_threshold(value) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError("The similarity threshold must be a number between 0 and 1.")
    if not 0.0 <= value <= 1.0:
        raise ValidationError("The similarity threshold must be between 0 and 1.")
    return value


@dataclass
class Candidate:
    faq_id: int
    question: str
    category: str
    score: float
    word_score: float
    char_score: float


@dataclass
class ChatResult:
    question: str
    cleaned: str
    tokens: list
    tokens_no_stopwords: list
    stems: list
    answered: bool
    status: str                      # answered | low_confidence | no_terms | empty_kb
    response: str
    threshold: float
    best: Candidate | None = None
    matched_faq: dict | None = None
    predicted_category: str | None = None
    candidates: list = field(default_factory=list)
    category_scores: dict = field(default_factory=dict)
    term_weights: list = field(default_factory=list)
    exact_match: bool = False
    method: str = METHOD_NAME

    @property
    def score(self) -> float:
        return self.best.score if self.best else 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class ChatbotEngine:
    def __init__(self, faqs: list[dict] | None = None, threshold: float = DEFAULT_THRESHOLD,
                 word_weight: float = WORD_WEIGHT, char_weight: float = CHAR_WEIGHT):
        self.threshold = validate_threshold(threshold)
        self.word_weight = word_weight
        self.char_weight = char_weight
        self.faqs: list[dict] = []
        self.vectorizer: FAQVectorizer | None = None
        self._clean_questions: list[str] = []
        self.load(faqs or [])

    # ------------------------------------------------------------------ build
    def load(self, faqs: list[dict]) -> None:
        """(Re)build the TF-IDF index from a list of FAQ dicts."""
        self.faqs = list(faqs)
        self._clean_questions = [clean_text(f["question"]) for f in self.faqs]
        if not self.faqs:
            self.vectorizer = None
            return
        # Each FAQ document = its question + its keywords.
        docs = [preprocess(f"{f['question']} {f.get('keywords') or ''}") for f in self.faqs]
        self.vectorizer = FAQVectorizer().fit(docs)

    @property
    def is_ready(self) -> bool:
        return self.vectorizer is not None and bool(self.faqs)

    # ----------------------------------------------------------------- answer
    def answer(self, question: str, threshold: float | None = None, top_k: int = TOP_K) -> ChatResult:
        question = validate_question(question)
        threshold = self.threshold if threshold is None else validate_threshold(threshold)
        pre = preprocess(question)
        base = dict(question=question, cleaned=pre.cleaned, tokens=pre.tokens,
                    tokens_no_stopwords=pre.tokens_no_stopwords, stems=pre.stems,
                    threshold=threshold)

        if not self.is_ready:
            return ChatResult(answered=False, status="empty_kb", response=EMPTY_KB_MESSAGE, **base)
        if not pre.stems:
            return ChatResult(answered=False, status="no_terms", response=FALLBACK_MESSAGE, **base)

        word_q, char_q = self.vectorizer.transform(pre)
        word_scores = cosine_scores(word_q, self.vectorizer.word_matrix)
        char_scores = cosine_scores(char_q, self.vectorizer.char_matrix)
        scores = combine_scores(word_scores, char_scores, self.word_weight, self.char_weight)

        candidates = [
            Candidate(
                faq_id=self.faqs[i]["id"], question=self.faqs[i]["question"],
                category=self.faqs[i]["category"], score=round(float(scores[i]), 4),
                word_score=round(float(word_scores[i]), 4), char_score=round(float(char_scores[i]), 4),
            )
            for i in top_k_indices(scores, max(1, top_k))
        ]
        best = candidates[0]

        # Intent matching: best score per category among the candidates.
        category_scores: dict[str, float] = {}
        for c in candidates:
            if c.score > 0:
                category_scores[c.category] = max(category_scores.get(c.category, 0.0), c.score)

        answered = best.score >= threshold
        predicted = best.category if best.score >= threshold * 0.5 and best.score > 0 else None
        matched = next((f for f in self.faqs if f["id"] == best.faq_id), None) if answered else None

        return ChatResult(
            answered=answered,
            status="answered" if answered else "low_confidence",
            response=matched["answer"] if answered else FALLBACK_MESSAGE,
            best=best, matched_faq=matched, predicted_category=predicted,
            candidates=candidates, category_scores=category_scores,
            term_weights=self.vectorizer.query_term_weights(pre),
            exact_match=pre.cleaned in self._clean_questions,
            **base,
        )
