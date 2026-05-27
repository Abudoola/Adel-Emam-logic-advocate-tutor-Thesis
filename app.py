"""
app.py
------
Entry point for the Logic Advocate Tutor Streamlit app.

Routes:
  * URL has ?room_id=...        -> online player/spectator view
  * Mode = "🌐 Online Debate"   -> online host dashboard
  * Mode = "🤝 AI vs AI"        -> self-play tournament view
  * Otherwise                   -> single-machine debate (HvAI / HvH)

Mode changes preserve each mode's debate state under a per-mode stash
so you can flip back and forth without losing anything.
"""
import os
import streamlit as st

from views.local_debate import render_local_debate
from views.mobile_multiplayer import render_mobile_host, render_mobile_player
from views.ai_vs_ai import render_ai_vs_ai

st.set_page_config(page_title="Logic Advocate Arena", layout="wide")

os.makedirs("uploads", exist_ok=True)

MODES = [
    "🤖 Human vs AI",
    "👥 Human vs Human (Local)",
    "🤝 AI vs AI",
    "🌐 Online Debate",
]

# Keys whose values are part of a debate's state and should be stashed
# per-mode when the user switches modes (so going back restores them).
_MODE_STATE_KEYS = (
    "engine", "messages", "msg_counter", "battle_over",
    "current_turn", "history", "blitz_enabled", "turn_start_time",
    "hints_used_recent", "last_hint",
    "detected_premise", "attach_premise", "spell_typos",
    "tikz_export_text",
    # AI-vs-AI specific
    "aivai_running", "aivai_topic", "aivai_max_turns",
)


def _stash_state_for_mode(mode_name: str) -> None:
    """Move per-mode keys into a per-mode dict so they can be restored later."""
    stash = {}
    for k in _MODE_STATE_KEYS:
        if k in st.session_state:
            stash[k] = st.session_state[k]
            del st.session_state[k]
    if stash:
        st.session_state[f"_stash::{mode_name}"] = stash


def _restore_state_for_mode(mode_name: str) -> None:
    """Restore any previously stashed per-mode keys."""
    stash_key = f"_stash::{mode_name}"
    stash = st.session_state.get(stash_key, {})
    for k, v in stash.items():
        st.session_state[k] = v
    if stash_key in st.session_state:
        del st.session_state[stash_key]


def _switch_mode(old_mode: str, new_mode: str) -> None:
    """Save the current mode's state, restore the new mode's state."""
    if old_mode:
        _stash_state_for_mode(old_mode)
    _restore_state_for_mode(new_mode)
    st.session_state.mode = new_mode


# =========================================================== Routing

query_params = st.query_params
room_id = query_params.get("room_id")
role    = query_params.get("role")

if room_id:
    render_mobile_player(room_id, role)
else:
    st.sidebar.title("⚖️ Logic Advocate Tutor")
    st.sidebar.caption("Mode selection")

    if st.sidebar.button("⬅️ Close Sidebar", use_container_width=True):
        st.components.v1.html(
            """
            <script>
            const btn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]');
            if (btn) {
                btn.click();
            }
            </script>
            """,
            height=0,
        )

    if "mode" not in st.session_state:
        st.session_state.mode = MODES[0]

    chosen = st.sidebar.radio(
        "Select Game Mode:",
        MODES,
        index=MODES.index(st.session_state.mode)
              if st.session_state.mode in MODES else 0,
    )

    if chosen != st.session_state.mode:
        _switch_mode(st.session_state.mode, chosen)
        st.rerun()

    if chosen == "🌐 Online Debate":
        render_mobile_host()
    elif chosen == "🤝 AI vs AI":
        render_ai_vs_ai()
    else:
        render_local_debate()
