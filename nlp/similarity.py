"""Cosine similarity and score combination."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def cosine_scores(query_vector, matrix) -> np.ndarray:
    """Cosine similarity of one query vector against every FAQ vector."""
    return cosine_similarity(query_vector, matrix).ravel()


CHAR_FLOOR = 0.85


def combine_scores(word_scores, char_scores, word_weight: float, char_weight: float,
                   char_floor: float = CHAR_FLOOR) -> np.ndarray:
    """Combine the word-level and character-level cosine scores.

    final = max( weighted average of both scores , char_floor * char score )

    The weighted average rewards matching words. The "floor" lets a question
    with spelling mistakes ("adimssion aplication") still match through shared
    character n-grams even when no whole word matches.
    """
    total = word_weight + char_weight
    if total <= 0:
        raise ValueError("Weights must sum to a positive number.")
    word_scores = np.asarray(word_scores)
    char_scores = np.asarray(char_scores)
    blended = (word_weight * word_scores + char_weight * char_scores) / total
    return np.maximum(blended, char_floor * char_scores)


def top_k_indices(scores, k: int) -> list[int]:
    """Indices of the k highest scores (highest first, stable for ties)."""
    scores = np.asarray(scores)
    order = np.argsort(-scores, kind="stable")
    return [int(i) for i in order[:k]]
