"""
views/local_debate.py
---------------------
Single-machine view for Human-vs-AI and Human-vs-Human (Local) modes.

This file is intentionally thinner than the original. The math lives
in logic_engine, the LLM calls live in ai_agent, the MDP lives in
hint_mdp, the shared CSS/widgets live in views/_styles, and the
Defense Mode panel lives in views/engine_inspector.
"""
from __future__ import annotations
import json
import os
import time

import streamlit as st

from logic_engine import AcademicLogicEngine, VALID_VALUE_TAGS
from ai_agent import (
    generate_counter_argument,
    generate_hint_v2,
    transcribe_audio,
    detect_implicit_premise,
)
from views._styles import (
    inject_css,
    render_argument_bubble,
    render_momentum_bar,
    render_logic_graph,
)
from views.engine_inspector import render_inspector_panel


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "unified_battle_history.json",
)


# ============================================================ INITIALISATION

def _init_session_state() -> None:
    """Set up everything we need in st.session_state on first run."""
    if "engine" in st.session_state:
        return

    st.session_state.engine            = AcademicLogicEngine()
    st.session_state.messages          = []
    st.session_state.msg_counter       = 1
    st.session_state.battle_over       = False
    st.session_state.current_turn      = "Side A"
    st.session_state.history           = []
    st.session_state.blitz_enabled     = False
    st.session_state.turn_start_time   = time.time()
    st.session_state.hints_used_recent = 0
    st.session_state.last_hint         = None
    st.session_state.detected_premise  = None   # implicit premise card state
    st.session_state.attach_premise    = False  # whether to add it on submit
    st.session_state.spell_typos       = None   # typo list from last check
    st.session_state.widget_interaction = False

def _record_interaction() -> None:
    st.session_state.widget_interaction = True


# =================================================================== SAVE/LOAD

def _save_battle() -> None:
    history = []
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append({
        "mode":     st.session_state.mode,
        "messages": st.session_state.messages,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    with open(DB_PATH, "w") as f:
        json.dump(history, f, indent=2)
    st.toast("✅ Battle saved")


def _load_battle(idx: int) -> None:
    """Load a previously saved battle by index (offset from history list)."""
    try:
        with open(DB_PATH, "r") as f:
            history_data = json.load(f)
    except Exception:
        return
    if idx >= len(history_data):
        return
    saved = history_data[idx]
    msgs = saved["messages"]
    st.session_state.messages = msgs
    st.session_state.engine   = AcademicLogicEngine.rebuild_from_messages(msgs)
    st.session_state.mode     = saved.get("mode", st.session_state.mode)
    st.session_state.msg_counter = max(
        (int(m["id"].split("_")[1]) for m in msgs if m["id"].startswith("Msg_")),
        default=0,
    ) + 1
    st.session_state.battle_over = True


# ============================================================ UNDO

def _undo_last_move() -> None:
    """
    Pop the most recent move(s) off the engine and the chat.

    In Human-vs-AI mode the AI's reply is paired with the user's move, so
    we pop BOTH the AI's last reply and the user's preceding move (the AI
    only spoke because the user did). In Human-vs-Human or AI-vs-AI mode
    we pop just one move.
    """
    msgs = st.session_state.messages
    if not msgs:
        st.toast("Nothing to undo.")
        return

    # How many moves to pop?
    is_hvai = (st.session_state.mode == "🤖 Human vs AI")
    n_pop = 1
    if is_hvai and len(msgs) >= 2:
        last_two = msgs[-2:]
        if last_two[0]["side"] == "Side A" and last_two[1]["side"] == "Side B":
            n_pop = 2
        elif msgs[-1].get("id") == "Concession" and len(msgs) >= 2:
            # Concession after a user move: pop both
            n_pop = 2

    popped = msgs[-n_pop:]
    st.session_state.messages = msgs[:-n_pop]

    # Rebuild the engine from the truncated message list
    st.session_state.engine = AcademicLogicEngine.rebuild_from_messages(
        st.session_state.messages
    )
    # Roll the counter back to the highest remaining Msg_X id + 1
    remaining = [
        int(m["id"].split("_")[1]) for m in st.session_state.messages
        if m["id"].startswith("Msg_")
    ]
    st.session_state.msg_counter = (max(remaining) + 1) if remaining else 1

    # Re-open the debate if the popped moves included the concession or
    # a manual end. Otherwise stay in whatever state we were in.
    if any(p.get("id") == "Concession" for p in popped):
        st.session_state.battle_over = False
    if st.session_state.battle_over and st.session_state.messages:
        st.session_state.battle_over = False

    # Clear stale UI state
    st.session_state.detected_premise = None
    st.session_state.attach_premise = False
    st.session_state.spell_typos = None
    st.session_state.last_hint = None

    st.toast(f"↩️ Undid {n_pop} move{'s' if n_pop > 1 else ''}.")


# ============================================================ ANALYSIS HELPERS

def _compute_trajectory(messages):
    """
    Replay every move and record the engine state after each one.
    Returns a list of dicts with main_score, statuses, side weights.
    """
    trajectory = []
    engine = AcademicLogicEngine()
    for i, m in enumerate(messages):
        if m.get("id") == "Concession":
            continue
        engine.add_argument(m["id"], m["content"], m.get("weight", 5),
                             m.get("value_tag", "Logic"))
        tgt = m.get("target")
        if tgt and tgt != "None":
            if m.get("action") == "Attack":
                engine.add_direct_attack(m["id"], tgt)
            else:
                engine.add_support(m["id"], tgt)
        engine.evaluate_semantics()

        a_weight = sum(
            engine.nodes[mm["id"]]["weight"] for mm in messages[:i + 1]
            if mm["id"] in engine.nodes
            and engine.statuses.get(mm["id"]) == "IN"
            and mm["side"] == "Side A"
        )
        b_weight = sum(
            engine.nodes[mm["id"]]["weight"] for mm in messages[:i + 1]
            if mm["id"] in engine.nodes
            and engine.statuses.get(mm["id"]) == "IN"
            and mm["side"] == "Side B"
        )
        trajectory.append({
            "turn":         i + 1,
            "move_id":      m["id"],
            "side":         m["side"],
            "value_tag":    m.get("value_tag", "Logic"),
            "main_score":   round(engine.scores.get("Msg_1", 1.0), 3),
            "main_status":  engine.statuses.get("Msg_1", "IN"),
            "side_a_weight": a_weight,
            "side_b_weight": b_weight,
        })
    return trajectory


def _find_turning_point(trajectory):
    """
    Return the turn index where the Main Claim's status FLIPPED for the
    last time (the move that decided the final verdict). Returns None
    if no flip occurred.
    """
    if len(trajectory) < 2:
        return None
    final_status = trajectory[-1]["main_status"]
    for i in range(len(trajectory) - 1, 0, -1):
        if trajectory[i]["main_status"] != trajectory[i - 1]["main_status"]:
            return i
    return None


def _value_tag_breakdown(messages):
    """Count value tags per side."""
    counts = {"Side A": {}, "Side B": {}}
    for m in messages:
        if m.get("id") == "Concession":
            continue
        side = m.get("side")
        tag  = m.get("value_tag", "Logic")
        if side in counts:
            counts[side][tag] = counts[side].get(tag, 0) + 1
    return counts


# ============================================================ TOP DASHBOARD

def _render_top_dashboard() -> None:
    engine = st.session_state.engine

    existing_ids = list(engine.nodes.keys())
    if not existing_ids:
        return

    # Three small status cards
    c1, c2, c3 = st.columns(3)
    main_status = engine.statuses.get("Msg_1", "OUT")
    surviving   = "● SURVIVING" if main_status == "IN" else "● DEFEATED"
    color       = "#28a745" if main_status == "IN" else "#dc3545"
    with c1:
        st.markdown(
            f'<div class="stat-card"><b>Main Claim</b><br>'
            f'<span style="color:{color};">{surviving}</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        winner = "Side A (Pro)" if main_status == "IN" else "Side B (Opp)"
        st.markdown(
            f'<div class="stat-card"><b>Currently Ahead</b><br>'
            f'<span style="color:#ffaa00;">🥇 {winner}</span></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-card"><b>Graph Size</b><br>'
            f'<span>{len(existing_ids)} nodes</span></div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # Momentum bar + End Debate inline
    bar_col, end_col = st.columns([5, 1])
    with bar_col:
        st.markdown("### 📊 Live Debate Momentum")
        render_momentum_bar(st.session_state.messages, engine.statuses, engine.nodes)
    with end_col:
        st.write("")  # vertical breathing room
        if not st.session_state.battle_over:
            if st.button("🚨 End Debate", use_container_width=True,
                          key="end_debate_topbar"):
                st.session_state.battle_over = True
                st.rerun()

    # Logic map (expandable)
    with st.expander("🗺️ View Interactive Logic Map", expanded=False):
        st.graphviz_chart(render_logic_graph(engine, st.session_state.messages))


# ============================================================ CHAT HISTORY

def _render_chat_history() -> None:
    container = st.container(height=400)
    with container:
        for msg in st.session_state.messages:
            engine_score = st.session_state.engine.scores.get(msg["id"], 1.0)
            is_concession = (msg.get("id") == "Concession")

            with st.container():
                render_argument_bubble(
                    mid=msg["id"],
                    content=msg["content"],
                    side=msg["side"],
                    weight=msg.get("weight", 0),
                    action=msg.get("action", ""),
                    target=msg.get("target"),
                    value_tag=msg.get("value_tag", "Logic"),
                    score=engine_score,
                    is_concession=is_concession,
                )

                # Display attached media if any
                if msg.get("media_path") and os.path.exists(msg["media_path"]):
                    if msg["media_type"].startswith("image"):
                        st.image(msg["media_path"], width=200)
                    elif msg["media_type"].startswith("video"):
                        st.video(msg["media_path"])

            st.write("")


# ============================================================ INPUT BAR

def _render_move_controls(active_side: str):
    """Render the action/target/value-tag selectors. Returns a tuple."""
    engine = st.session_state.engine
    my_msgs    = {m["id"]: m["content"] for m in st.session_state.messages
                  if m["side"] == active_side}
    enemy_msgs = {m["id"]: m["content"] for m in st.session_state.messages
                  if m["side"] != active_side}

    if not engine.nodes:
        st.info(f"🟢 {active_side} goes first. Post your Main Claim.")
        value_tag = st.selectbox("Value Tag:", VALID_VALUE_TAGS, key="val_first", on_change=_record_interaction)
        return ("Main Claim", "None", "Attack", value_tag, enemy_msgs)

    turn_idx = st.session_state.msg_counter
    col_act, col_tgt, col_val = st.columns([1, 1.5, 1])
    with col_act:
        action_choice = st.radio(
            "Move:", ["⚔️ Attack", "🛡️ Support"],
            horizontal=True, key=f"action_d_{turn_idx}", on_change=_record_interaction
        )
    with col_tgt:
        if action_choice == "⚔️ Attack":
            if enemy_msgs:
                target = st.selectbox(
                    "Target:", list(enemy_msgs.keys()),
                    index=len(enemy_msgs) - 1,
                    format_func=lambda x: f"[{x}] {enemy_msgs[x]}",
                    key=f"target_enemy_d_{turn_idx}", on_change=_record_interaction
                )
                action = "Attack"
            else:
                st.warning("No enemy arguments to attack yet.")
                target, action = "None", "Attack"
        else:
            if my_msgs:
                target = st.selectbox(
                    "Target:", list(my_msgs.keys()),
                    index=len(my_msgs) - 1,
                    format_func=lambda x: f"[{x}] {my_msgs[x]}",
                    key=f"target_self_d_{turn_idx}", on_change=_record_interaction
                )
                action = "Support"
            else:
                st.warning("You have no arguments to support.")
                target, action = "None", "Support"
    with col_val:
        value_tag = st.selectbox(
            "Value Tag:", VALID_VALUE_TAGS, key=f"val_d_{turn_idx}", on_change=_record_interaction
        )

    return (action_choice, target, action, value_tag, enemy_msgs)


def _render_premise_button(active_side: str, turn_key) -> None:
    """
    Implicit-premise detector (operationalises Ku et al. 2025).

    Reads whatever the user has currently typed into the composer,
    asks the LLM to identify the unstated assumption their argument
    relies on, and offers to attach it as a supporting node when the
    user submits.
    """
    cols = st.columns([1, 4])
    with cols[0]:
        clicked = st.button("🔍 Check assumptions", use_container_width=True,
                            key=f"check_assumptions_{turn_key}", on_click=_record_interaction)

    if clicked:
        # Pull the current draft text out of the composer's session state
        draft_key = f"desktop_text_{turn_key}"
        draft = st.session_state.get(draft_key, "").strip()
        if not draft:
            st.warning("Type something first, then I can check it.")
        else:
            # Use the last few moves as context if available
            recent = st.session_state.messages[-4:] if st.session_state.messages else None
            with st.spinner("Looking for an unstated premise..."):
                result = detect_implicit_premise(draft, recent_messages=recent)
            st.session_state.detected_premise = result
            st.session_state.attach_premise = False  # default off until user opts in

    # Render the most recent detection if any
    dp = st.session_state.detected_premise
    if dp is None:
        return

    if not dp["found"]:
        st.markdown(
            f'<div class="hint-card" style="border-left-color:#9aa0a6;">'
            f'<div class="hint-strategy" style="background:#5f6368;">'
            f'IMPLICIT PREMISE · NONE FOUND</div>'
            f'<div class="hint-body">{dp["justification"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    conf_pct = int(dp["confidence"] * 100)
    st.markdown(
        f'<div class="hint-card" style="border-left-color:#ffb74d;">'
        f'<div class="hint-strategy" style="background:#ef6c00;">'
        f'IMPLICIT PREMISE · CONFIDENCE {conf_pct}%</div>'
        f'<div class="hint-body"><b>You are assuming:</b> '
        f'“{dp["premise"]}”</div>'
        f'<div class="hint-debug">Why: {dp["justification"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Checkbox to attach this as a supporting node on submit
    st.session_state.attach_premise = st.checkbox(
        "Add this premise as a SUPPORT to my argument when I submit",
        value=st.session_state.attach_premise,
        key=f"attach_premise_{turn_key}",
        help=(
            "When checked, your move will create two nodes: your main "
            "argument plus this premise as a supporter of it. This makes "
            "your reasoning logically explicit in the engine."
        ),
        on_change=_record_interaction
    )


def _render_spellcheck_button(active_side: str, turn_key) -> None:
    """
    Pre-submission spell check.

    Reads the draft text in the composer, scans for likely typos with
    pyspellchecker (offline), and offers a one-click 'fix all' that
    replaces typos with the top suggestion before the argument enters
    the engine. The chat bubble and TikZ export will then show clean
    text instead of the verbatim typo.
    """
    import spellcheck

    cols = st.columns([1, 4])
    with cols[0]:
        clicked = st.button("🔤 Check spelling", use_container_width=True,
                            key=f"check_spelling_{turn_key}",
                            disabled=not spellcheck.is_available(),
                            help=(
                                "Offline spell check via pyspellchecker. "
                                "Install with: pip install pyspellchecker"
                            ), on_click=_record_interaction)

    if clicked:
        draft_key = f"desktop_text_{turn_key}"
        draft = st.session_state.get(draft_key, "").strip()
        if not draft:
            st.warning("Type something first, then I can check it.")
        else:
            typos = spellcheck.find_typos(draft)
            st.session_state.spell_typos = typos
            st.session_state.spell_checked_text = draft

    typos = st.session_state.get("spell_typos")
    if typos is None:
        return

    if not typos:
        st.markdown(
            '<div class="hint-card" style="border-left-color:#4caf50;">'
            '<div class="hint-strategy" style="background:#2e7d32;">'
            'SPELLING · CLEAN</div>'
            '<div class="hint-body">No likely typos detected. Good to '
            'submit.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    n = len(typos)
    word_count = sum(1 for _ in typos)
    st.markdown(
        f'<div class="hint-card" style="border-left-color:#ff9800;">'
        f'<div class="hint-strategy" style="background:#e65100;">'
        f'SPELLING · {n} POSSIBLE TYPO{"S" if n != 1 else ""}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    for i, t in enumerate(typos):
        sugs = t["suggestions"] or ["(no suggestion)"]
        st.markdown(
            f"  • **{t['word']}** → "
            f"{', '.join(f'`{s}`' for s in sugs[:3])}"
        )

    have_suggestions = any(t["suggestions"] for t in typos)
    c_fix, c_ignore = st.columns(2)
    with c_fix:
        if st.button("✅ Fix all (use top suggestion)",
                     use_container_width=True,
                     type="primary",
                     disabled=not have_suggestions,
                     key=f"fix_spell_{turn_key}", on_click=_record_interaction):
            draft_key = f"desktop_text_{turn_key}"
            corrections = {
                t["word"]: t["suggestions"][0]
                for t in typos if t["suggestions"]
            }
            current = st.session_state.get(draft_key, "")
            fixed = spellcheck.apply_corrections(current, corrections)
            st.session_state[draft_key] = fixed
            st.session_state.spell_typos = None
            st.toast(f"✅ Replaced {len(corrections)} typo"
                     f"{'s' if len(corrections) != 1 else ''}")
            st.rerun()
    with c_ignore:
        if st.button("Ignore and continue", use_container_width=True,
                     key=f"ignore_spell_{turn_key}", on_click=_record_interaction):
            st.session_state.spell_typos = None
            st.rerun()


def _render_hint_button(active_side: str, enemy_msgs) -> None:
    """The MDP-guided hint button."""
    if not enemy_msgs:
        return

    cols = st.columns([1, 4])
    with cols[0]:
        clicked = st.button("💡 Get Hint", use_container_width=True, on_click=_record_interaction)

    if clicked:
        own_msgs = [m for m in st.session_state.messages
                    if m["side"] == active_side]
        own_main_claim = own_msgs[0]["content"] if own_msgs else ""
        last_enemy_msg = list(enemy_msgs.values())[-1]

        with st.spinner("Strategising..."):
            result = generate_hint_v2(
                engine=st.session_state.engine,
                messages=st.session_state.messages,
                learner_side=active_side,
                recent_hints=st.session_state.hints_used_recent,
                enemy_argument=last_enemy_msg,
                own_main_claim=own_main_claim,
            )
        st.session_state.last_hint = result
        st.session_state.hints_used_recent += 1

    # Always render the most recent hint if present (does not disappear on rerun)
    h = st.session_state.last_hint
    if h:
        st.markdown(
            f'<div class="hint-card">'
            f'<div class="hint-strategy">STRATEGY · {h["action"]}</div>'
            f'<div class="hint-body">{h["hint"]}</div>'
            f'<div class="hint-debug">MDP state: {h["state"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _render_composer(turn_key):
    """The WhatsApp-style composer at the bottom. Returns (text_input, audio_file, uploaded_file, submitted)."""
    uploaded_file, audio_file = None, None
    col_attach, col_input, col_send = st.columns([0.6, 8, 0.8])
    with col_attach:
        with st.popover("➕", use_container_width=True):
            uploaded_file = st.file_uploader(
                "📎 Attach evidence",
                type=["png", "jpg", "jpeg", "mp4"],
                key=f"local_file_{turn_key}",
                on_change=_record_interaction
            )
            if hasattr(st, "audio_input"):
                audio_file = st.audio_input(
                    "🎤 Record voice", key=f"local_audio_{turn_key}", on_change=_record_interaction
                )
            elif hasattr(st, "experimental_audio_input"):
                audio_file = st.experimental_audio_input(
                    "🎤 Record voice", key=f"local_audio_{turn_key}", on_change=_record_interaction
                )
    with col_input:
        text_input = st.text_input(
            "msg", placeholder="Type a message",
            key=f"desktop_text_{turn_key}", label_visibility="collapsed",
        )
    with col_send:
        submitted = st.button(
            "➡️", use_container_width=True, type="primary", key="desktop_submit",
        )

    # Enter-to-send works natively: Streamlit reruns the script when the
    # user hits Enter inside a text_input.
    # However, to prevent premature submission when users click other buttons
    # or change options (blur events), we only auto-submit if no other widget
    # was interacted with.
    interacted = st.session_state.get("widget_interaction", False)
    if not submitted and text_input and text_input.strip() and not interacted:
        submitted = True

    # Reset interaction flag for the next event
    st.session_state.widget_interaction = False

    return text_input, audio_file, uploaded_file, submitted


# ============================================================ TURN PROCESSING

def _process_move(text, value_tag, target, action, active_side,
                  uploaded_file, saved_media_path, media_type):
    """Add a new argument to the engine and (in HvAI mode) ask the AI to respond."""
    mid = f"Msg_{st.session_state.msg_counter}"
    weight = min(25, len(text.split()) + 5)

    engine = st.session_state.engine
    engine.add_argument(mid, text, weight, value_tag)
    if target != "None":
        if action == "Attack":
            engine.add_direct_attack(mid, target)
        else:
            engine.add_support(mid, target)

    msg_data = {
        "id":        mid,
        "content":   text,
        "side":      active_side,
        "target":    target if target != "None" else None,
        "action":    action,
        "weight":    weight,
        "value_tag": value_tag,
    }
    if saved_media_path:
        msg_data["media_path"] = saved_media_path
        msg_data["media_type"] = media_type

    st.session_state.messages.append(msg_data)
    st.session_state.msg_counter += 1

    # ----- Implicit-premise attachment ---------------------------------
    # If the user clicked "Check assumptions" and ticked the checkbox,
    # also insert the detected premise as a SUPPORTING node for the
    # argument they just submitted. This makes the implicit reasoning
    # explicit in the engine, addressing the Ku et al. (2025) gap.
    dp = st.session_state.detected_premise
    if dp and dp.get("found") and st.session_state.attach_premise:
        premise_mid = f"Msg_{st.session_state.msg_counter}"
        premise_text = dp["premise"]
        premise_weight = min(25, len(premise_text.split()) + 5)
        engine.add_argument(premise_mid, premise_text, premise_weight, "Logic")
        engine.add_support(premise_mid, mid)
        st.session_state.messages.append({
            "id":         premise_mid,
            "content":    f"[implicit premise] {premise_text}",
            "side":       active_side,
            "target":     mid,
            "action":     "Support",
            "weight":     premise_weight,
            "value_tag":  "Logic",
            "is_premise": True,
        })
        st.session_state.msg_counter += 1
        st.toast(f"🔍 Premise added: {premise_text[:60]}...")
    # Reset premise detector state for the next turn
    st.session_state.detected_premise = None
    st.session_state.attach_premise   = False

    st.session_state.hints_used_recent = 0   # reset the hint streak
    st.session_state.last_hint = None        # clear the previous hint
    st.session_state.turn_start_time = time.time()

    # Branch on mode
    if st.session_state.mode == "🤖 Human vs AI":
        _ai_turn(text, uploaded_file, saved_media_path, media_type, mid)
    elif st.session_state.mode == "👥 Human vs Human (Local)":
        st.session_state.current_turn = "Side B" if st.session_state.current_turn == "Side A" else "Side A"

    st.rerun()


def _ai_turn(latest_human_text, uploaded_file, saved_media_path,
             media_type, human_mid):
    """Have the AI generate a counter-argument and add it to the engine."""
    placeholder = st.empty()
    for stage_text, stage_delay in [
        ("🧠 Reading your argument...", 0.7),
        ("💭 Thinking of a counter...", 0.8),
        ("✍️ Formulating response...",   0.6),
    ]:
        placeholder.markdown(
            f"<div style='text-align:center; color:#8696a0; font-style:italic; "
            f"padding:10px;'>{stage_text}</div>",
            unsafe_allow_html=True,
        )
        time.sleep(stage_delay)
    placeholder.empty()

    try:
        llm_weight, llm_text, human_weight, llm_val = generate_counter_argument(
            st.session_state.messages,
            latest_human_text,
            uploaded_file,
            saved_media_path,
            media_type,
        )

        # Calibrate human weight based on AI's evaluation
        st.session_state.engine.nodes[human_mid]["weight"] = human_weight
        st.session_state.messages[-1]["weight"] = human_weight

        if llm_text == "CONCEDE":
            st.toast("🏆 The AI has conceded to your logic!")
            st.session_state.messages.append({
                "id":        "Concession",
                "content":   "I have no further counter-arguments. Your logic is sound. You win.",
                "side":      "Side B",
                "target":    human_mid,
                "action":    "Support",
                "weight":    0,
                "value_tag": "Logic",
            })
            st.session_state.battle_over = True
        else:
            llm_mid = f"Msg_{st.session_state.msg_counter}"
            st.session_state.engine.add_argument(llm_mid, llm_text, llm_weight, llm_val)
            st.session_state.engine.add_direct_attack(llm_mid, human_mid)
            st.session_state.messages.append({
                "id":        llm_mid,
                "content":   llm_text,
                "side":      "Side B",
                "target":    human_mid,
                "action":    "Attack",
                "weight":    llm_weight,
                "value_tag": llm_val,
            })
            st.session_state.msg_counter += 1
    except Exception as e:
        st.error(f"The AI encountered an error: {e}")


# ============================================================ SIDEBAR

def _render_sidebar() -> None:
    st.sidebar.markdown("---")
    blitz = st.sidebar.checkbox(
        "⚡ Enable Blitz Mode (60s timer)",
        value=st.session_state.blitz_enabled,
    )
    if blitz != st.session_state.blitz_enabled:
        st.session_state.blitz_enabled = blitz
        st.session_state.turn_start_time = time.time()
        st.rerun()

    if st.sidebar.button("🚨 End Debate Now", use_container_width=True):
        st.session_state.battle_over = True
        st.rerun()

    # Undo last move (pairs the user + AI moves in HvAI mode)
    can_undo = bool(st.session_state.get("messages"))
    if st.sidebar.button(
        "↩️ Undo Last Move",
        use_container_width=True,
        disabled=not can_undo,
        help=("Pops the most recent move off the engine. In Human vs AI mode "
              "this undoes both your move and the AI's reply."),
    ):
        _undo_last_move()
        st.rerun()

    if st.sidebar.button("💾 Save Battle", use_container_width=True):
        _save_battle()

    # TikZ export for thesis figures
    if st.sidebar.button("📐 Export as TikZ", use_container_width=True,
                          help="Generate LaTeX code for the current "
                               "argumentation graph. Paste into your thesis "
                               "as a figure."):
        from tikz_export import export_to_tikz
        st.session_state.tikz_export_text = export_to_tikz(
            st.session_state.engine,
            debate_title=f"{st.session_state.mode[2:]} debate",
            label=f"fig:debate-{int(time.time())}",
            include_text=True,
        )
    if st.session_state.get("tikz_export_text"):
        with st.sidebar.expander("📐 TikZ output (copy this)", expanded=True):
            st.code(st.session_state.tikz_export_text, language="latex")
            if st.button("Clear", key="clear_tikz", use_container_width=True):
                del st.session_state.tikz_export_text
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Previous Debates")
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                history_data = json.load(f)
            if not history_data:
                st.sidebar.info("No saved battles yet.")
            for i, battle in enumerate(reversed(history_data)):
                idx = len(history_data) - 1 - i
                label = f"🗓️ #{len(history_data) - i} · {battle.get('mode', '?')[2:]}"
                if st.sidebar.button(label, key=f"view_hist_{i}",
                                      use_container_width=True):
                    _load_battle(idx)
                    st.rerun()
        except Exception:
            st.sidebar.error("Error loading history.")


# ============================================================ BLITZ TIMER

def _render_blitz_timer() -> None:
    if st.session_state.battle_over or not st.session_state.blitz_enabled:
        return
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1000, limit=None, key="blitz_refresh")
    except ImportError:
        return

    elapsed = int(time.time() - st.session_state.turn_start_time)
    remaining = max(0, 60 - elapsed)
    color = "red" if remaining <= 10 else "black"
    st.markdown(
        f"<h3 style='text-align: center; color: {color};'>"
        f"⏳ Time Remaining: {remaining}s</h3>",
        unsafe_allow_html=True,
    )
    if remaining == 0:
        st.error("⏰ TIME'S UP! Turn forfeited.")
        st.session_state.turn_start_time = time.time()
        time.sleep(2)
        if st.session_state.mode == "👥 Human vs Human (Local)":
            st.session_state.current_turn = (
                "Side B" if st.session_state.current_turn == "Side A" else "Side A"
            )
        else:
            st.session_state.battle_over = True
        st.rerun()


# ============================================================ VICTORY SCREEN

def _render_victory_screen() -> None:
    """
    Rich post-debate analysis screen.

    Shows: the final verdict, score trajectory chart, turning-point move,
    value-tag distribution per side, and the per-node final score table.
    """
    engine = st.session_state.engine
    messages = st.session_state.messages
    main_status = engine.statuses.get("Msg_1", "OUT")

    # ---------- Verdict banner ----------
    st.header("🏁 The Debate Has Concluded!")
    if main_status == "IN":
        st.markdown(
            '<div class="victory-box" style="background-color: rgba(40,167,69,0.2); '
            'border: 2px solid #28a745; color: #28a745;">'
            '🏆 SIDE A emerges victorious!<br>The main claim stands strong.</div>',
            unsafe_allow_html=True,
        )
        st.balloons()
    else:
        st.markdown(
            '<div class="victory-box" style="background-color: rgba(220,53,69,0.2); '
            'border: 2px solid #dc3545; color: #dc3545;">'
            '💥 SIDE B claims victory!<br>The main claim has been shattered.</div>',
            unsafe_allow_html=True,
        )

    if not messages:
        if st.button("🔄 Start New Debate", use_container_width=True, type="primary"):
            _wipe_session_for_new_debate()
            st.rerun()
        return

    st.divider()
    st.subheader("📈 Post-Debate Analysis")

    # ---------- Compute trajectory ----------
    trajectory = _compute_trajectory(messages)

    # ---------- Headline metrics ----------
    final_main_score = trajectory[-1]["main_score"] if trajectory else 1.0
    final_a_weight = trajectory[-1]["side_a_weight"] if trajectory else 0
    final_b_weight = trajectory[-1]["side_b_weight"] if trajectory else 0
    total_moves = len([m for m in messages if m.get("id") != "Concession"])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Main Claim final score", f"{final_main_score:.3f}")
    with c2:
        st.metric("Total moves played", total_moves)
    with c3:
        st.metric("Side A surviving weight", final_a_weight)
    with c4:
        st.metric("Side B surviving weight", final_b_weight)

    # ---------- Score trajectory chart ----------
    if len(trajectory) >= 2:
        st.markdown("**Main Claim score over time** "
                     "(0.5 = the IN/OUT threshold)")
        chart_data = {
            "Turn": [t["turn"] for t in trajectory],
            "Main Claim score": [t["main_score"] for t in trajectory],
            "Threshold": [0.5] * len(trajectory),
        }
        st.line_chart(chart_data, x="Turn", height=220)

        st.markdown("**Side momentum over time** "
                     "(cumulative weight of each side's surviving arguments)")
        momentum_data = {
            "Turn": [t["turn"] for t in trajectory],
            "Side A": [t["side_a_weight"] for t in trajectory],
            "Side B": [t["side_b_weight"] for t in trajectory],
        }
        st.line_chart(momentum_data, x="Turn", height=220)

    # ---------- Turning point ----------
    turn_idx = _find_turning_point(trajectory)
    if turn_idx is not None:
        turning = trajectory[turn_idx]
        st.markdown("**🎯 Turning-point move**")
        st.info(
            f"At turn **{turning['turn']}**, "
            f"**{turning['move_id']}** by **{turning['side']}** "
            f"(value tag: {turning['value_tag']}) flipped the Main Claim's "
            f"status to **{turning['main_status']}**. "
            f"This was the decisive move of the debate."
        )

    # ---------- Value-tag breakdown ----------
    st.markdown("**🏷️ Value-tag distribution per side**")
    tag_counts = _value_tag_breakdown(messages)
    tag_cols = st.columns(2)
    with tag_cols[0]:
        st.markdown(f"**Side A** — {sum(tag_counts['Side A'].values())} moves")
        if tag_counts["Side A"]:
            for tag, n in sorted(tag_counts["Side A"].items(),
                                   key=lambda x: -x[1]):
                st.markdown(f"• {tag}: {n}")
        else:
            st.caption("(no moves)")
    with tag_cols[1]:
        st.markdown(f"**Side B** — {sum(tag_counts['Side B'].values())} moves")
        if tag_counts["Side B"]:
            for tag, n in sorted(tag_counts["Side B"].items(),
                                   key=lambda x: -x[1]):
                st.markdown(f"• {tag}: {n}")
        else:
            st.caption("(no moves)")

    # ---------- Final node scores ----------
    with st.expander("📋 Final per-node scores", expanded=False):
        rows = []
        for mid, n in engine.nodes.items():
            side = next((m["side"] for m in messages if m["id"] == mid), "?")
            rows.append({
                "Node":      mid,
                "Side":      side,
                "Value":     n.get("value_tag", "Logic"),
                "Weight":    n["weight"],
                "Score":     round(engine.scores.get(mid, 1.0), 3),
                "Status":    engine.statuses.get(mid, "OUT"),
                "Text":      n["text"][:60] + ("..." if len(n["text"]) > 60 else ""),
            })
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        if st.button("🔄 Start New Debate", use_container_width=True,
                      type="primary"):
            _wipe_session_for_new_debate()
            st.rerun()
    with cols[1]:
        if st.button("📐 Export this Debate as TikZ", use_container_width=True):
            from tikz_export import export_to_tikz
            st.session_state.tikz_export_text = export_to_tikz(
                st.session_state.engine,
                debate_title=f"{st.session_state.mode[2:]} debate",
                label=f"fig:debate-{int(time.time())}",
                include_text=True,
            )
            st.toast("✅ TikZ exported — see sidebar")


def _wipe_session_for_new_debate() -> None:
    """Reset every per-debate key from session_state."""
    for key in ["engine", "messages", "msg_counter", "battle_over",
                 "current_turn", "history", "turn_start_time",
                 "hints_used_recent", "last_hint",
                 "detected_premise", "attach_premise", "spell_typos"]:
        if key in st.session_state:
            del st.session_state[key]


# ============================================================ ENTRY POINT


def render_local_debate() -> None:
    inject_css()
    _init_session_state()

    st.title(f"⚖️ Logic Advocate: {st.session_state.mode[2:]}")

    # Recompute scores once per render
    st.session_state.engine.evaluate_semantics()

    _render_top_dashboard()
    st.write("")
    _render_chat_history()

    st.divider()

   
    # Blitz timer (no-op if blitz disabled)
    _render_blitz_timer()

    if st.session_state.battle_over:
        _render_victory_screen()
    else:
        # Active side
        if st.session_state.mode == "🤖 Human vs AI":
            active_side = "Side A"
        else:
            active_side = st.session_state.current_turn
            color = "#007bff" if active_side == "Side A" else "#dc3545"
            st.markdown(
                f'<div class="turn-indicator" style="border:2px solid {color}; '
                f'color:{color};">It is currently {active_side}\'s turn</div>',
                unsafe_allow_html=True,
            )

        # Move controls
        action_choice, target, action, value_tag, enemy_msgs = _render_move_controls(active_side)

        # Hint button (MDP-guided)
        _render_hint_button(active_side, enemy_msgs)

        # Composer key (needed early so the premise/spellcheck buttons can read draft text)
        turn_key = st.session_state.msg_counter

        # Implicit premise detector (Ku et al. 2025 operationalised)
        _render_premise_button(active_side, turn_key)

        # Pre-submission spell check
        _render_spellcheck_button(active_side, turn_key)

        st.markdown("---")

        text_input, audio_file, uploaded_file, submitted = _render_composer(turn_key)

        # Build composed text from text + audio
        text = ""
        if submitted and text_input:
            text += text_input + "\n"
        if audio_file is not None:
            try:
                buffer = audio_file.getbuffer()
                if len(buffer) > 100:
                    with st.spinner("Transcribing voice..."):
                        os.makedirs("uploads", exist_ok=True)
                        audio_path = os.path.join("uploads", f"temp_audio_{int(time.time())}.wav")
                        with open(audio_path, "wb") as f:
                            f.write(buffer)
                        transcription = transcribe_audio(audio_path)
                        if transcription:
                            text += transcription
            except Exception as e:
                st.error(f"Voice error: {e}")

        text = text.strip()

        if submitted or audio_file:
            if text or uploaded_file:
                if not text:
                    text = "📎 Attached Media"

                saved_media_path, media_type = None, None
                if uploaded_file:
                    media_type = uploaded_file.type
                    os.makedirs("uploads", exist_ok=True)
                    saved_media_path = os.path.join(
                        "uploads",
                        f"Msg_{st.session_state.msg_counter}_{uploaded_file.name}",
                    )
                    with open(saved_media_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                _process_move(
                    text, value_tag, target, action, active_side,
                    uploaded_file, saved_media_path, media_type,
                )

    # Defense Mode panel (always render, collapsed)
    if st.session_state.engine.nodes:
        active_side_for_inspector = (
            "Side A" if st.session_state.mode == "🤖 Human vs AI"
            else st.session_state.current_turn
        )
        render_inspector_panel(
            engine=st.session_state.engine,
            messages=st.session_state.messages,
            learner_side=active_side_for_inspector,
            recent_hints=st.session_state.hints_used_recent,
        )

    _render_sidebar()
                "Side":      side,
                "Value":     n.get("value_tag", "Logic"),
                "Weight":    n["weight"],
                "Score":     round(engine.scores.get(mid, 1.0), 3),
                "Status":    engine.statuses.get(mid, "OUT"),
                "Text":      n["text"][:60] + ("..." if len(n["text"]) > 60 else ""),
            })
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        if st.button("🔄 Start New Debate", use_container_width=True,
                      type="primary"):
            _wipe_session_for_new_debate()
            st.rerun()
    with cols[1]:
        if st.button("📐 Export this Debate as TikZ", use_container_width=True):
            from tikz_export import export_to_tikz
            st.session_state.tikz_export_text = export_to_tikz(
                st.session_state.engine,
                debate_title=f"{st.session_state.mode[2:]} debate",
                label=f"fig:debate-{int(time.time())}",
                include_text=True,
            )
            st.toast("✅ TikZ exported — see sidebar")


def _wipe_session_for_new_debate() -> None:
    """Reset every per-debate key from session_state."""
    for key in ["engine", "messages", "msg_counter", "battle_over",
                 "current_turn", "history", "turn_start_time",
                 "hints_used_recent", "last_hint",
                 "detected_premise", "attach_premise", "spell_typos"]:
        if key in st.session_state:
            del st.session_state[key]
