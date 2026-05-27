"""
tools/run_ablation.py
---------------------
Ablation study: re-run the 60 scenarios from tools/scenarios.py with
each of the engine's three distinguishing features individually
disabled. Reports how often the verdict on the root claim changes.

Ablations:
  FULL              Everything on (the baseline)
  NO_BIPOLAR        Support edges deleted
  NO_VALUE_TAGS     All value-tag multipliers forced to 1.0
  NO_WEIGHTS        All argument weights forced to 1
  NO_GRADUAL        Drop the gradual loop; use grounded extension instead

For each ablation we report:
  * Number of scenarios whose root status flips vs FULL
  * Mean absolute difference in root score vs FULL
  * The flipping scenarios named explicitly so they can be inspected

Outputs:
  tools/results/ablation_results.csv      Per-scenario per-ablation table
  tools/results/ablation_summary.txt      Headline impact stats
  tools/results/ablation_table.tex        LaTeX table for Chapter 5

Run from project root:
    python -m tools.run_ablation
"""
from __future__ import annotations
import csv
import os
import sys
from typing import Dict, List

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import logic_engine as le
from logic_engine import AcademicLogicEngine
from tools.scenarios import ALL_SCENARIOS

RESULTS_DIR = os.path.join(THIS_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ===================================================== ablation builders

def _build_baseline(scenario: Dict) -> AcademicLogicEngine:
    e = AcademicLogicEngine()
    for (mid, text, w, tag) in scenario["arguments"]:
        e.add_argument(mid, text, w, tag)
    for (atk, tgt) in scenario["attacks"]:
        e.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        e.add_support(sup, tgt)
    return e


def _build_no_bipolar(scenario: Dict) -> AcademicLogicEngine:
    e = AcademicLogicEngine()
    for (mid, text, w, tag) in scenario["arguments"]:
        e.add_argument(mid, text, w, tag)
    for (atk, tgt) in scenario["attacks"]:
        e.add_direct_attack(atk, tgt)
    # Skip supports entirely
    return e


def _build_no_value_tags(scenario: Dict) -> AcademicLogicEngine:
    # Tag everything as Ethics, whose multiplier is 1.0
    e = AcademicLogicEngine()
    for (mid, text, w, _tag) in scenario["arguments"]:
        e.add_argument(mid, text, w, "Ethics")
    for (atk, tgt) in scenario["attacks"]:
        e.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        e.add_support(sup, tgt)
    return e


def _build_no_weights(scenario: Dict) -> AcademicLogicEngine:
    e = AcademicLogicEngine()
    for (mid, text, _w, tag) in scenario["arguments"]:
        e.add_argument(mid, text, 1, tag)  # force weight to 1
    for (atk, tgt) in scenario["attacks"]:
        e.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        e.add_support(sup, tgt)
    return e


def _evaluate_grounded(scenario: Dict) -> Dict:
    """
    Classical grounded extension: ignore weights, value tags, supports.
    A node is IN if and only if all its attackers are OUT (fixed point).
    Implements Dung's grounded labelling for attack-only AFs.
    """
    nodes  = [arg[0] for arg in scenario["arguments"]]
    atks   = scenario["attacks"]
    status = {n: "UNDEC" for n in nodes}
    changed = True
    while changed:
        changed = False
        for n in nodes:
            if status[n] != "UNDEC":
                continue
            attackers = [a for (a, t) in atks if t == n]
            if all(status.get(a) == "OUT" for a in attackers):
                status[n] = "IN"; changed = True
            elif any(status.get(a) == "IN" for a in attackers):
                status[n] = "OUT"; changed = True
    # Anything still UNDEC at the end of grounded is treated as OUT for
    # binary comparison
    for n in nodes:
        if status[n] == "UNDEC":
            status[n] = "OUT"
    root_id = nodes[0]
    return {
        "id":    scenario["id"],
        "root":  root_id,
        "engine_root_status": status[root_id],
        "engine_root_score":  1.0 if status[root_id] == "IN" else 0.0,
    }


ABLATIONS = [
    ("FULL",          _build_baseline),
    ("NO_BIPOLAR",    _build_no_bipolar),
    ("NO_VALUE_TAGS", _build_no_value_tags),
    ("NO_WEIGHTS",    _build_no_weights),
]


# ============================================================ run

def run_one(scenario: Dict) -> Dict[str, Dict]:
    """Return {ablation_name: {root_status, root_score}} for one scenario."""
    out = {}
    root_id = scenario["arguments"][0][0]
    for name, builder in ABLATIONS:
        engine = builder(scenario)
        engine.evaluate_semantics()
        out[name] = {
            "status": engine.statuses.get(root_id, "OUT"),
            "score":  round(engine.scores.get(root_id, 0.0), 3),
        }
    g = _evaluate_grounded(scenario)
    out["NO_GRADUAL"] = {
        "status": g["engine_root_status"],
        "score":  g["engine_root_score"],
    }
    return out


def run_all() -> List[Dict]:
    rows = []
    for s in ALL_SCENARIOS:
        result = run_one(s)
        row = {
            "id":       s["id"],
            "name":     s["name"],
            "topology": s["topology"],
            "expected": s["expected"],
        }
        for name, _ in ABLATIONS + [("NO_GRADUAL", None)]:
            row[f"{name}_status"] = result[name]["status"]
            row[f"{name}_score"]  = result[name]["score"]
        rows.append(row)
    return rows


# ============================================================ reports

def write_csv(rows: List[Dict]) -> str:
    path = os.path.join(RESULTS_DIR, "ablation_results.csv")
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


def write_summary(rows: List[Dict]) -> str:
    path = os.path.join(RESULTS_DIR, "ablation_summary.txt")
    total = len(rows)

    def flip_stats(ablation_name: str):
        flips, mean_delta = 0, 0.0
        flipped_ids = []
        for r in rows:
            base = r["FULL_status"]
            test = r[f"{ablation_name}_status"]
            if base != test:
                flips += 1
                flipped_ids.append(r["id"])
            mean_delta += abs(r["FULL_score"] - r[f"{ablation_name}_score"])
        return flips, mean_delta / total, flipped_ids

    with open(path, "w") as f:
        f.write("LOGIC ADVOCATE TUTOR --- ABLATION STUDY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total scenarios: {total}\n\n")

        f.write(f"{'Ablation':<18} {'Flips':>6} {'Mean |delta s|':>16}\n")
        f.write("-" * 50 + "\n")
        for name in ("NO_BIPOLAR", "NO_VALUE_TAGS", "NO_WEIGHTS", "NO_GRADUAL"):
            flips, mean_delta, _ = flip_stats(name)
            pct = flips / total * 100
            f.write(f"{name:<18} {flips:>3}/{total:<2} ({pct:4.1f}%)  "
                    f"{mean_delta:>10.3f}\n")
        f.write("\n")

        for name in ("NO_BIPOLAR", "NO_VALUE_TAGS", "NO_WEIGHTS", "NO_GRADUAL"):
            _, _, ids = flip_stats(name)
            if ids:
                f.write(f"\n{name} flipped these scenarios:\n")
                for i in ids:
                    r = next(rr for rr in rows if rr["id"] == i)
                    f.write(f"  [{i}] {r['name']}: "
                            f"FULL={r['FULL_status']} (s={r['FULL_score']:.3f}) "
                            f"-> {name}={r[f'{name}_status']} "
                            f"(s={r[f'{name}_score']:.3f})\n")
    return path


def write_latex(rows: List[Dict]) -> str:
    path = os.path.join(RESULTS_DIR, "ablation_table.tex")
    total = len(rows)

    def count_flips(name: str):
        return sum(1 for r in rows if r["FULL_status"] != r[f"{name}_status"])

    def mean_delta(name: str):
        return sum(abs(r["FULL_score"] - r[f"{name}_score"])
                    for r in rows) / total

    with open(path, "w") as f:
        f.write("% Auto-generated by tools/run_ablation.py\n")
        f.write("% Paste into Chapter 5 (Results) of the thesis.\n\n")
        f.write("\\begin{table}[h]\n\\centering\n")
        f.write("\\caption{Ablation study: effect on root-claim verdict when "
                "each engine feature is disabled in turn. Computed on the same "
                "60 scenarios as Table~\\ref{tab:eval_agreement}.}\n")
        f.write("\\label{tab:ablation}\n")
        f.write("\\begin{tabular}{lrr}\n")
        f.write("\\toprule\n")
        f.write("Disabled component & Verdicts changed & Mean $|\\Delta s|$ \\\\\n")
        f.write("\\midrule\n")
        for name, label in [
            ("NO_BIPOLAR",     "Support relation $R_{sup}$"),
            ("NO_VALUE_TAGS",  "Value-tag multipliers $\\mu$"),
            ("NO_WEIGHTS",     "Per-argument weights $w$"),
            ("NO_GRADUAL",     "Gradual semantics (Dung grounded instead)"),
        ]:
            f.write(f"{label} & {count_flips(name)}/{total} "
                    f"& {mean_delta(name):.3f} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    return path


def main() -> None:
    print(f"Running ablation across {len(ALL_SCENARIOS)} scenarios x {len(ABLATIONS)+1} variants...\n")
    rows = run_all()
    csv_path = write_csv(rows)
    sum_path = write_summary(rows)
    tex_path = write_latex(rows)
    print("Outputs written:")
    print(f"  {csv_path}")
    print(f"  {sum_path}")
    print(f"  {tex_path}")
    print()
    # Quick preview
    with open(sum_path) as f:
        print(f.read())


if __name__ == "__main__":
    main()
