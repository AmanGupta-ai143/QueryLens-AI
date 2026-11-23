"""Text cleaning, stop-word removal and input validation."""
import re
import unicodedata
from dataclasses import dataclass, field

from config import MAX_QUESTION_LENGTH
from errors import ValidationError
from nlp.tokenizer import stem_tokens, tokenize

# Common function words. Negations ("not", "no") are deliberately kept.
STOPWORDS = frozenset("""
a an the is are was were be been being am do does did doing have has had having
i me my mine we our ours you your yours he she it its they them their this that
these those of in on at to for from by with about into over under as and or but
if so than then too very can could should would will shall may might must
what which who whom whose when where why how there here also just please
tell kindly want know need get gets got able
""".split())


@dataclass
class PreprocessResult:
    """Every intermediate step, kept so the NLP Insights page can show it."""
    original: str
    cleaned: str
    tokens: list[str] = field(default_factory=list)
    tokens_no_stopwords: list[str] = field(default_factory=list)
    stems: list[str] = field(default_factory=list)

    @property
    def processed(self) -> str:
        """Stemmed, stop-word-free text used by the word-level TF-IDF."""
        return " ".join(self.stems)

    @property
    def char_text(self) -> str:
        """Stop-word-free (unstemmed) text used by the character n-gram TF-IDF."""
        return " ".join(self.tokens_no_stopwords)


def validate_question(text) -> str:
    """Return a whitespace-normalised question or raise ``ValidationError``."""
    if not isinstance(text, str):
        raise ValidationError("Please enter a question.")
    question = re.sub(r"\s+", " ", text).strip()
    if not question:
        raise ValidationError("Please type a question before sending.")
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValidationError(
            f"Your question is too long ({len(question)} characters). "
            f"Please keep it under {MAX_QUESTION_LENGTH}."
        )
    if not re.search(r"[A-Za-z0-9]", question):
        raise ValidationError("Your message must contain letters or numbers.")
    return question


def clean_text(text) -> str:
    """Lowercase, strip URLs/punctuation/special characters, collapse spaces."""
    if text is None:
        return ""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = text.replace("&", " and ")
    text = re.sub(r"(\w)['\u2019]s\b", r"\1", text)   # university's -> university
    text = re.sub(r"['\u2019]", "", text)             # don't -> dont
    text = re.sub(r"[^a-z0-9\s]", " ", text)          # punctuation & specials
    return re.sub(r"\s+", " ", text).strip()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Drop common function words."""
    return [t for t in tokens if t not in STOPWORDS]


def preprocess(text) -> PreprocessResult:
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    no_stop = remove_stopwords(tokens)
    return PreprocessResult(
        original="" if text is None else str(text),
        cleaned=cleaned,
        tokens=tokens,
        tokens_no_stopwords=no_stop,
        stems=stem_tokens(no_stop),
    )
