"""
views/ai_vs_ai.py
-----------------
AI vs AI debate view. Two LLaMA-3 agents argue against each other,
both constrained by the same engine that runs Human-vs-AI mode.

The Groq client prefers AIVAI_API_KEY from .streamlit/secrets.toml
(so tournament runs do not burn through the main Human-vs-AI key's
rate limit). Falls back to GROQ_API_KEY if AIVAI_API_KEY is missing.
"""
from __future__ import annotations
import os
import time

import streamlit as st
import httpx
from groq import Groq

class OpenRouterTransport(httpx.BaseTransport):
    def __init__(self, transport):
        self.transport = transport
    def handle_request(self, request):
        if '/openai/v1/chat/completions' in str(request.url):
            request.url = request.url.copy_with(path='/api/v1/chat/completions')
        return self.transport.handle_request(request)

from logic_engine import AcademicLogicEngine, VALID_VALUE_TAGS
from ai_agent import TEXT_MODEL, _build_transcript, _parse_counter_response
from views._styles import (
    inject_css, render_argument_bubble, render_momentum_bar,
    render_logic_graph,
)
from views.engine_inspector import render_inspector_panel


def _get_clients():
    """
    Returns ((client_a, model_a), (client_b, model_b))
    Side A uses GROQ_API_KEY. Side B uses AIVAI_API_KEY (with OpenRouter support).
    """
    client_a, model_a = None, None
    client_b, model_b = None, None
    
    try:
        key_a = st.secrets.get("GROQ_API_KEY")
        if key_a:
            client_a = Groq(api_key=key_a)
            model_a = "llama-3.3-70b-versatile"
    except Exception:
        pass

    try:
        key_b = st.secrets.get("AIVAI_API_KEY")
        if key_b:
            if key_b.startswith("sk-or"):
                http_client = httpx.Client(transport=OpenRouterTransport(httpx.HTTPTransport()))
                client_b = Groq(api_key=key_b, base_url="https://openrouter.ai/api/v1", http_client=http_client)
                model_b = "meta-llama/llama-3.3-70b-instruct"
            else:
                client_b = Groq(api_key=key_b)
                model_b = "llama-3.3-70b-versatile"
        else:
            client_b, model_b = client_a, model_a
    except Exception:
        client_b, model_b = client_a, model_a

    if not client_a and not client_b:
        st.error("No API keys configured. Add GROQ_API_KEY to .streamlit/secrets.toml.")
        return None, None

    if not client_a:
        client_a, model_a = client_b, model_b
    if not client_b:
        client_b, model_b = client_a, model_a

    return (client_a, model_a), (client_b, model_b)


_SIDE_PROMPT = """You are {role} in a structured debate.

The proposition is: "{topic}"
You ARGUE {stance} the proposition.

GROUND RULES:
- Engage with the OTHER SIDE'S latest move. Counter-attack their reasoning.
- Personal experience from your opponent counts as valid evidence.
- Score honestly. Do not flatter yourself.
- Stay focused on the proposition. Do not pick at typos or phrasing.
- Pick a ValueTag from: Logic, Fact, Ethics, Emotion. Choose the tag that best fits the nature of your argument based on the conversation.

STYLE:
- Chatty, conversational. As long or short as the point needs.
- Plain English. Direct. Not stiff.

Debate so far:
{transcript}

It is your turn ({role}). Write your move.

CRITICAL OUTPUT FORMAT:
Output EXACTLY ONE LINE. No preamble. No quotes. No explanation.
The single line MUST be:

   OpponentScore|YourScore|ValueTag|YourArgument

Example: 15|17|Logic|That is a real point, but it falls apart at scale because the costs do not shrink with the user base.

Output now."""


def _generate_move(client, model, role, topic, stance, transcript_text):
    """Ask one side to produce its next move."""
    prompt = _SIDE_PROMPT.format(
        role=role, topic=topic, stance=stance, transcript=transcript_text,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()
    return _parse_counter_response(raw)


def _init_state():
    if "engine" not in st.session_state:
        st.session_state.engine          = AcademicLogicEngine()
    if "messages" not in st.session_state:
        st.session_state.messages        = []
    if "msg_counter" not in st.session_state:
        st.session_state.msg_counter     = 1
    if "battle_over" not in st.session_state:
        st.session_state.battle_over     = False
    if "aivai_running" not in st.session_state:
        st.session_state.aivai_running   = False
    if "aivai_topic" not in st.session_state:
        st.session_state.aivai_topic     = ""
    if "aivai_max_turns" not in st.session_state:
        st.session_state.aivai_max_turns = 8
    if "aivai_starter" not in st.session_state:
        st.session_state.aivai_starter   = "Side A"


def _reset_debate():
    for k in ["engine", "messages", "msg_counter", "battle_over",
              "aivai_running"]:
        if k in st.session_state:
            del st.session_state[k]


def _run_one_turn():
    """Generate the next move. Returns True if a move was made."""
    if st.session_state.battle_over:
        return False
    if len(st.session_state.messages) >= st.session_state.aivai_max_turns:
        st.session_state.battle_over = True
        st.session_state.aivai_running = False
        return False

    clients_info = _get_clients()
    if clients_info == (None, None):
        st.session_state.aivai_running = False
        return False

    transcript_text = _build_transcript(st.session_state.messages)
    starter = st.session_state.get("aivai_starter", "Side A")
    if not st.session_state.messages:
        cur_side = starter
        stance = "FOR"
    else:
        last_side = st.session_state.messages[-1]["side"]
        cur_side  = "Side B" if last_side == "Side A" else "Side A"
        stance    = "FOR" if cur_side == starter else "AGAINST"

    if cur_side == "Side A":
        client, model = clients_info[0]
    else:
        client, model = clients_info[1]

    try:
        parsed = _generate_move(
            client, model, cur_side, st.session_state.aivai_topic,
            stance, transcript_text,
        )
    except Exception as e:
        st.error(f"Generation error: {e}")
        st.session_state.aivai_running = False
        return False

    if parsed["llm_text"] == "CONCEDE":
        st.toast(f"🏳️ {cur_side} has conceded.")
        st.session_state.messages.append({
            "id":        "Concession",
            "content":   f"{cur_side} has no further counter. The other side wins.",
            "side":      cur_side,
            "target":    None,
            "action":    "Support",
            "weight":    0,
            "value_tag": "Logic",
        })
        st.session_state.battle_over   = True
        st.session_state.aivai_running = False
        return False

    mid    = f"Msg_{st.session_state.msg_counter}"
    weight = parsed["llm_weight"]
    text   = parsed["llm_text"]
    tag    = parsed["llm_val"]

    target_id = None
    if st.session_state.messages:
        target_id = next(
            (m["id"] for m in reversed(st.session_state.messages)
             if m["side"] != cur_side),
            None,
        )

    st.session_state.engine.add_argument(mid, text, weight, tag)
    if target_id:
        st.session_state.engine.add_direct_attack(mid, target_id)
    st.session_state.messages.append({
        "id":        mid,
        "content":   text,
        "side":      cur_side,
        "target":    target_id,
        "action":    "Attack",
        "weight":    weight,
        "value_tag": tag,
    })
    st.session_state.msg_counter += 1
    return True


def render_ai_vs_ai() -> None:
    inject_css()
    _init_state()

    st.title("🤝 AI vs AI Debate")

    st.caption(
        "Two agents will argue against each other. "
        "Side A uses your Groq key, and Side B uses your AIVAI key (Groq or OpenRouter)."
    )

    # ---------- Setup form ----------
    if not st.session_state.messages and not st.session_state.aivai_running:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            topic = st.text_input(
                "Debate topic (Starter argues FOR, Other argues AGAINST):",
                value=st.session_state.aivai_topic or
                       "Schools should ban smartphones in classrooms",
                key="aivai_topic_input",
            )
        with c2:
            max_turns = st.number_input(
                "Max turns",
                min_value=2, max_value=20,
                value=st.session_state.aivai_max_turns,
                step=2, key="aivai_max_turns_input",
            )
        with c3:
            starter_choice = st.selectbox(
                "Starting API:",
                options=["Side A (Groq)", "Side B (OpenRouter)"],
                index=0 if st.session_state.get("aivai_starter", "Side A") == "Side A" else 1,
            )
        if st.button("🚀 Run Debate", type="primary", use_container_width=True):
            if not topic.strip():
                st.warning("Enter a topic first.")
            else:
                st.session_state.aivai_topic     = topic.strip()
                st.session_state.aivai_max_turns = int(max_turns)
                st.session_state.aivai_starter   = "Side A" if "Side A" in starter_choice else "Side B"
                st.session_state.aivai_running   = True
                st.rerun()
        return

    # ---------- Active debate ----------
    st.session_state.engine.evaluate_semantics()
    engine = st.session_state.engine

    st.markdown(f"**Topic:** {st.session_state.aivai_topic}")
    if engine.nodes:
        c1, c2, c3 = st.columns(3)
        main_status = engine.statuses.get("Msg_1", "OUT")
        surviving = "● SURVIVING" if main_status == "IN" else "● DEFEATED"
        color = "#28a745" if main_status == "IN" else "#dc3545"
        starter = st.session_state.get("aivai_starter", "Side A")
        other   = "Side B" if starter == "Side A" else "Side A"
        with c1:
            st.markdown(
                f'<div class="stat-card"><b>{starter} claim</b><br>'
                f'<span style="color:{color};">{surviving}</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            winner = f"{starter} (For)" if main_status == "IN" else f"{other} (Against)"
            st.markdown(
                f'<div class="stat-card"><b>Currently Ahead</b><br>'
                f'<span style="color:#ffaa00;">🥇 {winner}</span></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="stat-card"><b>Moves played</b><br>'
                f'<span>{len(st.session_state.messages)} / '
                f'{st.session_state.aivai_max_turns}</span></div>',
                unsafe_allow_html=True,
            )
        st.write("")
        st.markdown("### 📊 Live Debate Momentum")
        render_momentum_bar(st.session_state.messages, engine.statuses, engine.nodes)
        with st.expander("🗺️ View Interactive Logic Map", expanded=False):
            st.graphviz_chart(render_logic_graph(engine, st.session_state.messages))

    st.divider()

    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.messages:
            engine_score = engine.scores.get(msg["id"], 1.0)
            is_concession = (msg.get("id") == "Concession")
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

    st.divider()

    if st.session_state.battle_over:
        st.success("🏁 Debate concluded.")
        if st.button("🔄 Start New Debate", type="primary",
                      use_container_width=True):
            _reset_debate()
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.session_state.aivai_running:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.aivai_running = False
                    st.rerun()
            else:
                if st.button("▶️ Resume", use_container_width=True,
                              type="primary"):
                    st.session_state.aivai_running = True
                    st.rerun()
        with c2:
            if st.button("⏭️ Step (next move)", use_container_width=True):
                made = _run_one_turn()
                if made:
                    st.rerun()
        with c3:
            if st.button("🚨 End Debate", use_container_width=True):
                st.session_state.battle_over = True
                st.session_state.aivai_running = False
                st.rerun()

        if st.session_state.aivai_running:
            time.sleep(0.3)
            made = _run_one_turn()
            if made:
                st.rerun()

    if engine.nodes:
        render_inspector_panel(
            engine=engine,
            messages=st.session_state.messages,
            learner_side=st.session_state.get("aivai_starter", "Side A"),
            recent_hints=0,
        )
