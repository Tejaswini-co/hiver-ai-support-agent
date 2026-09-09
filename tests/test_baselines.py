from baselines.majority_baseline import majority_label


def test_majority_baseline_returns_most_common_label() -> None:
    assert majority_label(["a", "b", "a"]) == "a"