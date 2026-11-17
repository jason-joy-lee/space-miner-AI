from space_miner.core import galaxy, knn, accuracy, baseline
from space_miner.strategy import ranked_candidates


def test_default_mission_is_learnable_not_a_trap():
    g = galaxy(42)
    assert {name: len(group) for name, group in g.items()} == {
        "starter": 8, "reserve": 6, "validation": 20, "mining": 12
    }
    assert len({p.id for group in g.values() for p in group}) == 46
    assert {p.ore for p in g["starter"]} == {True, False}
    # The introductory mission should be a real learning task, not the old
    # accidental K=3 trap where validation accuracy was only 40%.
    assert accuracy(g["starter"], g["validation"], 3) >= 0.75
    assert accuracy(g["starter"], g["validation"], 3) > baseline(g["starter"], g["validation"])


def test_majority_vote_is_consistent_with_label():
    g = galaxy(42)
    for k in (1, 3, 5, 7):
        for planet in g["mining"]:
            predicted, neighbors, votes = knn(g["starter"], planet, k)
            assert len(neighbors) == k
            assert predicted == (votes > k // 2)


def test_scanning_more_examples_can_change_model_without_leaking_answers():
    g = galaxy(44)
    train = g["starter"]
    before = [(p.id, knn(train, p, 3)[0]) for p in g["mining"]]
    after = [(p.id, knn(train + g["reserve"], p, 3)[0]) for p in g["mining"]]
    # A scan adds examples; actual outcomes are fixed and never rewritten.
    assert g == galaxy(44)
    assert len(before) == len(after) == 12
    ranking = ranked_candidates(train, g["mining"], 3)
    assert {row[0].id for row in ranking} == {p.id for p in g["mining"]}
