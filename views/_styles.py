"""
views/_styles.py
----------------
Targeted CSS for the Logic Advocate Tutor.

ALL rules in this file target ONLY our own custom classes:
  .proponent-bubble, .opponent-bubble, .concession-bubble
  .hint-card, .hint-strategy, .hint-body, .hint-debug
  .stat-card, .victory-box, .turn-indicator
  .inspector-card, .badge-neural, .badge-symbolic

We deliberately NEVER style Streamlit's native widgets (.stButton,
.stTextInput, .stSelectbox, .stRadio, etc.). The colour palette is
set in .streamlit/config.toml using Streamlit's official theme API.
That way the composer, dropdowns, buttons and sidebar can never get
broken by our CSS.
"""
import streamlit as st

CHAT_CSS = """
<style>
/* =================================== Chat bubbles (cloud) ============ */

.proponent-bubble,
.opponent-bubble {
    color: white;
    padding: 14px 20px;
    margin-bottom: 12px;
    font-size: 14.5px;
    line-height: 1.5;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.proponent-bubble {
    background: linear-gradient(135deg, #5865F2, #4752C4);
    border-radius: 22px 22px 6px 22px;
    margin-left: 18%;
    margin-right: 4%;
    box-shadow: 0 4px 14px rgba(88, 101, 242, 0.30),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.opponent-bubble {
    background: linear-gradient(135deg, #F23F42, #C13438);
    border-radius: 22px 22px 22px 6px;
    margin-right: 18%;
    margin-left: 4%;
    box-shadow: 0 4px 14px rgba(242, 63, 66, 0.30),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.proponent-bubble b,
.opponent-bubble b {
    display: block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    opacity: 0.85;
    margin-bottom: 6px;
}
.concession-bubble {
    background: linear-gradient(135deg, #248046, #1A5C32);
    color: white;
    border-radius: 16px;
    padding: 16px 22px;
    margin: 14px 12%;
    font-size: 14px;
    font-weight: 600;
    text-align: center;
    border: 1px solid #248046;
    box-shadow: 0 4px 16px rgba(36, 128, 70, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
    letter-spacing: 0.3px;
}

/* =================================== Status cards ==================== */

.stat-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    color: rgba(220, 222, 225, 0.85);
}
.stat-card b {
    display: block;
    color: rgba(220, 222, 225, 0.55);
    text-transform: uppercase;
    font-size: 10px;
    letter-spacing: 0.7px;
    font-weight: 700;
    margin-bottom: 4px;
}
.stat-card span {
    font-size: 16px;
    font-weight: 600;
}

/* =================================== Victory banner ================== */

.victory-box {
    padding: 24px;
    border-radius: 14px;
    text-align: center;
    margin-top: 16px;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
}

/* =================================== Turn indicator ================== */

.turn-indicator {
    text-align: center;
    padding: 10px 16px;
    border-radius: 10px;
    margin-bottom: 12px;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.7px;
    text-transform: uppercase;
}

/* =================================== Hint / premise cards ============ */

.hint-card {
    background: rgba(88, 101, 242, 0.10);
    border: 1px solid rgba(88, 101, 242, 0.30);
    border-left: 4px solid #5865F2;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 10px 0;
    color: rgba(220, 222, 225, 0.95);
}
.hint-strategy {
    display: inline-block;
    background: #5865F2;
    color: white;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.9px;
    margin-bottom: 10px;
    text-transform: uppercase;
}
.hint-body {
    font-size: 14.5px;
    line-height: 1.5;
}
.hint-debug {
    font-size: 11px;
    opacity: 0.55;
    margin-top: 8px;
    font-family: monospace;
}

/* =================================== Inspector panel ================= */

.inspector-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-family: monospace;
    font-size: 12.5px;
}
.inspector-neural   { border-left: 4px solid #F23F42; }
.inspector-symbolic { border-left: 4px solid #F0B232; }
.badge-neural {
    background: #F23F42;
    color: white;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    margin-right: 8px;
    text-transform: uppercase;
}
.badge-symbolic {
    background: #F0B232;
    color: #14213D;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
    margin-right: 8px;
    text-transform: uppercase;
}
</style>
"""


def inject_css() -> None:
    st.markdown(CHAT_CSS, unsafe_allow_html=True)


# ============================================================ Render helpers

def render_argument_bubble(mid, content, side, weight, action, target,
                            value_tag="Logic", score=1.0,
                            is_concession=False) -> None:
    """Render a single chat bubble."""
    if is_concession:
        st.markdown(
            f'<div class="concession-bubble">🏳️ {content}</div>',
            unsafe_allow_html=True,
        )
        return

    side_class = "proponent-bubble" if side == "Side A" else "opponent-bubble"
    score_pct = int(score * 100)
    st.markdown(
        f'<div class="{side_class}">'
        f'<b>{mid} · {value_tag}</b>{content}'
        f'</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns([1, 1])
    with cols[0]:
        if target and target != "None":
            rel_icon = "⚔️ Attacks" if action == "Attack" else "🛡️ Supports"
            st.caption(f"{rel_icon} {target}")
    with cols[1]:
        st.caption(f"Acceptability: {score_pct}% · Weight: {weight}")


def render_momentum_bar(messages, statuses, nodes) -> None:
    """Discord-style thin momentum bar with side labels above."""
    a_score = sum(
        nodes[m["id"]]["weight"]
        for m in messages
        if statuses.get(m["id"]) == "IN" and m["side"] == "Side A"
    )
    b_score = sum(
        nodes[m["id"]]["weight"]
        for m in messages
        if statuses.get(m["id"]) == "IN" and m["side"] == "Side B"
    )
    total = a_score + b_score
    a_pct, b_pct = (a_score / total * 100, b_score / total * 100) if total > 0 else (50, 50)
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between;
                font-size:11px; opacity:0.7;
                text-transform:uppercase; letter-spacing:0.6px;
                font-weight:600; margin-bottom:4px;">
        <span style="color:#5865F2;">Side A · {a_score} pts</span>
        <span style="color:#F23F42;">{b_score} pts · Side B</span>
    </div>
    <div style="width:100%; height:12px; border-radius:6px;
                display:flex; overflow:hidden;
                background:rgba(255,255,255,0.06);
                border:1px solid rgba(255,255,255,0.08);
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);">
        <div style="width:{a_pct}%; background:linear-gradient(90deg, #5865F2, #4752C4);
                    transition:width 0.4s;"></div>
        <div style="width:{b_pct}%; background:linear-gradient(90deg, #C13438, #F23F42);
                    transition:width 0.4s;"></div>
    </div>
    """, unsafe_allow_html=True)


def render_logic_graph(engine, messages):
    """Graphviz output tuned to the dark theme."""
    import graphviz
    graph = graphviz.Digraph()
    graph.attr(rankdir="TB", bgcolor="transparent")

    for mid, ndata in engine.nodes.items():
        score = engine.scores.get(mid, 1.0)
        score_pct = int(score * 100)
        val_tag = ndata.get("value_tag", "Logic")
        # Red -> yellow -> green ramp
        r = int(255 * (1.0 - score))
        g = int(200 * score)
        fill = f"#{r:02x}{g:02x}44"
        label = f"{mid}\n[{val_tag}]\n{score_pct}%"
        graph.node(mid, label, style="filled",
                   fillcolor=fill, fontcolor="white", fontsize="10",
                   color="#3F4147")

    for m in messages:
        tgt = m.get("target")
        if tgt and tgt != "None":
            is_attack = (m.get("action") == "Attack")
            ecol  = "#F23F42" if is_attack else "#5865F2"
            elabel = "⚔" if is_attack else "🛡"
            graph.edge(m["id"], tgt, color=ecol, label=elabel,
                       fontcolor=ecol, fontsize="9")
    return graph
