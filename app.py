"""
app.py
------
Entry point for the Logic Advocate Tutor Streamlit app.

Three modes:
  * Human vs AI   — single-machine debate against a LLaMA-3 opponent
  * Human vs Human (Local) — two humans sharing the same screen
  * AI vs AI      — two LLaMA-3 agents debate each other

Mode changes preserve each mode's debate state under a per-mode stash
so flipping between modes does not lose any data.
"""
import os
import streamlit as st

from views.local_debate import render_local_debate
from views.ai_vs_ai import render_ai_vs_ai

st.set_page_config(page_title="Logic Advocate Arena", layout="wide")

os.makedirs("uploads", exist_ok=True)

MODES = [
    "🤖 Human vs AI",
    "👥 Human vs Human (Local)",
    "🤝 AI vs AI",
]

# Per-mode state keys that get stashed on mode switch
_MODE_STATE_KEYS = (
    "engine", "messages", "msg_counter", "battle_over",
    "current_turn", "history", "blitz_enabled", "turn_start_time",
    "hints_used_recent", "last_hint",
    "detected_premise", "attach_premise", "spell_typos",
    "tikz_export_text",
    "aivai_running", "aivai_topic", "aivai_max_turns",
)


def _stash_state_for_mode(mode_name: str) -> None:
    stash = {}
    for k in _MODE_STATE_KEYS:
        if k in st.session_state:
            stash[k] = st.session_state[k]
            del st.session_state[k]
    if stash:
        st.session_state[f"_stash::{mode_name}"] = stash


def _restore_state_for_mode(mode_name: str) -> None:
    stash_key = f"_stash::{mode_name}"
    stash = st.session_state.get(stash_key, {})
    for k, v in stash.items():
        st.session_state[k] = v
    if stash_key in st.session_state:
        del st.session_state[stash_key]


def _switch_mode(old_mode: str, new_mode: str) -> None:
    if old_mode:
        _stash_state_for_mode(old_mode)
    _restore_state_for_mode(new_mode)
    st.session_state.mode = new_mode


# =========================================================== Routing

st.sidebar.title("⚖️ Logic Advocate Tutor")
st.sidebar.caption("Display and mode selection")

if "mode" not in st.session_state:
    st.session_state.mode = MODES[0]
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

# Light/Dark toggle. The Light theme uses the BRIGHT_THEME_CSS overrides
# in views/_styles.py; if any element looks off in Light mode, the rules
# to tweak live in that file.
theme_label = st.sidebar.radio(
    "Display Mode:",
    ["🌙 Dark", "☀️ Light"],
    index=0 if st.session_state.theme_mode == "Dark" else 1,
)
theme_choice = "Dark" if theme_label.startswith("🌙") else "Bright"
if theme_choice != st.session_state.theme_mode:
    st.session_state.theme_mode = theme_choice
    st.rerun()

st.sidebar.markdown("---")
chosen = st.sidebar.radio(
    "Select Game Mode:",
    MODES,
    index=MODES.index(st.session_state.mode)
          if st.session_state.mode in MODES else 0,
)

if chosen != st.session_state.mode:
    _switch_mode(st.session_state.mode, chosen)
    st.rerun()

if chosen == "🤝 AI vs AI":
    render_ai_vs_ai()
else:
    render_local_debate()
