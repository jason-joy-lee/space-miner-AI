"""Synthetic mission data and a real, explainable KNN classifier.

The beginner mission intentionally uses two *learnable* sensor clusters instead
of the old sparse, misleading two-ore-island generator. Labels are never leaked
from mining candidates to KNN or held-out validation.
"""
from dataclasses import dataclass
from random import Random
from math import dist


@dataclass(frozen=True)
class Planet:
    id: str
    thermal: float
    spectral: float
    ore: bool


def galaxy(seed=42):
    """Build a repeatable mission with distinct ore/empty feature clusters.

    A few labels may be noisy. Random outcomes are never changed to make the
    player's picks win; all labels are generated once at mission creation.
    The 0–10 values are imaginary sensor readings, NOT planet coordinates.
    """
    rng = Random(seed)
    centers = {True: (3.0, 7.0), False: (7.0, 3.0)}

    def make(prefix, target_labels):
        out = []
        for i, target_ore in enumerate(target_labels, 1):
            center_x, center_y = centers[target_ore]
            x = round(min(10.0, max(0.0, rng.gauss(center_x, 1.15))), 2)
            y = round(min(10.0, max(0.0, rng.gauss(center_y, 1.15))), 2)
            actual_ore = target_ore if rng.random() >= 0.06 else not target_ore
            out.append(Planet(f"{prefix}-{i:02}", x, y, actual_ore))
        rng.shuffle(out)
        return out

    return {
        "starter": make("TR", [True, False] * 4),
        "reserve": make("SC", [True, False] * 3),
        "validation": make("VA", [True, False] * 10),
        "mining": make("PX", [True, False] * 6),
    }


SENSOR_WEIGHTS = {"balanced": (1.0, 1.0), "heat": (2.0, 0.5), "spectrum": (0.5, 2.0)}


def feature_distance(a, b, focus="balanced"):
    """Weighted Euclidean distance in synthetic sensor space."""
    if focus not in SENSOR_WEIGHTS:
        raise ValueError("Unknown sensor focus")
    heat_weight, spectrum_weight = SENSOR_WEIGHTS[focus]
    return dist((heat_weight * a.thermal, spectrum_weight * a.spectral),
                (heat_weight * b.thermal, spectrum_weight * b.spectral))


def knn(training, candidate, k, focus="balanced"):
    """Return predicted label, K nearest training examples and ore votes.

    Only sensor features from the candidate are read. Its true ore label is
    deliberately not accessed during prediction.
    """
    if not training or k < 1 or k > len(training) or k % 2 == 0:
        raise ValueError("K must be odd and fit training data")
    closest = sorted(
        training,
        key=lambda p: (feature_distance(p, candidate, focus), p.id)
    )[:k]
    votes = sum(p.ore for p in closest)
    return votes > k // 2, closest, votes


def accuracy(training, validation, k, focus="balanced"):
    if not validation:
        raise ValueError("Validation must not be empty")
    return sum(knn(training, p, k, focus)[0] == p.ore for p in validation) / len(validation)


def classification_metrics(training, validation, k, focus="balanced"):
    """Held-out evaluation of ore as the positive class.

    Precision = true ore among all predicted ore. When the model never
    predicts ore, precision is 0 by explicit convention (undefined otherwise).
    """
    if not validation:
        raise ValueError("Validation must not be empty")
    predicted=[knn(training,p,k,focus)[0] for p in validation]
    true_positive=sum(pred and p.ore for pred,p in zip(predicted,validation))
    false_positive=sum(pred and not p.ore for pred,p in zip(predicted,validation))
    true_negative=sum(not pred and not p.ore for pred,p in zip(predicted,validation))
    false_negative=sum(not pred and p.ore for pred,p in zip(predicted,validation))
    total=len(validation)
    positive=true_positive+false_positive
    return {
        "accuracy":(true_positive+true_negative)/total,
        "precision":true_positive/positive if positive else 0.0,
        "true_positive":true_positive,
        "false_positive":false_positive,
        "true_negative":true_negative,
        "false_negative":false_negative,
        "predicted_ore":positive,
        "total":total,
    }


def baseline(training, validation):
    if not training or not validation:
        raise ValueError("Training and validation data cannot be empty")
    majority = sum(p.ore for p in training) > len(training) / 2
    return sum(p.ore == majority for p in validation) / len(validation)


def mine(credits, mined, planet):
    if planet.id in mined:
        raise ValueError("Already mined")
    if len(mined) >= 5:
        raise ValueError("Five-mine limit")
    if credits < 10:
        raise ValueError("Insufficient credits")
    return credits - 10 + (25 if planet.ore else 0), mined | {planet.id}
