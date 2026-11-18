import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "benchmark", Path(__file__).parents[3] / "packages/evaluation/benchmark.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def result(reference="correct", seconds=4, classification="matching_segment"):
    return {
        "classification": classification,
        "candidates": [{"reference_id": reference, "start_seconds": seconds}],
    }


def test_wrong_source_is_not_correct_even_at_expected_timestamp():
    score = module.score_result(result(reference="wrong"), "correct")
    assert not score["top_1_source_correct"]
    assert not score["correct_decision"]
    assert score["timestamp_error_seconds"] is None


def test_source_hit_and_timestamp_localization_are_distinct():
    score = module.score_result(result(seconds=10), "correct")
    assert score["top_1_source_correct"]
    assert not score["localized_correctly"]
    assert not score["correct_decision"]
    assert score["timestamp_error_seconds"] == 6


def test_possible_match_is_not_a_confirmed_match():
    score = module.score_result(result(classification="possible_match"), "correct")
    assert score["localized_correctly"]
    assert not score["confirmed_correctly"]


def test_unknown_must_have_no_match_classification_and_no_candidates():
    assert module.score_result({"classification": "no_match", "candidates": []}, None)[
        "correct_decision"
    ]
    assert not module.score_result(result(), None)["correct_decision"]
    assert not module.score_result({"classification": "no_match", "candidates": [{}]}, None)[
        "correct_decision"
    ]
    assert not module.score_result({"classification": "matching_segment", "candidates": []}, None)[
        "correct_decision"
    ]


def test_timestamp_boundary_missing_and_nonfinite_values():
    assert module.score_result(result(seconds=4.5), "correct")["correct_decision"]
    assert not module.score_result(result(seconds=4.501), "correct")["correct_decision"]
    for seconds in (None, float("nan"), float("inf"), True, "4"):
        assert not module.score_result(result(seconds=seconds), "correct")["localized_correctly"]
    assert not module.score_result({"classification": "no_match", "candidates": []}, "correct")[
        "top_1_source_correct"
    ]
