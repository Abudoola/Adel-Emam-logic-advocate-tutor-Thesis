"""
tests/test_scenarios.py
-----------------------
Regression test: every scenario in tools/scenarios.py must reach a
final root score in [0, 1] and a status in {IN, OUT}. The dataset
itself is the contract; if anyone edits a scenario in a way that
breaks the engine's invariants, this catches it.
"""
try:
    import pytest
except ImportError:
    from tests import _pytest_shim as pytest
from logic_engine import AcademicLogicEngine
from tools.scenarios import ALL_SCENARIOS


@pytest.mark.parametrize("scenario", ALL_SCENARIOS,
                           ids=lambda s: s["id"])
def test_scenario_produces_valid_verdict(scenario):
    e = AcademicLogicEngine()
    for (mid, text, w, tag) in scenario["arguments"]:
        e.add_argument(mid, text, w, tag)
    for (atk, tgt) in scenario["attacks"]:
        e.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        e.add_support(sup, tgt)
    e.evaluate_semantics()

    root = scenario["arguments"][0][0]
    assert root in e.scores
    assert 0.0 <= e.scores[root] <= 1.0
    assert e.statuses[root] in {"IN", "OUT"}


def test_overall_agreement_does_not_regress():
    """We hold a hard floor on the agreement rate so a change to the
    engine that breaks our human-expert verdicts is caught immediately."""
    agree = 0
    for scenario in ALL_SCENARIOS:
        e = AcademicLogicEngine()
        for (mid, text, w, tag) in scenario["arguments"]:
            e.add_argument(mid, text, w, tag)
        for (atk, tgt) in scenario["attacks"]:
            e.add_direct_attack(atk, tgt)
        for (sup, tgt) in scenario["supports"]:
            e.add_support(sup, tgt)
        e.evaluate_semantics()
        root = scenario["arguments"][0][0]
        if e.statuses[root] == scenario["expected"]:
            agree += 1

    pct = agree / len(ALL_SCENARIOS)
    # Current baseline is 85%; we floor at 80% so small tuning is OK
    # but a regression triggers a failure.
    assert pct >= 0.80, f"Agreement dropped to {pct:.1%}, regression"
