"""
ROLE: BACKEND (Logic Layer)
DESCRIPTION: Contains the math and evaluation semantics for the argumentation framework.
"""
PYARG_INSTALLED = False
try:
    from py_arg.abstract_argumentation_classes.abstract_argumentation_framework import AbstractArgumentationFramework
    from py_arg.abstract_argumentation_classes.argument import Argument
    from py_arg.abstract_argumentation_classes.defeat import Defeat
    from py_arg.algorithms.semantics.get_grounded_extension import get_grounded_extension
    PYARG_INSTALLED = True
except ImportError:
    pass

class AcademicLogicEngine:
    def __init__(self):
        self.nodes = {}
        self.attacks = []
        self.supports = []
        self.statuses = {}
        self._dirty = True

    def add_argument(self, mid, text, weight):
        self.nodes[mid] = {"text": text, "weight": weight}
        self._dirty = True

    def update_weight(self, mid, weight):
        if mid in self.nodes:
            self.nodes[mid]["weight"] = weight
            self._dirty = True

    def add_direct_attack(self, attacker, target):
        self.attacks.append((attacker, target))
        self._dirty = True

    def add_support(self, supporter, target):
        self.supports.append((supporter, target))
        self._dirty = True

    def evaluate_semantics(self):
        if not self._dirty:
            return

        # Compute effective weights including support boosts without mutating node data
        effective_weights = {mid: data["weight"] for mid, data in self.nodes.items()}
        for supporter, target in self.supports:
            if supporter in self.nodes and target in self.nodes:
                effective_weights[target] += 4

        valid_defeats = []
        for atk, tgt in self.attacks:
            if atk in self.nodes and tgt in self.nodes:
                if effective_weights[atk] >= effective_weights[tgt]:
                    valid_defeats.append((atk, tgt))

        winning_ids = set()
        if PYARG_INSTALLED:
            try:
                af = AbstractArgumentationFramework('battle_arena')
                arg_objs = {}
                for mid in self.nodes:
                    arg_objs[mid] = Argument(mid)
                    af.add_argument(arg_objs[mid])
                for atk, tgt in valid_defeats:
                    af.add_defeat(Defeat(arg_objs[atk], arg_objs[tgt]))
                grounded = get_grounded_extension(af)
                winning_ids = {arg.name for arg in grounded}
            except Exception:
                winning_ids = self._fallback_eval(valid_defeats)
        else:
            winning_ids = self._fallback_eval(valid_defeats)

        for mid in self.nodes:
            self.statuses[mid] = "IN" if mid in winning_ids else "OUT"

        self._dirty = False

    def _fallback_eval(self, valid_defeats):
        in_args, out_args, changed, all_args = set(), set(), True, set(self.nodes.keys())
        while changed:
            changed = False
            for arg in all_args:
                if arg in in_args or arg in out_args:
                    continue
                attackers = [a for a, t in valid_defeats if t == arg]
                if not attackers or all(a in out_args for a in attackers):
                    in_args.add(arg)
                    changed = True
                elif any(a in in_args for a in attackers):
                    out_args.add(arg)
                    changed = True
        return in_args
