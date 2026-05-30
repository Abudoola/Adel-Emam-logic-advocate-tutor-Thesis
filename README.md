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
  |  views/local_debate.py    views/ai_vs_ai.py            |
  |  views/engine_inspector.py    views/_styles.py         |
  +--------------------------------------------------------+
                                  |
                                  v
  +-------------------- Dialogue Layer --------------------+
  |  Turn manager, blitz timer, mode router                |
  |  app.py + parts of local_debate.py and ai_vs_ai.py     |
  +--------------------------------------------------------+
                                  |
        +------------- Symbolic ---|--- Neural ----------+
        v                                                v
  +-------------+                                  +--------------+
  | logic_engine|                                  |  ai_agent    |
  |  .py        |                                  |   .py        |
  | hint_mdp.py |                                  | (Groq /      |
  | tikz_export |                                  |  LLaMA-3 /   |
  |  .py        |                                  |  Whisper)    |
  +-------------+                                  +--------------+
```

## Setup

```bash
pip install -r requirements.txt
# Put your Groq API key in .streamlit/secrets.toml:
#   GROQ_API_KEY  = "gsk_..."
#   AIVAI_API_KEY = "gsk_..."   # optional, for AI vs AI mode
streamlit run app.py
```

## Game modes

| Mode | Description |
|------|-------------|
| Human vs AI | You debate against a LLaMA-3 opponent constrained by the engine |
| Human vs Human (Local) | Two debaters share the same machine, taking turns |
| AI vs AI | Two LLaMA-3 agents debate each other; user configures the topic |

## Files

| File | Role |
|------|------|
| `app.py` | Entry point and mode router |
| `logic_engine.py` | **SYMBOLIC** Bipolar Gradual argumentation engine |
| `hint_mdp.py` | **SYMBOLIC** Markov Decision Process for hint strategy |
| `ai_agent.py` | **NEURAL** Groq/LLaMA-3/Whisper wrapper |
| `spellcheck.py` | Offline pre-submission spell check |
| `tikz_export.py` | Export the current debate as a LaTeX TikZ figure |
| `views/local_debate.py` | Single-machine UI (Human-vs-AI and Human-vs-Human Local) |
| `views/ai_vs_ai.py` | AI-vs-AI tournament view |
| `views/engine_inspector.py` | Defense Mode panel — shows engine internals |
| `views/_styles.py` | Shared CSS and small render helpers |

## Defense Mode

The Engine Inspector panel at the bottom of any active debate shows the
SYMBOLIC vs NEURAL separation: the engine state, the MDP state, the
optimal hint action, a "Why am I losing?" diagnostic, and a "What If?"
sandbox that lets you mutate any node and see the verdict change.

## Pedagogical Guarantee

The LLM cannot fake who is winning. Every score on every widget is
computed by the deterministic engine and only by the engine. When the
math says the AI has lost, the AI emits a `CONCEDE` sentinel and the
debate ends. See Section 4.3.2 of the thesis ("How I ground the LLM")
for the technical details.

## Evaluation tools (`tools/` folder)

| Script | What it produces | Run |
|--------|------------------|-----|
| `tools.run_evaluation` | Engine vs human-expert audit (60 scenarios) | `python -m tools.run_evaluation` |
| `tools.run_ablation` | Effect of disabling each engine feature | `python -m tools.run_ablation` |
| `tools.run_hint_comparison` | MDP-guided vs naive hint comparison | `python -m tools.run_hint_comparison --limit 20` |
| `tools.run_self_play` | Self-play tournament (CLI batch) | `python -m tools.run_self_play --batch tools/topics.txt` |
| `tools.make_rater_template` | Excel workbook with kappa formulas | `python -m tools.make_rater_template` |

## Tests

```bash
python run_tests.py            # standalone runner, no pytest needed
pytest tests/                  # full pytest with parametrisation
```

101 passing assertions across engine, MDP, scenarios, and TikZ export.
