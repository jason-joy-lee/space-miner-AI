"""V0.6 challenge generator: a deliberately *undertrained* real KNN mission.

The starter survey severely over-samples ore-rich regions (7 ORE-like,
1 EMPTY-like). The six optional reserve surveys represent under-sampled empty
regions (1 ORE-like, 5 EMPTY-like). The validation set includes more empty
planets to expose the model's false-positive ore predictions. Players improve predictions by labeling/independently scanning
those reports. No hidden mining labels are manipulated after a decision.
"""
from random import Random
from .core import Planet


def novice_galaxy(seed: int = 12) -> dict[str, list[Planet]]:
    rng = Random(seed)
    centers = {True: (3.0, 7.0), False: (7.0, 3.0)}

    def survey(prefix: str, intended_labels: list[bool]) -> list[Planet]:
        out = []
        for index, expected_ore in enumerate(intended_labels, start=1):
            heat, spectrum = centers[expected_ore]
            heat = round(max(0.0, min(10.0, rng.gauss(heat, 1.5))), 2)
            spectrum = round(max(0.0, min(10.0, rng.gauss(spectrum, 1.5))), 2)
            # Modest label noise: sensor features are informative, not perfect.
            actual_ore = expected_ore if rng.random() >= 0.06 else not expected_ore
            out.append(Planet(f"{prefix}-{index:02}", heat, spectrum, actual_ore))
        rng.shuffle(out)
        return out

    return {
        "starter": survey("TR", [True] * 7 + [False]),
        "reserve": survey("SC", [True] + [False] * 5),
        "validation": survey("VA", [True, False] * 6 + [False] * 8),
        "mining": survey("PX", [True, False] * 4 + [False] * 4),
    }
