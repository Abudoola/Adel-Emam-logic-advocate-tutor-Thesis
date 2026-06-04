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

TOPIC_SUGGESTIONS = (
    "Schools should ban smartphones in classrooms",
    "AI tutors should be allowed to grade student essays",
    "Public transport should be free in large cities",
    "Social media platforms should verify all users",
    "Universities should replace exams with projects",
    "Governments should tax sugary drinks",
    "Remote work is better than office work",
    "Nuclear power should be expanded",
    "Fast fashion should be heavily regulated",
    "Students should be allowed to use AI tools in homework",
)


def _next_topic_suggestion() -> str:
    idx = st.session_state.get("aivai_topic_suggestion_idx", -1) + 1
    st.session_state.aivai_topic_suggestion_idx = idx
    return TOPIC_SUGGESTIONS[idx % len(TOPIC_SUGGESTIONS)]


def _use_topic_suggestion() -> None:
    suggestion = st.session_state.get("aivai_topic_placeholder", "")
    st.session_state.aivai_topic = suggestion
    st.session_state.aivai_topic_input = suggestion


def _get_clients():
    """
    Returns ((client_a, model_a, provider_a), (client_b, model_b, provider_b))
    Side A uses GROQ_API_KEY. Side B uses AIVAI_API_KEY (with OpenRouter support).
    provider_x is a short label ("Groq", "OpenRouter", or "Groq (fallback)").
    """
    client_a, model_a, prov_a = None, None, None
    client_b, model_b, prov_b = None, None, None

    try:
        key_a = st.secrets.get("GROQ_API_KEY")
        if key_a:
            client_a = Groq(api_key=key_a)
            model_a  = "llama-3.3-70b-versatile"
            prov_a   = "Groq"
    except Exception:
        pass

    try:
        key_b = st.secrets.get("AIVAI_API_KEY")
        if key_b:
            if key_b.startswith("sk-or"):
                http_client = httpx.Client(transport=OpenRouterTransport(httpx.HTTPTransport()))
                client_b = Groq(api_key=key_b, base_url="https://openrouter.ai/api/v1", http_client=http_client)
                model_b  = "meta-llama/llama-3.3-70b-instruct"
                prov_b   = "OpenRouter"
            else:
                client_b = Groq(api_key=key_b)
                model_b  = "llama-3.3-70b-versatile"
                prov_b   = "Groq (AIVAI key)"
        else:
            client_b, model_b = client_a, model_a
            prov_b = (prov_a or "Groq") + " (fallback)"
    except Exception:
        client_b, model_b = client_a, model_a
        prov_b = (prov_a or "Groq") + " (fallback)"

    if not client_a and not client_b:
        st.error("No API keys configured. Add GROQ_API_KEY to .streamlit/secrets.toml.")
        return None, None

    if not client_a:
        client_a, model_a, prov_a = client_b, model_b, (prov_b or "Groq") + " (fallback)"
    if not client_b:
        client_b, model_b, prov_b = client_a, model_a, (prov_a or "Groq") + " (fallback)"

    return (client_a, model_a, prov_a), (client_b, model_b, prov_b)


# ---- pretty short model names for display ----
_MODEL_DISPLAY = {
    "llama-3.3-70b-versatile":          "LLaMA 3.3 70B",
    "meta-llama/llama-3.3-70b-instruct": "LLaMA 3.3 70B Instruct",
}

def _provider_color(provider: str) -> str:
    if "OpenRouter" in provider:
        return "#5865F2"
    if "fallback" in provider.lower():
        return "#6c757d"
    return "#28a745"

def _provider_badge(provider: str, model: str) -> str:
    """Small HTML chip showing provider + short model name."""
    short = _MODEL_DISPLAY.get(model, model)
    bg, fg = _provider_color(provider), "white"
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:10px;font-size:11px;font-weight:600;'
            f'white-space:nowrap;">{provider} · {short}</span>')


_SIDE_PROMPT = """You are {role} in a structured debate.

The proposition is: "{topic}"
You ARGUE {stance} the proposition.

GROUND RULES:
- Each turn you must pick an Action: ATTACK or SUPPORT.
    ATTACK  = refute the OPPONENT'S argument. TargetID must be one of
              the opponent's previous Msg IDs (you can see them in the
              transcript below).
    SUPPORT = add a new reason, evidence or clarification that
              REINFORCES YOUR OWN previous argument. TargetID must be
              one of YOUR OWN previous Msg IDs.
              SUPPORT is only valid if you have at least one previous
              move on your side. Do NOT use SUPPORT to agree with the
              opponent.
- Vary your moves. A debate of only attacks is shallower than one in
  which each side also strengthens its own case from new angles.
- Personal experience from your opponent counts as valid evidence.
- Score honestly. Do not flatter yourself.
- Stay focused on the proposition. Do not pick at typos or phrasing.
- Pick a ValueTag from: Logic, Fact, Ethics, Emotion. Pick the tag that
  best fits the nature of your argument.

STYLE:
- Chatty, conversational. As long or short as the point needs.
- Plain English. Direct. Not stiff.

{available_targets_block}
Debate so far:
{transcript}

It is your turn ({role}). Write your move.

CRITICAL OUTPUT FORMAT:
Output EXACTLY ONE LINE. No preamble. No quotes. No explanation.
The single line MUST be:

   OpponentScore|YourScore|ValueTag|Action|TargetID|YourArgument

Action MUST be exactly Attack or Support (capitalised).
TargetID MUST be an existing Msg_N from the debate (or "None" only on
the very first move when there is nothing yet to target).

Examples:
   15|17|Logic|Attack|Msg_2|That is a real point, but it falls apart at scale because the costs do not shrink with the user base.
   0|20|Fact|Support|Msg_1|Adding to my earlier point: the WHO 2022 report puts the figure at 30 percent, which is consistent with the trend I described.
   0|0|Logic|Attack|None|CONCEDE

Output now."""


# AI-vs-AI specific 6-field pipe parser. The prompt asks for
# OpponentScore|YourScore|ValueTag|Action|TargetID|YourArgument
# We can't use _parse_counter_response from ai_agent.py because it only
# reads four fields and would silently drop Action and TargetID.
import re as _re
_AIVAI_PIPE_RE = _re.compile(
    r"(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*"
    r"(Logic|Fact|Ethics|Emotion)\s*\|\s*"
    r"(Attack|Support|ATTACK|SUPPORT)\s*\|\s*"
    r"(Msg_\d+|None|none|-)\s*\|\s*"
    r"([^\n]+)",
    _re.IGNORECASE,
)

def _parse_aivai_response(text):
    """Returns the dict shape that _run_one_turn expects:
        llm_weight, human_weight, llm_val, llm_text, llm_action, llm_target, parsed.
    Falls back to the legacy 4-field parser (assumed Attack) when the
    LLM omits the Action/TargetID fields.
    """
    matches = _AIVAI_PIPE_RE.findall(text)
    if matches:
        hw_s, aw_s, tag, act_raw, tgt_raw, txt = matches[-1]
        act = act_raw.capitalize()  # "Attack" or "Support"
        txt = txt.strip().strip("'").strip('"')
        # CONCEDE handling (LLM emits CONCEDE either as the argument text
        # or via the 0|0|... convention).
        if "CONCEDE" in txt.upper():
            return {"human_weight": 0, "llm_weight": 0,
                    "llm_val": "Logic", "llm_text": "CONCEDE",
                    "llm_action": "Attack", "llm_target": None,
                    "parsed": True}
        tgt = None if tgt_raw.lower() in ("none", "-") else tgt_raw
        return {"human_weight": max(1, min(25, int(hw_s))),
                "llm_weight":   max(1, min(25, int(aw_s))),
                "llm_val":      tag.capitalize(),
                "llm_text":     txt,
                "llm_action":   act,
                "llm_target":   tgt,
                "parsed":       True}
    # Fallback: maybe the LLM emitted the legacy 4-field format. Use
    # the original parser and default Action to Attack with no explicit
    # target (the cross-side validation in _run_one_turn will pick one).
    legacy = _parse_counter_response(text)
    legacy["llm_action"] = "Attack"
    legacy["llm_target"] = None
    return legacy


def _build_available_targets_block(messages, role):
    """List the Msg IDs the LLM is allowed to point at:
       Attack-targets = opponent's previous moves;
       Support-targets = own previous moves.
    """
    own_ids = [m["id"] for m in messages if m["side"] == role]
    opp_ids = [m["id"] for m in messages if m["side"] != role]
    own_str = ", ".join(own_ids) if own_ids else "(none yet)"
    opp_str = ", ".join(opp_ids) if opp_ids else "(none yet)"
    return (
        "AVAILABLE TARGET IDs:\n"
        f"  Attack (must target one of the OPPONENT'S moves): {opp_str}\n"
        f"  Support (must target one of YOUR OWN moves):     {own_str}\n"
    )


def _generate_move(client, model, role, topic, stance, transcript_text,
                   messages=None):
    """Ask one side to produce its next move."""
    targets_block = _build_available_targets_block(messages or [], role)
    prompt = _SIDE_PROMPT.format(
        role=role, topic=topic, stance=stance, transcript=transcript_text,
        available_targets_block=targets_block,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    raw = response.choices[0].message.content.strip()
    return _parse_aivai_response(raw)


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
              "aivai_running", "aivai_topic", "aivai_topic_input",
              "aivai_topic_placeholder"]:
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
        client, model, _prov = clients_info[0]
    else:
        client, model, _prov = clients_info[1]

    try:
        parsed = _generate_move(
            client, model, cur_side, st.session_state.aivai_topic,
            stance, transcript_text,
            messages=st.session_state.messages,
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
            "provider":  _prov,
            "model":     model,
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

    # Process Action & Target with cross-side validation
    valid_ids = list(st.session_state.engine.nodes.keys())
    target_id = parsed.get("llm_target")
    action = parsed.get("llm_action", "Attack")

    # Build per-side ID sets
    own_ids = {m["id"] for m in st.session_state.messages if m["side"] == cur_side}
    opp_ids = {m["id"] for m in st.session_state.messages if m["side"] != cur_side}

    if action == "Support":
        if target_id in own_ids and target_id in valid_ids:
            pass  # valid
        elif own_ids & set(valid_ids):
            # Fallback: support own most-recent node
            target_id = next(m["id"] for m in reversed(st.session_state.messages)
                             if m["side"] == cur_side and m["id"] in valid_ids)
        else:
            # No own nodes — switch to attack
            action = "Attack"
            target_id = next((m["id"] for m in reversed(st.session_state.messages)
                              if m["side"] != cur_side), None)
    else:  # Attack
        if target_id in opp_ids and target_id in valid_ids:
            pass  # valid
        elif target_id in valid_ids:
            pass  # allow attacking any valid node as fallback
        else:
            target_id = next((m["id"] for m in reversed(st.session_state.messages)
                              if m["side"] != cur_side), None)

    st.session_state.engine.add_argument(mid, text, weight, tag)
    if target_id:
        if action == "Support":
            st.session_state.engine.add_support(mid, target_id)
        else:
            st.session_state.engine.add_direct_attack(mid, target_id)
            
    st.session_state.messages.append({
        "id":        mid,
        "content":   text,
        "side":      cur_side,
        "provider":  _prov,
        "model":     model,
        "target":    target_id,
        "action":    action,
        "weight":    weight,
        "value_tag": tag,
    })
    st.session_state.msg_counter += 1
    return True


def render_ai_vs_ai() -> None:
    inject_css()
    _init_state()

    st.title("🤝 AI vs AI Debate")

    # ---- detect providers once for header display ----
    clients_info = _get_clients()
    if clients_info != (None, None):
        (_, model_a, prov_a), (_, model_b, prov_b) = clients_info
    else:
        prov_a = prov_b = "—"
        model_a = model_b = "—"

    st.caption(
        "Two agents will argue against each other. "
        "Side A uses your Groq key, and Side B uses your AIVAI key (Groq or OpenRouter)."
    )

    # ---- provider banner ----
    st.markdown(
        f'<div style="display:flex;gap:12px;align-items:center;'
        f'margin:4px 0 12px 0;flex-wrap:wrap;">'
        f'<span style="color:#999;font-size:12px;">Configured agents:</span>'
        f'<span><b>🟢 Side A:</b>&nbsp;{_provider_badge(prov_a, model_a)}</span>'
        f'<span style="color:#666;">vs</span>'
        f'<span><b>🔵 Side B:</b>&nbsp;{_provider_badge(prov_b, model_b)}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---------- Setup form ----------
    if not st.session_state.messages and not st.session_state.aivai_running:
        if "aivai_topic_placeholder" not in st.session_state:
            st.session_state.aivai_topic_placeholder = _next_topic_suggestion()
        c1, c_suggest, c2, c3 = st.columns([3, 0.8, 1, 1])
        with c1:
            topic = st.text_input(
                "Debate topic (Starter argues FOR, Other argues AGAINST):",
                value=st.session_state.aivai_topic,
                placeholder=st.session_state.aivai_topic_placeholder,
                key="aivai_topic_input",
            )
        with c_suggest:
            st.write("")
            st.button(
                "Use suggestion",
                use_container_width=True,
                on_click=_use_topic_suggestion,
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
                options=[f"Side A ({prov_a})", f"Side B ({prov_b})"],
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
                # remember providers for later display
                st.session_state.aivai_prov_a    = prov_a
                st.session_state.aivai_prov_b    = prov_b
                st.session_state.aivai_model_a   = model_a
                st.session_state.aivai_model_b   = model_b
                st.rerun()
        return

    # ---------- Active debate ----------
    st.session_state.engine.evaluate_semantics()
    engine = st.session_state.engine

    # Pull providers locked in when the debate started.
    saved_prov_a = st.session_state.get("aivai_prov_a", prov_a)
    saved_prov_b = st.session_state.get("aivai_prov_b", prov_b)

    st.markdown(f"**Topic:** {st.session_state.aivai_topic}")
    if engine.nodes:
        c1, c2, c3 = st.columns(3)
        main_status = engine.statuses.get("Msg_1", "OUT")
        surviving = "* SURVIVING" if main_status == "IN" else "* DEFEATED"
        color = "#28a745" if main_status == "IN" else "#dc3545"
        starter = st.session_state.get("aivai_starter", "Side A")
        other   = "Side B" if starter == "Side A" else "Side A"
        starter_prov = saved_prov_a if starter == "Side A" else saved_prov_b
        other_prov   = saved_prov_b if starter == "Side A" else saved_prov_a
        with c1:
            st.markdown(
                f'<div class="stat-card"><b>{starter} claim ({starter_prov})</b><br>'
                f'<span style="color:{color};">{surviving}</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            if main_status == "IN":
                winner = f"{starter} - {starter_prov} (For)"
            else:
                winner = f"{other} - {other_prov} (Against)"
            st.markdown(
                f'<div class="stat-card"><b>Currently Ahead</b><br>'
                f'<span style="color:#ffaa00;">{winner}</span></div>',
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
        st.markdown(
            f'<div style="display:flex;gap:14px;font-size:12px;'
            f'margin:2px 0 6px 0;">'
            f'<span><b style="color:{_provider_color(saved_prov_a)};">'
            f'Side A</b> &mdash; {saved_prov_a}</span>'
            f'<span style="color:#666;">|</span>'
            f'<span><b style="color:{_provider_color(saved_prov_b)};">'
            f'Side B</b> &mdash; {saved_prov_b}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Live Debate Momentum")
        render_momentum_bar(st.session_state.messages, engine.statuses, engine.nodes)

    st.divider()

    # ---- Side-by-side: chat history (left) + live logic map (right) ----
    chat_col, map_col = st.columns([3, 2], gap="medium")
    with chat_col:
        chat_container = st.container(height=600)
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
    with map_col:
        map_container = st.container(height=600)
        with map_container:
            st.markdown("##### Live Logic Map")
            st.caption(
                "Solid red = attack | dashed blue = support | "
                "green node = Groq | blue node = OpenRouter | "
                "IN/OUT is written inside each node"
            )
            if engine.nodes:
                st.graphviz_chart(
                    render_logic_graph(engine, st.session_state.messages),
                    use_container_width=True,
                )
            else:
                st.caption("The map appears once arguments are added.")

    if "aivai_full_chat_open" not in st.session_state:
        st.session_state.aivai_full_chat_open = False
    label = "Close full chat" if st.session_state.aivai_full_chat_open else "Open full chat"
    if st.button(label, use_container_width=True):
        st.session_state.aivai_full_chat_open = not st.session_state.aivai_full_chat_open
        st.rerun()
    if st.session_state.aivai_full_chat_open:
        with st.container(border=True):
            st.markdown("##### Full Chat")
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
        st.success("Debate concluded.")
        if st.button("Start New Debate", type="primary",
                     use_container_width=True):
            _reset_debate()
            st.rerun()
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.session_state.aivai_running:
                if st.button("Pause", use_container_width=True):
                    st.session_state.aivai_running = False
                    st.rerun()
            else:
                if st.button("Resume", use_container_width=True,
                             type="primary"):
                    st.session_state.aivai_running = True
                    st.rerun()
        with c2:
            if st.button("Step (next move)", use_container_width=True):
                made = _run_one_turn()
                if made:
                    st.rerun()
        with c3:
            if st.button("End Debate", use_container_width=True):
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
