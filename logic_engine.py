"""
logic_engine.py
---------------
Backend (Logic Layer) for the Logic Advocate Tutor.

This module implements the Bipolar Gradual evaluator described in
Chapter 3 of the thesis. It is the SYMBOLIC half of the system. It has
no knowledge of the LLM, the UI, or the network. You can import it,
build a graph, and ask it for scores.

Formal framework:
    F = <A, R_att, R_sup, w, v>
    A         = set of arguments
    R_att     = attack relation        (R_att subset of A x A)
    R_sup     = support relation       (R_sup subset of A x A)
    w(a)      = weight of argument a   (int in 1..25)
    v(a)      = value tag of argument  (Fact, Logic, Ethics, Emotion)

Acceptability score s(a) is the fixed point of the update rule:
    alpha(a)    = sum over (b,a) in R_att   of s(b) * w(b) * mu(v(b))/mu(v(a))
    sigma(a)    = sum over (b,a) in R_sup   of s(b) * w(b) * mu(v(b))/mu(v(a))
    s_(t+1)(a)  = min(1, (1 + sigma(a)/w(a)) / (1 + alpha(a)/w(a)))

Computed by 10 rounds of synchronous relaxation, then thresholded at
0.5 to recover an IN/OUT status label.
"""
from __future__ import annotations
from typing import Dict, List, Tuple


VALUE_WEIGHTS: Dict[str, float] = {
    "Fact":    1.2,
    "Logic":   1.1,
    "Ethics":  1.0,
    "Emotion": 0.8,
}

VALID_VALUE_TAGS = tuple(VALUE_WEIGHTS.keys())

RELAXATION_ITERATIONS = 10
IN_OUT_THRESHOLD      = 0.5


class AcademicLogicEngine:
    """A Bipolar Gradual argumentation evaluator."""

    def __init__(self) -> None:
        self.nodes:    Dict[str, Dict] = {}   # mid -> {text, weight, value_tag}
        self.attacks:  List[Tuple[str, str]] = []
        self.supports: List[Tuple[str, str]] = []
        self.statuses: Dict[str, str] = {}    # mid -> "IN" | "OUT"
        self.scores:   Dict[str, float] = {}  # mid -> float in [0, 1]
        self._last_convergence_iter: int = 0  # how many iters it took

    # ---------------------------------------------------------------- mutators

    def add_argument(self, mid: str, text: str, weight: int,
                     value_tag: str = "Logic") -> None:
        if value_tag not in VALUE_WEIGHTS:
            value_tag = "Logic"
        self.nodes[mid] = {
            "text":      text,
            "weight":    int(max(1, min(25, weight))),
            "value_tag": value_tag,
        }

    def add_direct_attack(self, attacker: str, target: str) -> None:
        self.attacks.append((attacker, target))

    def add_support(self, supporter: str, target: str) -> None:
        self.supports.append((supporter, target))

    # ----------------------------------------------------- score computation

    def evaluate_semantics(self) -> None:
        """Compute acceptability scores by ten rounds of synchronous relaxation."""
        if not self.nodes:
            self.scores = {}
            self.statuses = {}
            self._last_convergence_iter = 0
            return

        self.scores = {mid: 1.0 for mid in self.nodes}

        last_max_delta = float("inf")
        self._last_convergence_iter = RELAXATION_ITERATIONS
        for iteration in range(RELAXATION_ITERATIONS):
            new_scores: Dict[str, float] = {}
            for mid in self.nodes:
                t_val = self.nodes[mid].get("value_tag", "Logic")
                target_weight = max(1, self.nodes[mid]["weight"])

                attack_sum = 0.0
                for atk, tgt in self.attacks:
                    if tgt == mid and atk in self.nodes:
                        a_val = self.nodes[atk].get("value_tag", "Logic")
                        mult  = VALUE_WEIGHTS[a_val] / VALUE_WEIGHTS[t_val]
                        attack_sum += self.scores[atk] * self.nodes[atk]["weight"] * mult

                support_sum = 0.0
                for sup, tgt in self.supports:
                    if tgt == mid and sup in self.nodes:
                        s_val = self.nodes[sup].get("value_tag", "Logic")
                        mult  = VALUE_WEIGHTS[s_val] / VALUE_WEIGHTS[t_val]
                        support_sum += self.scores[sup] * self.nodes[sup]["weight"] * mult

                score = (1.0 + support_sum / target_weight) / (1.0 + attack_sum / target_weight)
                new_scores[mid] = min(1.0, score)

            max_delta = max(abs(new_scores[m] - self.scores[m]) for m in self.nodes)
            self.scores = new_scores

            if max_delta < 1e-6:
                self._last_convergence_iter = iteration + 1
                break
            last_max_delta = max_delta

        for mid in self.nodes:
            self.statuses[mid] = "IN" if self.scores[mid] >= IN_OUT_THRESHOLD else "OUT"

    # ---------------------------------------------------- inspector helpers

    def convergence_info(self) -> Dict[str, int | float]:
        """Diagnostic info about the last relaxation run."""
        return {
            "max_iterations":          RELAXATION_ITERATIONS,
            "iterations_until_stable": self._last_convergence_iter,
            "node_count":              len(self.nodes),
            "attack_count":            len(self.attacks),
            "support_count":           len(self.supports),
        }

    def attackers_of(self, mid: str) -> List[str]:
        return [a for (a, t) in self.attacks if t == mid]

    def supporters_of(self, mid: str) -> List[str]:
        return [s for (s, t) in self.supports if t == mid]

    def diagnose(self, mid: str) -> Dict[str, object]:
        """
        Produce a human-readable diagnostic of why an argument has the score
        it has. Used by the 'Why am I losing?' button in the UI.
        """
        if mid not in self.nodes:
            return {"error": f"Unknown argument {mid}"}

        node = self.nodes[mid]
        attackers = []
        for atk_id in self.attackers_of(mid):
            attackers.append({
                "id":         atk_id,
                "text":       self.nodes[atk_id]["text"],
                "value_tag":  self.nodes[atk_id].get("value_tag", "Logic"),
                "weight":     self.nodes[atk_id]["weight"],
                "score":      self.scores.get(atk_id, 0.0),
            })
        supporters = []
        for sup_id in self.supporters_of(mid):
            supporters.append({
                "id":         sup_id,
                "text":       self.nodes[sup_id]["text"],
                "value_tag":  self.nodes[sup_id].get("value_tag", "Logic"),
                "weight":     self.nodes[sup_id]["weight"],
                "score":      self.scores.get(sup_id, 0.0),
            })
        return {
            "id":         mid,
            "text":       node["text"],
            "value_tag":  node.get("value_tag", "Logic"),
            "weight":     node["weight"],
            "score":      self.scores.get(mid, 0.0),
            "status":     self.statuses.get(mid, "OUT"),
            "attackers":  attackers,
            "supporters": supporters,
        }

    # ------------------------------------------------------- export helpers

    def to_dict(self) -> Dict[str, object]:
        """Serialise the engine state for saving."""
        return {
            "nodes":    self.nodes,
            "attacks":  self.attacks,
            "supports": self.supports,
            "scores":   self.scores,
            "statuses": self.statuses,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AcademicLogicEngine":
        engine = cls()
        engine.nodes    = dict(data.get("nodes",    {}))
        engine.attacks  = [tuple(p) for p in data.get("attacks",  [])]
        engine.supports = [tuple(p) for p in data.get("supports", [])]
        engine.scores   = dict(data.get("scores",   {}))
        engine.statuses = dict(data.get("statuses", {}))
        return engine

    @classmethod
    def rebuild_from_messages(cls, messages: List[Dict]) -> "AcademicLogicEngine":
        """
        Construct an engine by replaying a list of move dicts. Used by the
        multiplayer view and by the save/load flow so we never have to
        persist the engine separately.
        """
        engine = cls()
        for m in messages:
            engine.add_argument(m["id"], m["content"], m.get("weight", 5),
                                m.get("value_tag", "Logic"))
        for m in messages:
            tgt = m.get("target")
            if tgt and tgt != "None":
                if m.get("action") == "Attack":
                    engine.add_direct_attack(m["id"], tgt)
                else:
                    engine.add_support(m["id"], tgt)
        engine.evaluate_semantics()
        return engine
