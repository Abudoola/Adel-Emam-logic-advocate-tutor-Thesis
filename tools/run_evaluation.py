"""
tools/run_evaluation.py
-----------------------
Run every scenario from tools/scenarios.py through the engine, compare
the engine's verdict against the hand-labelled human-expert verdict,
and write:

  - tools/results/evaluation_results.csv      Full per-scenario table
  - tools/results/evaluation_summary.txt      Headline agreement stats
  - tools/results/evaluation_table.tex        Pre-formatted LaTeX table
                                              (paste into Chapter 5)

Run from the project root:
    python -m tools.run_evaluation

This script touches NO external services (no Groq, no Streamlit), so
it runs in a few seconds and can be re-run any time the engine or
scenarios change.
"""
from __future__ import annotations
import csv
import os
import sys
from typing import Dict, List

# Make the project root importable when running as a module
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from logic_engine import AcademicLogicEngine
from tools.scenarios import ALL_SCENARIOS


RESULTS_DIR = os.path.join(THIS_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# =============================================================== run

def run_scenario(scenario: Dict) -> Dict:
    """Build an engine for one scenario and return its verdict + diagnostics.

    Returns the verdict from three semantics on the same input:
      * `engine`            -- my bipolar gradual semantics (k = 0.5)
      * `dung_grounded`     -- classical Dung grounded extension
      * `hcat`              -- Besnard-Hunter h-categorizer
    Each is independently compared against the human-expert label so
    the Chapter 5 baseline table can be regenerated from this script.
    """
    engine = AcademicLogicEngine()
    for (mid, text, weight, tag) in scenario["arguments"]:
        engine.add_argument(mid, text, weight, tag)
    for (atk, tgt) in scenario["attacks"]:
        engine.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        engine.add_support(sup, tgt)
    engine.evaluate_semantics()

    root_id = scenario["arguments"][0][0]
    root_score = engine.scores.get(root_id, 0.0)
    root_status = engine.statuses.get(root_id, "OUT")

    # Classical Dung grounded extension. Root is IN iff it sits in
    # the least fixed point of the characteristic function.
    grounded_S = engine.grounded_extension()
    dung_status = "IN" if root_id in grounded_S else "OUT"

    # Besnard-Hunter h-categorizer. Threshold at 0.5 to recover a
    # binary IN/OUT verdict on the same root argument.
    hcat_scores = engine.h_categorizer()
    hcat_score = hcat_scores.get(root_id, 0.0)
    hcat_status = "IN" if hcat_score >= 0.5 else "OUT"

    expected = scenario["expected"]
    return {
        "id":             scenario["id"],
        "name":           scenario["name"],
        "topology":       scenario["topology"],
        "n_args":         len(scenario["arguments"]),
        "n_attacks":      len(scenario["attacks"]),
        "n_supports":     len(scenario["supports"]),
        "expected":       expected,
        "engine":         root_status,
        "score":          round(root_score, 3),
        "agreement":      "Y" if expected == root_status else "N",
        "dung":           dung_status,
        "dung_agreement": "Y" if expected == dung_status else "N",
        "hcat":           hcat_status,
        "hcat_score":     round(hcat_score, 3),
        "hcat_agreement": "Y" if expected == hcat_status else "N",
        "iters":          engine.convergence_info()["iterations_until_stable"],
        "reasoning":      scenario["reasoning"],
    }


def run_all() -> List[Dict]:
    return [run_scenario(s) for s in ALL_SCENARIOS]


# =============================================================== reports

def write_csv(rows: List[Dict]) -> str:
    path = os.path.join(RESULTS_DIR, "evaluation_results.csv")
    fields = list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


def write_summary(rows: List[Dict]) -> str:
    path = os.path.join(RESULTS_DIR, "evaluation_summary.txt")
    total = len(rows)
    agree = sum(1 for r in rows if r["agreement"] == "Y")
    pct = agree / total * 100 if total else 0

    by_topology = {}
    for r in rows:
        t = r["topology"]
        by_topology.setdefault(t, {"agree": 0, "total": 0, "disagree_ids": []})
        by_topology[t]["total"] += 1
        if r["agreement"] == "Y":
            by_topology[t]["agree"] += 1
        else:
            by_topology[t]["disagree_ids"].append(r["id"])

    with open(path, "w") as f:
        f.write("LOGIC ADVOCATE TUTOR --- EVALUATION SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Overall agreement with human-expert labels: {agree}/{total} "
                f"({pct:.1f}%)\n\n")

        f.write("Breakdown by topology:\n")
        f.write("-" * 60 + "\n")
        for t in ("LIN", "STR", "BIP", "LNG"):
            if t not in by_topology:
                continue
            d = by_topology[t]
            tpct = d["agree"] / d["total"] * 100 if d["total"] else 0
            label = {
                "LIN": "Linear chains      ",
                "STR": "Star attacks       ",
                "BIP": "Bipolar mixed      ",
                "LNG": "Long mixed-shape   ",
            }[t]
            f.write(f"  {label}: {d['agree']:>2}/{d['total']:>2}  "
                    f"({tpct:5.1f}%)\n")
            if d["disagree_ids"]:
                f.write(f"    Disagreements: {', '.join(d['disagree_ids'])}\n")
        f.write("\n")
        f.write("Average score of root arguments labelled IN:    "
                f"{_mean([r['score'] for r in rows if r['expected']=='IN']):.3f}\n")
        f.write("Average score of root arguments labelled OUT:   "
                f"{_mean([r['score'] for r in rows if r['expected']=='OUT']):.3f}\n")
        f.write("Average iterations until score vector stable:   "
                f"{_mean([r['iters'] for r in rows]):.1f}\n")

        if any(r["agreement"] == "N" for r in rows):
            f.write("\nDisagreement detail:\n")
            f.write("-" * 60 + "\n")
            for r in rows:
                if r["agreement"] == "N":
                    f.write(f"  [{r['id']}] {r['name']}: expected {r['expected']}, "
                            f"engine said {r['engine']} (score={r['score']:.3f})\n")
                    f.write(f"     Reasoning: {r['reasoning']}\n")
    return path


def write_latex_table(rows: List[Dict]) -> str:
    """A booktabs-style LaTeX table you can paste directly into Ch 5."""
    path = os.path.join(RESULTS_DIR, "evaluation_table.tex")

    total = len(rows)
    agree = sum(1 for r in rows if r["agreement"] == "Y")
    pct = agree / total * 100 if total else 0

    by_topology = {}
    for r in rows:
        t = r["topology"]
        by_topology.setdefault(t, [0, 0])
        by_topology[t][1] += 1
        if r["agreement"] == "Y":
            by_topology[t][0] += 1

    with open(path, "w") as f:
        f.write("% Auto-generated by tools/run_evaluation.py\n")
        f.write("% Paste into Chapter 5 (Results) of the thesis.\n\n")

        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\caption{Engine verdict vs.~human-expert label across 60 "
                "argumentative scenarios, grouped by graph topology.}\n")
        f.write("\\label{tab:eval_agreement}\n")
        f.write("\\begin{tabular}{lrrr}\n")
        f.write("\\toprule\n")
        f.write("Topology & Scenarios & Agreement & Rate \\\\\n")
        f.write("\\midrule\n")
        for t, label in [("LIN", "Linear chains"),
                          ("STR", "Star attacks"),
                          ("BIP", "Bipolar mixed"),
                          ("LNG", "Long mixed-shape")]:
            if t in by_topology:
                a, n = by_topology[t]
                f.write(f"{label} & {n} & {a}/{n} & "
                        f"{a/n*100:.1f}\\% \\\\\n")
        f.write("\\midrule\n")
        f.write(f"\\textbf{{Overall}} & \\textbf{{{total}}} & "
                f"\\textbf{{{agree}/{total}}} & "
                f"\\textbf{{{pct:.1f}\\%}} \\\\\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")
    return path


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


# ============================================================ main

def main() -> None:
    print(f"Running {len(ALL_SCENARIOS)} scenarios through the engine...\n")
    rows = run_all()

    csv_path = write_csv(rows)
    sum_path = write_summary(rows)
    tex_path = write_latex_table(rows)

    total = len(rows)
    agree = sum(1 for r in rows if r["agreement"] == "Y")
    pct = agree / total * 100 if total else 0

    print(f"Agreement: {agree}/{total} ({pct:.1f}%)\n")
    print("Outputs written:")
    print(f"  {csv_path}")
    print(f"  {sum_path}")
    print(f"  {tex_path}")


if __name__ == "__main__":
    main()
