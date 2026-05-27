"""
tools/run_hint_comparison.py
-----------------------------
Generate paired hints for a sample of scenarios:
  * one hint from the MDP-guided pipeline (generate_hint_v2)
  * one hint from the naive baseline    (generate_hint)

Outputs a CSV with both hints and blank rating columns. The user
then fills in their (and ideally one or two classmates') quality
scores from 1 (useless) to 5 (excellent, actionable), and a Cohen's-
kappa-friendly spreadsheet (tools/rater_template.xlsx) is provided
separately for aggregation.

Two safety modes:
  --dry-run    Skip all API calls. Just verify scenario selection
               and CSV scaffolding. Free.
  --limit N    Run only N scenarios (default 20). Each scenario
               costs ~2 Groq API calls so 20 = 40 calls total,
               which is well within the free tier.

Run from project root:
    python -m tools.run_hint_comparison --limit 20
    python -m tools.run_hint_comparison --dry-run    # safe preview
"""
from __future__ import annotations
import argparse
import csv
import os
import random
import sys
import time
from typing import Dict, List

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from logic_engine import AcademicLogicEngine
from hint_mdp import derive_state, choose_action, render_prompt
from tools.scenarios import ALL_SCENARIOS

RESULTS_DIR = os.path.join(THIS_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def _build_engine_and_messages(scenario: Dict):
    """Build a (engine, messages) pair as if Side A played the scenario."""
    engine = AcademicLogicEngine()
    messages = []
    for (mid, text, w, tag) in scenario["arguments"]:
        engine.add_argument(mid, text, w, tag)

    # Reconstruct sides: Msg_1 root by Side A, then alternating.
    # Since the scenario uses ids like a1, a2, a3..., we map them to Side A
    # for the root and to whichever side based on attack source.
    a1 = scenario["arguments"][0][0]
    sides = {a1: "Side A"}
    for (atk, tgt) in scenario["attacks"]:
        if atk not in sides:
            sides[atk] = "Side B" if sides.get(tgt, "Side B") == "Side A" else "Side A"
    for (sup, tgt) in scenario["supports"]:
        if sup not in sides:
            sides[sup] = sides.get(tgt, "Side A")

    for (mid, text, w, tag) in scenario["arguments"]:
        atk_target = next((t for (a, t) in scenario["attacks"] if a == mid), None)
        sup_target = next((t for (s, t) in scenario["supports"] if s == mid), None)
        target = atk_target or sup_target
        action = "Attack" if atk_target else ("Support" if sup_target else "Attack")
        messages.append({
            "id":        mid,
            "content":   text,
            "side":      sides.get(mid, "Side A"),
            "target":    target,
            "action":    action,
            "weight":    w,
            "value_tag": tag,
        })

    for (atk, tgt) in scenario["attacks"]:
        engine.add_direct_attack(atk, tgt)
    for (sup, tgt) in scenario["supports"]:
        engine.add_support(sup, tgt)
    engine.evaluate_semantics()
    return engine, messages


def select_scenarios(limit: int) -> List[Dict]:
    """Pick scenarios where Side A has at least one Side B argument to receive a hint about."""
    eligible = []
    for s in ALL_SCENARIOS:
        if not s["attacks"]:  # no enemy moves yet, hint makes no sense
            continue
        eligible.append(s)
    random.seed(42)
    return random.sample(eligible, min(limit, len(eligible)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20,
                        help="How many scenarios to compare. Default 20.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip the Groq API calls. Useful for preview.")
    args = parser.parse_args()

    selected = select_scenarios(args.limit)
    print(f"Selected {len(selected)} scenarios for hint comparison.")
    if args.dry_run:
        print("Dry-run mode: no API calls will be made.\n")
    else:
        print("Calling Groq API (this may take 30-60 seconds)...\n")

    # Only import ai_agent if we actually need API calls. ai_agent imports
    # streamlit (for st.secrets), so we route around it in dry-run mode.
    if not args.dry_run:
        try:
            from ai_agent import generate_hint_v2, generate_hint
        except Exception as e:
            print(f"Could not import ai_agent (needs Streamlit + secrets.toml): {e}")
            print("Re-run with --dry-run to skip API calls.")
            sys.exit(1)

    rows = []
    for i, s in enumerate(selected, 1):
        engine, messages = _build_engine_and_messages(s)
        side_a_msgs = [m for m in messages if m["side"] == "Side A"]
        side_b_msgs = [m for m in messages if m["side"] == "Side B"]
        own_main_claim = side_a_msgs[0]["content"] if side_a_msgs else ""
        enemy_arg = side_b_msgs[-1]["content"] if side_b_msgs else ""
        mdp_state = derive_state(engine, messages, "Side A", recent_hints=0)
        mdp_action = choose_action(mdp_state)

        if args.dry_run:
            mdp_hint = f"[DRY-RUN: would call MDP-guided LLM with strategy {mdp_action}]"
            naive_hint = "[DRY-RUN: would call naive single-call LLM]"
        else:
            mdp_result = generate_hint_v2(
                engine=engine,
                messages=messages,
                learner_side="Side A",
                recent_hints=0,
                enemy_argument=enemy_arg,
                own_main_claim=own_main_claim,
            )
            mdp_hint = mdp_result["hint"]
            naive_hint = generate_hint(enemy_arg)
            time.sleep(0.3)  # gentle rate-limit

        print(f"  [{i:>2}/{len(selected)}] {s['id']} ({s['topology']}, "
              f"MDP={mdp_action})")

        # Randomise order so the rater does not know which is which
        order_a_is_mdp = bool((hash(s["id"]) + i) % 2)
        hint_a = mdp_hint  if order_a_is_mdp else naive_hint
        hint_b = naive_hint if order_a_is_mdp else mdp_hint
        rows.append({
            "scenario_id":         s["id"],
            "scenario_name":       s["name"],
            "topology":            s["topology"],
            "own_main_claim":      own_main_claim,
            "enemy_argument":      enemy_arg,
            "mdp_state":           str(mdp_state),
            "mdp_action":          mdp_action,
            "hint_A":              hint_a,
            "hint_B":              hint_b,
            "_hidden_A_is_mdp":    order_a_is_mdp,
            "rating_A_actionable_1to5":  "",
            "rating_B_actionable_1to5":  "",
            "rater_notes":         "",
        })

    out_path = os.path.join(RESULTS_DIR, "hint_comparison.csv")
    fields = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out_path}")
    print()
    print("Next steps:")
    print("  1. Open the CSV in Excel.")
    print("  2. For each row, read hint_A and hint_B and rate each on a 1-5 scale")
    print("     of actionability. Do NOT look at the _hidden_A_is_mdp column;")
    print("     it is there only to decode the blind labels after rating.")
    print("  3. (Optional) Have one or two classmates rate the same CSV.")
    print("  4. Open tools/results/rater_template.xlsx for aggregation and")
    print("     Cohen's kappa across raters.")


if __name__ == "__main__":
    main()
