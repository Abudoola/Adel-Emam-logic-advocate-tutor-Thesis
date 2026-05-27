"""
tests/test_hint_mdp.py
----------------------
Unit tests for the MDP-based hint policy.
"""
try:
    import pytest
except ImportError:
    from tests import _pytest_shim as pytest
from hint_mdp import (
    STATES, ACTIONS,
    derive_state, choose_action,
    policy_table, value_table,
    _transition_distribution, _LANDING_PROBABILITY,
    HINT_COST, DISCOUNT,
)


class TestStateSpace:
    def test_state_space_has_18_states(self):
        assert len(STATES) == 18

    def test_actions_has_four(self):
        assert len(ACTIONS) == 4

    def test_actions_are_distinct(self):
        assert len(set(ACTIONS)) == len(ACTIONS)


class TestPolicy:
    def test_policy_covers_every_state(self):
        pol = policy_table()
        for s in STATES:
            assert s in pol
            assert pol[s] in ACTIONS

    def test_losing_states_prefer_step_back(self):
        pol = policy_table()
        for state, action in pol.items():
            own_status, _, _ = state
            if own_status == "LOSING":
                assert action == "STEP_BACK", (
                    f"Losing state {state} should pick STEP_BACK, got {action}"
                )

    def test_high_pressure_winning_prefers_value_reframe(self):
        # When the user is doing well but the opponent's last argument
        # is strong, the MDP should bias toward value reframing.
        pol = policy_table()
        for state, action in pol.items():
            own_status, pressure, _ = state
            if own_status in ("WINNING", "TIED") and pressure == "HIGH":
                assert action == "VALUE_REFRAME", (
                    f"State {state} should pick VALUE_REFRAME, got {action}"
                )


class TestTransitions:
    def test_distributions_sum_to_one(self):
        for state in STATES:
            for action in ACTIONS:
                d = _transition_distribution(state, action)
                total = sum(d.values())
                assert total == pytest.approx(1.0, abs=1e-6), (
                    f"({state}, {action}) sums to {total}, not 1"
                )

    def test_all_next_states_are_valid(self):
        for state in STATES:
            for action in ACTIONS:
                d = _transition_distribution(state, action)
                for next_state in d.keys():
                    assert next_state in STATES


class TestDeriveState:
    def test_empty_engine_returns_tied_low_zero(self):
        from logic_engine import AcademicLogicEngine
        e = AcademicLogicEngine()
        s = derive_state(e, messages=[], learner_side="Side A", recent_hints=0)
        assert s == ("TIED", "LOW", "ZERO")

    def test_hint_streak_bucketing(self):
        from logic_engine import AcademicLogicEngine
        e = AcademicLogicEngine()
        msgs = [{"id": "Msg_1", "content": "x", "side": "Side A",
                 "weight": 10, "value_tag": "Logic", "target": None,
                 "action": "Attack"}]
        e.add_argument("Msg_1", "x", 10, "Logic")
        e.evaluate_semantics()

        assert derive_state(e, msgs, "Side A", 0)[2] == "ZERO"
        assert derive_state(e, msgs, "Side A", 1)[2] == "ONE"
        assert derive_state(e, msgs, "Side A", 2)[2] == "TWO_PLUS"
        assert derive_state(e, msgs, "Side A", 5)[2] == "TWO_PLUS"


class TestPolicyConstants:
    def test_hint_cost_is_negative(self):
        assert HINT_COST < 0, "Hint cost should mildly discourage spamming"

    def test_discount_in_range(self):
        assert 0.0 < DISCOUNT < 1.0

    def test_landing_probability_table_covers_all_actions(self):
        for action in ACTIONS:
            assert action in _LANDING_PROBABILITY
            assert set(_LANDING_PROBABILITY[action]) == {"WINNING", "TIED", "LOSING"}
