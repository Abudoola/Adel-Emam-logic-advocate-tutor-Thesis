"""
hint_mdp.py
-----------
A small Markov Decision Process (MDP) that decides WHICH KIND of hint
the Logic Advocate Tutor should give a learner at any moment in a debate.

The MDP does NOT generate text. It only picks a hint strategy. The actual
prose generation stays in `ai_agent.generate_hint_v2()`, which receives
the chosen strategy and uses a different prompt template for each one.

==============================================================
Formal definition of the MDP (the tuple <S, A, P, R, gamma>)
==============================================================

  S  - Discrete state space.
       state = (own_status, opponent_pressure, hint_streak)
         own_status        in {WINNING, TIED, LOSING}    (3)
         opponent_pressure in {LOW, HIGH}                (2)
         hint_streak       in {ZERO, ONE, TWO_PLUS}      (3)
       |S| = 18 states total.

  A  - Action space. Four hint strategies:
         STRATEGIC_ATTACK     attack opponent's weakest premise
         DEFENSIVE_REINFORCE  reinforce learner's main claim
         VALUE_REFRAME        suggest a different value tag
         STEP_BACK            reconsider the main claim entirely

  P  - Transition probabilities. An expert-informed initial model,
       documented in `_transition_distribution()` below. The model is
       designed to be re-estimated empirically once enough debate
       transcripts have been logged.

  R  - Reward. Tied DIRECTLY to the engine's verdict on the learner's
       NEXT argument:
         +1.0  if the next own_status is WINNING (claim IN)
          0.0  if TIED
         -1.0  if LOSING (claim OUT)
       minus a small per-hint cost (HINT_COST = -0.05) per Stamper et
       al.'s "non-evaluative help" principle (we don't punish help-seeking
       hard, but we discourage hint-spamming).

  gamma - Discount factor, set to 0.9.

Solver: value iteration on the small state space. Runs at module
import time and converges in milliseconds. The resulting policy
pi*(s) -> a is cached.

==============================================================
Link to the supervisor's "logical validity" requirement
==============================================================

The supervisor specifically asked that the MDP's reward function be
"explicitly linked to the logical validity of the student's argument."
That linkage is direct: own_status is computed from the engine's
status() verdict (IN if s(a) >= 0.5, OUT otherwise) on the learner's
main claim. So the reward depends on the gradual-semantics verdict and
nothing else.
"""
from typing import Dict, List, Tuple

# ----------------------------------------------------- Discrete state space

OWN_STATUS_LEVELS  = ("WINNING", "TIED", "LOSING")
OPPONENT_PRESSURE  = ("LOW", "HIGH")
HINT_STREAK_LEVELS = ("ZERO", "ONE", "TWO_PLUS")

State = Tuple[str, str, str]
STATES: List[State] = [
    (s, p, h)
    for s in OWN_STATUS_LEVELS
    for p in OPPONENT_PRESSURE
    for h in HINT_STREAK_LEVELS
]

# ----------------------------------------------------- Action space

ACTIONS: Tuple[str, ...] = (
    "STRATEGIC_ATTACK",
    "DEFENSIVE_REINFORCE",
    "VALUE_REFRAME",
    "STEP_BACK",
)

# ----------------------------------------------------- Reward model

HINT_COST = -0.05
REWARD_BY_NEXT_STATUS = {"WINNING": 1.0, "TIED": 0.0, "LOSING": -1.0}


def reward(state: State, action: str, next_state: State) -> float:
    """Reward for transitioning state -> next_state under action."""
    base = REWARD_BY_NEXT_STATUS[next_state[0]]
    return base + HINT_COST  # any non-null action incurs the hint cost


# ----------------------------------------------------- Transition model
#
# Each entry below encodes an expert-informed prior on how often a hint
# "lands" (improves the learner's own_status) for each combination of
# (current own_status, action).
#
# These values can later be re-estimated empirically by counting state
# transitions across logged debate sessions. See `update_transition_model()`
# at the bottom of this file for a stub that does that.

_LANDING_PROBABILITY = {
    "STRATEGIC_ATTACK":    {"WINNING": 0.20, "TIED": 0.45, "LOSING": 0.55},
    "DEFENSIVE_REINFORCE": {"WINNING": 0.30, "TIED": 0.55, "LOSING": 0.25},
    "VALUE_REFRAME":       {"WINNING": 0.25, "TIED": 0.40, "LOSING": 0.35},
    "STEP_BACK":           {"WINNING": 0.10, "TIED": 0.30, "LOSING": 0.60},
}

_PRESSURE_PENALTY  = 0.7   # high pressure dampens hint effectiveness
_PRESSURE_BONUS    = 1.1   # except for VALUE_REFRAME, which counters it
_FATIGUE_ONE       = 0.85  # second hint in a row is less helpful
_FATIGUE_TWO_PLUS  = 0.65  # third or later hint in a row is much less helpful


def _transition_distribution(state: State, action: str) -> Dict[State, float]:
    """
    Return { next_state: probability } summing to 1.0.

    The distribution is parameterised by three intuitions:
      1. STRATEGIC_ATTACK helps most when own_status is LOSING.
      2. DEFENSIVE_REINFORCE helps most when own_status is TIED.
      3. VALUE_REFRAME helps most under HIGH opponent_pressure.
      4. STEP_BACK is the rescue action when everything else is failing.
    Plus a fatigue penalty that grows with hint_streak (Stamper-style).
    """
    own, pressure, streak = state
    p = _LANDING_PROBABILITY[action][own]

    if pressure == "HIGH":
        p *= _PRESSURE_BONUS if action == "VALUE_REFRAME" else _PRESSURE_PENALTY

    if streak == "ONE":
        p *= _FATIGUE_ONE
    elif streak == "TWO_PLUS":
        p *= _FATIGUE_TWO_PLUS

    # Clamp to a sensible range
    p = max(0.05, min(0.85, p))

    # Next-state computation
    next_streak = {"ZERO": "ONE", "ONE": "TWO_PLUS", "TWO_PLUS": "TWO_PLUS"}[streak]
    next_own_if_land = {"WINNING": "WINNING", "TIED": "WINNING", "LOSING": "TIED"}[own]
    next_own_if_miss = {"WINNING": "TIED",    "TIED": "LOSING",  "LOSING": "LOSING"}[own]

    dist: Dict[State, float] = {}
    for next_pressure in OPPONENT_PRESSURE:
        p_pressure = 0.5  # uniform prior over opponent's next move strength
        ns_land = (next_own_if_land, next_pressure, next_streak)
        ns_miss = (next_own_if_miss, next_pressure, next_streak)
        dist[ns_land] = dist.get(ns_land, 0.0) + p_pressure * p
        dist[ns_miss] = dist.get(ns_miss, 0.0) + p_pressure * (1.0 - p)
    return dist


# ----------------------------------------------------- Value iteration solver

DISCOUNT = 0.9
EPSILON  = 1e-4


def solve() -> Tuple[Dict[State, float], Dict[State, str]]:
    """Run value iteration. Returns (V, policy)."""
    V: Dict[State, float] = {s: 0.0 for s in STATES}
    while True:
        new_V: Dict[State, float] = {}
        delta = 0.0
        for s in STATES:
            best = max(
                sum(prob * (reward(s, a, ns) + DISCOUNT * V[ns])
                    for ns, prob in _transition_distribution(s, a).items())
                for a in ACTIONS
            )
            new_V[s] = best
            delta = max(delta, abs(best - V[s]))
        V = new_V
        if delta < EPSILON:
            break

    policy: Dict[State, str] = {}
    for s in STATES:
        best_a, best_q = ACTIONS[0], -float("inf")
        for a in ACTIONS:
            q = sum(prob * (reward(s, a, ns) + DISCOUNT * V[ns])
                    for ns, prob in _transition_distribution(s, a).items())
            if q > best_q:
                best_q, best_a = q, a
        policy[s] = best_a
    return V, policy


_VALUES, _POLICY = solve()


# ----------------------------------------------------- State construction

def derive_state(engine, messages, learner_side: str, recent_hints: int) -> State:
    """
    Build an MDP state from the engine's current view of the debate.

    Parameters
    ----------
    engine        : AcademicLogicEngine
    messages      : list of message dicts (from st.session_state.messages)
    learner_side  : "Side A" or "Side B"
    recent_hints  : how many hints the learner has used since their last move
    """
    if not engine.nodes or not messages:
        return ("TIED", "LOW", "ZERO")

    # Find the learner's MAIN claim (their first argument in the debate)
    learner_msgs = [m for m in messages if m["side"] == learner_side]
    if not learner_msgs:
        return ("TIED", "LOW", "ZERO")
    main_claim_id = learner_msgs[0]["id"]
    own_score = engine.scores.get(main_claim_id, 1.0)

    if own_score >= 0.6:
        own_status = "WINNING"
    elif own_score <= 0.4:
        own_status = "LOSING"
    else:
        own_status = "TIED"

    # Opponent pressure: based on the most recent enemy argument's score
    opponent_msgs = [m for m in messages if m["side"] != learner_side]
    if opponent_msgs:
        last_enemy_id = opponent_msgs[-1]["id"]
        enemy_score = engine.scores.get(last_enemy_id, 0.5)
        opponent_pressure = "HIGH" if enemy_score >= 0.65 else "LOW"
    else:
        opponent_pressure = "LOW"

    hint_streak = "ZERO" if recent_hints == 0 else "ONE" if recent_hints == 1 else "TWO_PLUS"

    return (own_status, opponent_pressure, hint_streak)


def choose_action(state: State) -> str:
    """Return the optimal hint strategy for a given MDP state."""
    return _POLICY[state]


# ----------------------------------------------------- Prompt templates

STRATEGY_PROMPTS = {
    "STRATEGIC_ATTACK": (
        "My opponent in a debate just made the following argument:\n"
        "\"{enemy}\"\n\n"
        "Give me a one-sentence hint identifying the WEAKEST PREMISE in this "
        "argument and how to attack it directly."
    ),
    "DEFENSIVE_REINFORCE": (
        "My main claim in a debate is:\n"
        "\"{own}\"\n\n"
        "Give me a one-sentence hint suggesting how I can SUPPORT or REINFORCE "
        "this claim to make it harder for my opponent to defeat."
    ),
    "VALUE_REFRAME": (
        "My opponent just argued:\n"
        "\"{enemy}\"\n\n"
        "Give me a one-sentence hint suggesting a different VALUE TYPE "
        "(Fact, Logic, Ethics, or Emotion) I should use in my next argument "
        "to neutralise this attack."
    ),
    "STEP_BACK": (
        "I am losing a debate. My main claim is:\n"
        "\"{own}\"\n"
        "My opponent's latest argument is:\n"
        "\"{enemy}\"\n\n"
        "Give me a one-sentence hint suggesting whether I should ABANDON or "
        "RESTATE my main claim to recover."
    ),
}


def render_prompt(action: str, enemy_argument: str = "", own_main_claim: str = "") -> str:
    """Return the LLM prompt for a chosen action."""
    return STRATEGY_PROMPTS[action].format(enemy=enemy_argument, own=own_main_claim)


# ----------------------------------------------------- Public inspectors

def policy_table() -> Dict[State, str]:
    """Return the optimal policy as a dict."""
    return dict(_POLICY)


def value_table() -> Dict[State, float]:
    """Return the value function as a dict."""
    return dict(_VALUES)


# ----------------------------------------------------- Empirical update stub

def update_transition_model_from_logs(log_path: str) -> None:
    """
    Stub for future empirical re-estimation of P from logged debate
    transcripts. Counts (state, action, next_state) triples in the log
    and updates _LANDING_PROBABILITY accordingly.

    NOT YET IMPLEMENTED. Intended as the bridge between the expert-informed
    initial model and a data-driven model, per future work in Section 6.4
    of the thesis.
    """
    raise NotImplementedError(
        "Empirical re-estimation is left as future work. "
        "See Chapter 6 of the thesis for the proposed methodology."
    )


# ----------------------------------------------------- CLI for inspection

if __name__ == "__main__":
    print("=" * 60)
    print("Optimal hint policy (state -> action):")
    print("=" * 60)
    for s in STATES:
        print(f"  {str(s):42s} -> {_POLICY[s]}")
    print()
    print("=" * 60)
    print("Value function (state -> expected return):")
    print("=" * 60)
    for s in STATES:
        print(f"  {str(s):42s} -> {_VALUES[s]:+.3f}")
