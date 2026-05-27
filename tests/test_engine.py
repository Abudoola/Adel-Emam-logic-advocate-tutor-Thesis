"""
tests/test_engine.py
--------------------
Unit tests for the Bipolar Gradual logic engine.
"""
try:
    import pytest
except ImportError:
    from tests import _pytest_shim as pytest

from logic_engine import (
    AcademicLogicEngine,
    VALUE_WEIGHTS,
    VALID_VALUE_TAGS,
    IN_OUT_THRESHOLD,
    RELAXATION_ITERATIONS,
)


class TestBounds:
    """All scores must stay inside [0, 1] regardless of input shape."""

    def test_empty_engine_has_no_scores(self):
        e = AcademicLogicEngine()
        e.evaluate_semantics()
        assert e.scores == {}
        assert e.statuses == {}

    def test_single_node_scores_one(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "claim", 10, "Logic")
        e.evaluate_semantics()
        assert e.scores["a1"] == 1.0
        assert e.statuses["a1"] == "IN"

    def test_scores_always_in_unit_interval(self):
        e = AcademicLogicEngine()
        for i in range(15):
            e.add_argument(f"a{i}", f"text {i}", (i % 25) + 1, "Logic")
        for i in range(14):
            e.add_direct_attack(f"a{i+1}", f"a{i}")
        for i in range(5):
            e.add_support(f"a{i+10}", "a0")
        e.evaluate_semantics()
        for mid, s in e.scores.items():
            assert 0.0 <= s <= 1.0, f"{mid} score {s} out of bounds"


class TestClassicalAgreement:
    """On attack-only inputs with heavy attackers, the engine should
    agree with Dung's grounded extension after thresholding at 0.5."""

    def test_unattacked_root_is_IN(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 1, "Ethics")
        e.evaluate_semantics()
        assert e.statuses["a1"] == "IN"

    def test_single_attack_defeats_root(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 1, "Ethics")
        e.add_argument("a2", "atk",  5, "Ethics")
        e.add_direct_attack("a2", "a1")
        e.evaluate_semantics()
        assert e.statuses["a1"] == "OUT"
        assert e.statuses["a2"] == "IN"

    def test_three_node_chain_root_survives(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 1, "Ethics")
        e.add_argument("a2", "atk",  5, "Ethics")
        e.add_argument("a3", "def", 25, "Ethics")
        e.add_direct_attack("a2", "a1")
        e.add_direct_attack("a3", "a2")
        e.evaluate_semantics()
        assert e.statuses["a1"] == "IN"
        assert e.statuses["a2"] == "OUT"
        assert e.statuses["a3"] == "IN"


class TestValueTagAsymmetry:
    """A Fact attack on an Emotion claim should hit harder than an
    Emotion attack on a Fact claim."""

    def _root_score_after_attack(self, root_tag, attacker_tag):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 10, root_tag)
        e.add_argument("a2", "atk",  10, attacker_tag)
        e.add_direct_attack("a2", "a1")
        e.evaluate_semantics()
        return e.scores["a1"]

    def test_fact_attack_on_emotion_harder_than_reverse(self):
        emotion_root_under_fact = self._root_score_after_attack("Emotion", "Fact")
        fact_root_under_emotion = self._root_score_after_attack("Fact", "Emotion")
        assert emotion_root_under_fact < fact_root_under_emotion

    def test_same_tag_attack_yields_symmetric_drop(self):
        a = self._root_score_after_attack("Logic", "Logic")
        b = self._root_score_after_attack("Ethics", "Ethics")
        assert a == pytest.approx(b, abs=1e-6)


class TestBipolar:
    """Support should reinforce the target's score."""

    def test_support_increases_score(self):
        e1 = AcademicLogicEngine()
        e1.add_argument("a1", "root", 10, "Logic")
        e1.add_argument("a2", "atk",  10, "Logic")
        e1.add_direct_attack("a2", "a1")
        e1.evaluate_semantics()
        no_sup = e1.scores["a1"]

        e2 = AcademicLogicEngine()
        e2.add_argument("a1", "root", 10, "Logic")
        e2.add_argument("a2", "atk",  10, "Logic")
        e2.add_argument("a3", "sup",  10, "Logic")
        e2.add_direct_attack("a2", "a1")
        e2.add_support("a3", "a1")
        e2.evaluate_semantics()
        with_sup = e2.scores["a1"]

        assert with_sup > no_sup

    def test_support_alone_keeps_root_in(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 10, "Logic")
        e.add_argument("a2", "sup",  10, "Logic")
        e.add_support("a2", "a1")
        e.evaluate_semantics()
        assert e.statuses["a1"] == "IN"


class TestConvergence:
    """The relaxation loop should stop within RELAXATION_ITERATIONS."""

    def test_convergence_info_is_populated(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 10, "Logic")
        e.evaluate_semantics()
        info = e.convergence_info()
        assert info["node_count"] == 1
        assert info["iterations_until_stable"] <= RELAXATION_ITERATIONS

    def test_simple_input_converges_in_one_iteration(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 10, "Logic")
        e.evaluate_semantics()
        assert e.convergence_info()["iterations_until_stable"] == 1

    def test_long_chain_still_terminates(self):
        e = AcademicLogicEngine()
        for i in range(20):
            e.add_argument(f"a{i}", f"x{i}", 10, "Logic")
        for i in range(19):
            e.add_direct_attack(f"a{i+1}", f"a{i}")
        e.evaluate_semantics()
        assert e.convergence_info()["iterations_until_stable"] <= RELAXATION_ITERATIONS


class TestDiagnose:
    def test_diagnose_includes_attackers_and_supporters(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "root", 10, "Logic")
        e.add_argument("a2", "atk",  10, "Logic")
        e.add_argument("a3", "sup",  10, "Logic")
        e.add_direct_attack("a2", "a1")
        e.add_support("a3", "a1")
        e.evaluate_semantics()
        d = e.diagnose("a1")
        assert d["id"] == "a1"
        assert len(d["attackers"]) == 1
        assert len(d["supporters"]) == 1

    def test_diagnose_unknown_id_returns_error(self):
        e = AcademicLogicEngine()
        d = e.diagnose("nonexistent")
        assert "error" in d


class TestSerialisation:
    def test_to_dict_round_trip_preserves_scores(self):
        e1 = AcademicLogicEngine()
        e1.add_argument("a1", "root", 10, "Logic")
        e1.add_argument("a2", "atk",  10, "Logic")
        e1.add_direct_attack("a2", "a1")
        e1.evaluate_semantics()
        data = e1.to_dict()
        e2 = AcademicLogicEngine.from_dict(data)
        assert e2.nodes == e1.nodes
        assert e2.scores == e1.scores

    def test_rebuild_from_messages_produces_same_scores(self):
        e1 = AcademicLogicEngine()
        e1.add_argument("a1", "root", 10, "Fact")
        e1.add_argument("a2", "atk",  10, "Logic")
        e1.add_direct_attack("a2", "a1")
        e1.evaluate_semantics()
        msgs = [
            {"id": "a1", "content": "root", "weight": 10, "value_tag": "Fact",
             "side": "A", "target": None, "action": "Attack"},
            {"id": "a2", "content": "atk",  "weight": 10, "value_tag": "Logic",
             "side": "B", "target": "a1", "action": "Attack"},
        ]
        e2 = AcademicLogicEngine.rebuild_from_messages(msgs)
        assert e2.scores == e1.scores


class TestValidation:
    def test_invalid_value_tag_falls_back_to_logic(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "x", 10, "Bogus")
        assert e.nodes["a1"]["value_tag"] == "Logic"

    def test_weight_clamped_into_range(self):
        e = AcademicLogicEngine()
        e.add_argument("a1", "x", -5, "Logic")
        e.add_argument("a2", "y", 9999, "Logic")
        assert e.nodes["a1"]["weight"] == 1
        assert e.nodes["a2"]["weight"] == 25
