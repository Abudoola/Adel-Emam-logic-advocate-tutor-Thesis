# Logic Advocate Tutor

Bachelor thesis project (GUC, SS26) by Adel Ashraf Mohamed Kamel Emam.

An interactive web tutor that binds a generative language model
(LLaMA-3 via Groq) to a deterministic Bipolar Gradual argumentation
engine. The engine, not the LLM, decides who is winning every debate.

## Architecture

```
                                User
                                  |
                                  v
  +-------------------- Presentation Layer ----------------+
  |  views/local_debate.py   views/mobile_multiplayer.py   |
  |  views/engine_inspector.py    views/_styles.py         |
  +--------------------------------------------------------+
                                  |
                                  v
  +-------------------- Dialogue Layer --------------------+
  |  Turn manager, blitz timer, lobby state machine        |
  |  app.py, parts of local_debate.py and mobile_*.py      |
  +--------------------------------------------------------+
                                  |
        +------------- Symbolic ---|--- Neural ----------+
        v                                                v
  +-------------+                                  +--------------+
  | logic_engine|                                  |  ai_agent    |
  |  .py        |                                  |   .py        |
  | hint_mdp.py |                                  | (Groq /      |
  | lobby_db.py |                                  |  LLaMA-3 /   |
  +-------------+                                  |  Whisper)    |
                                                   +--------------+
```

## Setup

```bash
pip install -r requirements.txt
# Add your Groq API key to .streamlit/secrets.toml
# GROQ_API_KEY = "gsk_..."
streamlit run app.py
```

## Files

| File | Role |
|------|------|
| `app.py` | Entry point and mode router |
| `logic_engine.py` | **SYMBOLIC** Bipolar Gradual argumentation engine |
| `hint_mdp.py` | **SYMBOLIC** Markov Decision Process for hint strategy |
| `ai_agent.py` | **NEURAL** Groq/LLaMA-3/Whisper wrapper |
| `lobby_db.py` | JSON-backed lobby store for online mode |
| `views/local_debate.py` | Single-machine UI (HvAI + Local HvH) |
| `views/mobile_multiplayer.py` | Online host dashboard + player view |
| `views/engine_inspector.py` | Defense Mode panel — shows engine internals |
| `views/_styles.py` | Shared CSS and small render helpers |

## Defense Mode

The Engine Inspector panel at the bottom of any active debate shows the
SYMBOLIC vs NEURAL separation: the engine state, the MDP state, the
optimal hint action, and a "Why am I losing?" diagnostic. It is intended
to make the formal architecture visible to a viewer.

## Pedagogical Guarantee

The LLM cannot fake who is winning. Every score on every widget is
computed by the deterministic engine and only by the engine. When the
math says the AI has lost, the AI emits a `CONCEDE` sentinel and the
debate ends. See Section 4.3.2 of the thesis ("How I ground the LLM")
for the technical details.

## Evaluation tools (`tools/` folder)

Four scripts produce the quantitative material the thesis Chapter 5 needs.
All are CLI-only: no Streamlit, no UI.

| Script | What it produces | Run with |
|--------|------------------|----------|
| `tools.run_evaluation` | Engine vs human-expert verdict on 60 scenarios | `python -m tools.run_evaluation` |
| `tools.run_ablation` | Effect of disabling each engine feature in turn | `python -m tools.run_ablation` |
| `tools.run_hint_comparison` | MDP-guided hint vs naive single-call hint, blinded | `python -m tools.run_hint_comparison --limit 20` |
| `tools.make_rater_template` | Excel workbook with kappa + means built in | `python -m tools.make_rater_template` |

Outputs land in `tools/results/`:

- `evaluation_results.csv`, `evaluation_summary.txt`, `evaluation_table.tex`
- `ablation_results.csv`, `ablation_summary.txt`, `ablation_table.tex`
- `hint_comparison.csv`
- `rater_template.xlsx`

Scenario dataset lives in `tools/scenarios.py` (60 hand-crafted graphs across
linear-chain, star, bipolar, and long mixed-shape topologies).
