"""Tokenization and stemming.

* Tokenization uses NLTK's ``RegexpTokenizer`` (no corpus download needed).
  If NLTK is not installed, an equivalent regex keeps the app working.
* Stemming uses a small rule-based suffix stripper so results are identical on
  every machine (and covered by unit tests).
"""
import re

try:  # pragma: no cover - depends on the environment
    from nltk.tokenize import RegexpTokenizer

    _TOKENIZER = RegexpTokenizer(r"[a-z0-9]+")
    NLTK_AVAILABLE = True
except Exception:  # pragma: no cover
    _TOKENIZER = None
    NLTK_AVAILABLE = False


def tokenize(text: str) -> list[str]:
    """Split *cleaned* text into alphanumeric tokens."""
    if not text:
        return []
    if _TOKENIZER is not None:
        return _TOKENIZER.tokenize(text)
    return re.findall(r"[a-z0-9]+", text)


def rule_stem(word: str) -> str:
    """applying/applied/apply -> appli, fees -> fee, exams -> exam."""
    if len(word) <= 3 or word.isdigit():
        return word
    for suffix, repl in (("sses", "ss"), ("ies", "i"), ("ing", ""),
                         ("ed", ""), ("es", ""), ("s", "")):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            if suffix == "s" and word.endswith("ss"):
                continue
            word = word[: -len(suffix)] + repl
            break
    if word.endswith("y") and len(word) > 3:
        word = word[:-1] + "i"
    return word


def stem(word: str) -> str:
    return rule_stem(word)


def stem_tokens(tokens: list[str]) -> list[str]:
    return [stem(t) for t in tokens]
