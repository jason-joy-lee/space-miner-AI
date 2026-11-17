"""Presentation helpers without hidden-label leakage."""
from .core import knn, feature_distance


def ranked_candidates(training, candidates, k, focus="balanced"):
    """Rank by KNN ore vote; ties use average neighbor distance and planet ID.

    Vote fractions are NOT calibrated ore probabilities.
    """
    ranked = []
    for planet in candidates:
        predicted, neighbors, ore_votes = knn(training, planet, k, focus)
        avg_distance = sum(feature_distance(p, planet, focus)
                           for p in neighbors) / k
        ranked.append((planet, predicted, ore_votes, avg_distance))
    return sorted(ranked, key=lambda x: (not x[1], -x[2], x[3], x[0].id))


def explanation(predicted, votes, k):
    """Human-readable explanation of real nearest-neighbor voting."""
    label = "ORE" if predicted else "EMPTY"
    return (f"Among the {k} most similar surveyed planets, "
            f"{votes} contained ore and {k-votes} were empty. "
            f"The majority voted {label}. This is a classification, "
            "not a guaranteed or calibrated probability.")
