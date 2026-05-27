"""
tools/run_self_play.py
----------------------
Self-play tournament: two LLaMA-3 agents debate each other, both
constrained by the deterministic AcademicLogicEngine.

This produces real quantitative data without needing human volunteers.
Use it to:
  * generate transcripts for thesis examples
  * measure Side-A win rates across topics, value-tag biases, etc.
  * stress-test the engine against AI-generated traffic at scale
  * benchmark prompt-engineering changes by re-running the same topics

Usage:
    # one-off debate on a single topic
    python -m tools.run_self_play \
        --topic "Schools should ban smartphones" \
        --turns 10

    # batch mode: 50 debates across topics in a file
    python -m tools.run_self_play \
        --batch tools/topics.txt --turns 10

    # dry-run with no API calls
    python -m tools.run_self_play --topic "test" --dry-run

Outputs in tools/results/self_play/:
    * <slug>__<timestamp>__transcript.json   full move history
    * <slug>__<timestamp>__final.txt         human-readable summary
    * (batch mode) self_play_summary.csv     aggregated win/loss table
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import random
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from logic_engine import AcademicLogicEngine

RESULTS_DIR = os.path.join(THIS_DIR, "results", "self_play")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================== prompts

SIDE_A_SYSTEM = (
    "You are Side A in a structured debate. You ARGUE FOR the proposition. "
    "Reply in ONE concise sentence (max 25 words). "
    "Be specific, factual when possible, and avoid hedging."
)

SIDE_B_SYSTEM = (
    "You are Side B in a structured debate. You ARGUE AGAINST the proposition. "
    "Reply in ONE concise sentence (max 25 words). "
    "Be specific, factual when possible, and avoid hedging."
)


# ============================================================== helpers

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "untitled"


def _classify_value_tag(text: str) -> str:
    """
    Lightweight heuristic to tag a generated argument with one of the
    four value classes. Cheap and deterministic so it does not require
    an extra API call per move.
    """
    tl = text.lower()
    if any(w in tl for w in ("study", "research", "data", "statistics",
                              "%", "percent", "according to", "evidence",
                              "shows that", "found that")):
        return "Fact"
    if any(w in tl for w in ("feel", "feels", "scared", "fear", "love",
                              "happy", "sad", "horrible", "amazing",
                              "tragic", "heartbreaking")):
        return "Emotion"
    if any(w in tl for w in ("right", "wrong", "moral", "ethical",
                              "fair", "unfair", "should", "ought",
                              "duty", "justice", "human dignity")):
        return "Ethics"
    return "Logic"


def _word_count(text: str) -> int:
    return len(text.split())


# ============================================================== generation

def _generate_side_move(client, model, system_prompt: str, topic: str,
                         transcript: List[Dict], temperature: float = 0.7,
                         max_tokens: int = 80) -> str:
    """Ask one side's LLM to produce its next move."""
    history_text = "\n".join(
        f"{m['side']}: {m['content']}" for m in transcript
    )
    user_msg = (
        f"Debate topic: {topic}\n\n"
        f"Debate so far:\n{history_text or '(no moves yet)'}\n\n"
        "Your turn. Reply in one sentence."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_msg},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip().split("\n")[0]


# ============================================================== one debate

def run_one_debate(topic: str, turns: int = 10,
                    dry_run: bool = False,
                    seed: Optional[int] = None) -> Dict:
    """Run a single self-play debate and return a transcript dict."""
    if seed is not None:
        random.seed(seed)

    if dry_run:
        client = None
        model = "(dry-run)"
    else:
        try:
            import streamlit as st
            from groq import Groq
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            model = "llama-3.3-70b-versatile"
        except Exception as e:
            print(f"Could not initialise Groq client: {e}")
            print("Re-run with --dry-run for an API-free preview.")
            sys.exit(1)

    engine = AcademicLogicEngine()
    transcript: List[Dict] = []
    msg_counter = 1
    last_side: Optional[str] = None

    # First move: Side A opens with the proposition itself
    if dry_run:
        opening = f"(DRY-RUN opening) {topic}"
    else:
        opening = _generate_side_move(
            client, model, SIDE_A_SYSTEM, topic, transcript,
        )
    open_tag = _classify_value_tag(opening)
    open_w = min(25, _word_count(opening) + 5)
    mid_open = f"Msg_{msg_counter}"
    engine.add_argument(mid_open, opening, open_w, open_tag)
    transcript.append({
        "id":        mid_open,
        "side":      "Side A",
        "content":   opening,
        "value_tag": open_tag,
        "weight":    open_w,
        "action":    "Attack",
        "target":    None,
    })
    msg_counter += 1
    last_side = "Side A"

    # Subsequent turns: alternate sides, each attacks the opponent's last move
    for _ in range(turns - 1):
        cur_side  = "Side B" if last_side == "Side A" else "Side A"
        system    = SIDE_B_SYSTEM if cur_side == "Side B" else SIDE_A_SYSTEM
        if dry_run:
            text = f"(DRY-RUN {cur_side} reply turn {msg_counter})"
        else:
            try:
                text = _generate_side_move(
                    client, model, system, topic, transcript,
                )
            except Exception as e:
                text = f"[generation error: {e}]"
                break

        # Target is the last enemy message
        target_id = next(
            (m["id"] for m in reversed(transcript) if m["side"] != cur_side),
            None,
        )
        if target_id is None:
            break

        tag = _classify_value_tag(text)
        w   = min(25, _word_count(text) + 5)
        mid = f"Msg_{msg_counter}"
        engine.add_argument(mid, text, w, tag)
        engine.add_direct_attack(mid, target_id)
        transcript.append({
            "id":        mid,
            "side":      cur_side,
            "content":   text,
            "value_tag": tag,
            "weight":    w,
            "action":    "Attack",
            "target":    target_id,
        })
        msg_counter += 1
        last_side = cur_side

        if not dry_run:
            time.sleep(0.2)  # gentle rate-limit

    engine.evaluate_semantics()
    root_id = transcript[0]["id"]
    root_score = engine.scores.get(root_id, 0.0)
    root_status = engine.statuses.get(root_id, "OUT")
    winner = "Side A" if root_status == "IN" else "Side B"

    # Per-side surviving weight (momentum-bar style)
    side_a_weight = sum(
        engine.nodes[m["id"]]["weight"] for m in transcript
        if engine.statuses.get(m["id"]) == "IN" and m["side"] == "Side A"
    )
    side_b_weight = sum(
        engine.nodes[m["id"]]["weight"] for m in transcript
        if engine.statuses.get(m["id"]) == "IN" and m["side"] == "Side B"
    )

    return {
        "topic":          topic,
        "turns":          len(transcript),
        "root_score":     round(root_score, 3),
        "root_status":    root_status,
        "winner":         winner,
        "side_a_weight":  side_a_weight,
        "side_b_weight":  side_b_weight,
        "transcript":     transcript,
        "convergence":    engine.convergence_info(),
        "value_tag_counts": _tag_counts(transcript),
    }


def _tag_counts(transcript: List[Dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for m in transcript:
        out[m["value_tag"]] = out.get(m["value_tag"], 0) + 1
    return out


# ============================================================== persistence

def save_debate(result: Dict, prefix: str = "") -> Tuple[str, str]:
    ts = time.strftime("%Y%m%d_%H%M%S")
    slug = _slug(result["topic"])
    name = f"{prefix}{slug}__{ts}"

    transcript_path = os.path.join(RESULTS_DIR, f"{name}__transcript.json")
    with open(transcript_path, "w") as f:
        json.dump(result, f, indent=2)

    summary_path = os.path.join(RESULTS_DIR, f"{name}__final.txt")
    with open(summary_path, "w") as f:
        f.write(f"Topic: {result['topic']}\n")
        f.write(f"Turns: {result['turns']}\n")
        f.write(f"Winner: {result['winner']}\n")
        f.write(f"Root score: {result['root_score']:.3f}\n")
        f.write(f"Side A surviving weight: {result['side_a_weight']}\n")
        f.write(f"Side B surviving weight: {result['side_b_weight']}\n")
        f.write(f"Value-tag counts: {result['value_tag_counts']}\n")
        f.write(f"Convergence iterations: "
                f"{result['convergence']['iterations_until_stable']}\n")
        f.write("\nFull transcript:\n")
        f.write("=" * 60 + "\n")
        for m in result["transcript"]:
            tgt = f" -> {m['target']}" if m.get("target") else ""
            f.write(f"[{m['id']}] {m['side']} ({m['value_tag']}, "
                    f"w={m['weight']}){tgt}\n")
            f.write(f"    {m['content']}\n\n")
    return transcript_path, summary_path


def append_batch_row(result: Dict, batch_csv_path: str) -> None:
    new_file = not os.path.exists(batch_csv_path)
    with open(batch_csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow([
                "topic", "winner", "root_score", "turns",
                "side_a_weight", "side_b_weight",
                "fact_count", "logic_count", "ethics_count", "emotion_count",
            ])
        tc = result["value_tag_counts"]
        w.writerow([
            result["topic"], result["winner"], result["root_score"],
            result["turns"], result["side_a_weight"], result["side_b_weight"],
            tc.get("Fact", 0), tc.get("Logic", 0),
            tc.get("Ethics", 0), tc.get("Emotion", 0),
        ])


# ============================================================== batch driver

def run_batch(topics_path: str, turns: int, dry_run: bool) -> None:
    with open(topics_path) as f:
        topics = [line.strip() for line in f if line.strip()
                   and not line.startswith("#")]
    print(f"Running {len(topics)} debates ({turns} turns each)")
    batch_csv = os.path.join(RESULTS_DIR, "self_play_summary.csv")
    if os.path.exists(batch_csv):
        os.rename(batch_csv, batch_csv + ".bak")
    wins_a = 0
    for i, topic in enumerate(topics, 1):
        print(f"  [{i:>3}/{len(topics)}] {topic[:60]}...")
        result = run_one_debate(topic, turns=turns, dry_run=dry_run, seed=i)
        save_debate(result, prefix=f"batch{i:03d}__")
        append_batch_row(result, batch_csv)
        if result["winner"] == "Side A":
            wins_a += 1

    pct = wins_a / len(topics) * 100 if topics else 0
    print()
    print(f"Side A win rate: {wins_a}/{len(topics)} ({pct:.1f}%)")
    print(f"Summary CSV: {batch_csv}")


# ============================================================== main

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--topic", help="Single topic to debate.")
    p.add_argument("--batch", help="Path to a text file with one topic per line.")
    p.add_argument("--turns", type=int, default=10,
                    help="Total moves per debate (default 10).")
    p.add_argument("--dry-run", action="store_true",
                    help="Skip API calls, use placeholder text.")
    args = p.parse_args()

    if not args.topic and not args.batch:
        p.error("Provide --topic or --batch")

    if args.batch:
        run_batch(args.batch, args.turns, args.dry_run)
    else:
        result = run_one_debate(args.topic, turns=args.turns,
                                  dry_run=args.dry_run)
        tp, sp = save_debate(result)
        print()
        print(f"Topic:        {result['topic']}")
        print(f"Winner:       {result['winner']} (root s={result['root_score']:.3f})")
        print(f"Turns played: {result['turns']}")
        print(f"Tag counts:   {result['value_tag_counts']}")
        print()
        print(f"Transcript: {tp}")
        print(f"Summary:    {sp}")


if __name__ == "__main__":
    main()
