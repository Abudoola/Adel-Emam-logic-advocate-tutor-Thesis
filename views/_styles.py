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

/* =================================== Composer ======================== */

[data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="base-input"] {
    min-height: 92px !important;
    height: 92px !important;
    border-radius: 14px !important;
    align-items: center !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] input {
    min-height: 92px !important;
    height: 92px !important;
    font-size: 18px !important;
    line-height: 1.4 !important;
    padding: 0 18px !important;
}

[data-testid="stForm"] [data-testid="stButton"] button {
    min-height: 50px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
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

BRIGHT_THEME_CSS = """
<style>
:root {
    --lat-page: #F6F7FB;
    --lat-panel: #FFFFFF;
    --lat-panel-soft: #EEF1F7;
    --lat-border: rgba(20, 33, 61, 0.14);
    --lat-text: #1F2937;
    --lat-muted: #5B6472;
}

.stApp {
    background: var(--lat-page);
    color: var(--lat-text);
}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
    background: #FFFFFF;
    color: var(--lat-text);
}

[data-testid="stHeader"] {
    background: rgba(246, 247, 251, 0.82);
}

[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
h1, h2, h3, h4, h5, h6 {
    color: var(--lat-text);
}

[data-testid="stCaptionContainer"] {
    color: var(--lat-muted);
}

[data-testid="stSelectbox"] label,
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stFileUploader"] label,
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    color: var(--lat-text);
}

[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stTextInput"] div[data-baseweb="base-input"],
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #FFFFFF;
    border-color: var(--lat-border);
    color: var(--lat-text);
}

[data-testid="stTextInput"] input {
    caret-color: var(--lat-text);
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #7A8494;
    opacity: 1;
}

[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
.stButton > button,
.stDownloadButton > button {
    background: #FFFFFF;
    border: 1px solid var(--lat-border);
    color: var(--lat-text);
    box-shadow: 0 1px 4px rgba(20, 33, 61, 0.05);
}

[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #5865F2;
    color: #1F2937;
}

[data-testid="stButton"] button[kind="primary"],
[data-testid="stDownloadButton"] button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: #5865F2;
    border-color: #5865F2;
    color: #FFFFFF;
}

[data-testid="stButton"] button:disabled,
[data-testid="stDownloadButton"] button:disabled,
.stButton > button:disabled,
.stDownloadButton > button:disabled,
button[data-testid^="baseButton"]:disabled {
    background: #EEF1F7;
    border-color: var(--lat-border);
    color: #7A8494;
    opacity: 1;
}

[data-testid="stButton"] button:disabled *,
[data-testid="stDownloadButton"] button:disabled *,
.stButton > button:disabled *,
.stDownloadButton > button:disabled * {
    color: #7A8494;
    opacity: 1;
}

[data-testid="stSelectbox"] svg,
[data-testid="stTextInput"] svg,
[data-testid="stTextArea"] svg,
[data-testid="stButton"] svg {
    color: currentColor;
    fill: currentColor;
}

.stat-card {
    background: var(--lat-panel);
    border: 1px solid var(--lat-border);
    color: var(--lat-text);
    box-shadow: 0 2px 10px rgba(20, 33, 61, 0.06);
}
.stat-card b {
    color: var(--lat-muted);
}

.hint-card {
    background: #F3F6FF;
    border-color: rgba(88, 101, 242, 0.24);
    color: var(--lat-text);
}
.hint-body {
    color: var(--lat-text);
}
.hint-debug {
    color: var(--lat-muted);
    opacity: 1;
}

.inspector-card {
    background: var(--lat-panel);
    border-color: var(--lat-border);
    color: var(--lat-text);
}

.turn-indicator {
    background: var(--lat-panel);
}

.victory-box {
    box-shadow: 0 4px 18px rgba(20, 33, 61, 0.12);
}
</style>
"""

DARK_THEME_CSS = """
<style>
.stApp {
    background: #1E1F22;
}
</style>
"""


def inject_css() -> None:
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    theme = st.session_state.get("theme_mode", "Dark")
    st.markdown(
        BRIGHT_THEME_CSS if theme == "Bright" else DARK_THEME_CSS,
        unsafe_allow_html=True,
    )


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
    """Graphviz output tuned for a tall, narrow SIDE PANEL.

    The map is intended to render in a column roughly 35-40% of the page
    width, alongside the chat. Aspect ratio is therefore narrow + tall.
    """
    import graphviz
    graph = graphviz.Digraph()
    # No `size`/`ratio` cap: let the graph render at its natural height so
    # the host container can grow with the debate. Streamlit's
    # `use_container_width=True` still scales the SVG to fit the column
    # width. Tight nodesep/ranksep keep the layout compact.
    graph.attr(rankdir="TB", bgcolor="transparent",
               nodesep="0.12",
               ranksep="0.22",
               margin="0.04", pad="0.04",
               fontname="Helvetica")
    # Defaults so every node uses the same compact rounded-box shape.
    graph.attr("node", shape="box", style="rounded,filled",
               fontname="Helvetica", fontsize="10",
               fontcolor="white", color="#3F4147",
               margin="0.08,0.04", penwidth="2.5")
    graph.attr("edge", fontname="Helvetica", fontsize="9",
               penwidth="1.6", arrowsize="0.6")

    # Per-message lookups for side/provider colour and premise marking.
    side_map = {}
    provider_map = {}
    premise_set = set()
    for m in messages:
        side_map[m["id"]] = m.get("side", "")
        provider_map[m["id"]] = m.get("provider", "")
        if m.get("is_premise"):
            premise_set.add(m["id"])

    provider_graph = any(provider_map.values())
    if not provider_graph:
        graph.attr(size="2.4,3.4!", ratio="compress")
        graph.attr("node", fontsize="6", margin="0.04,0.025", penwidth="1.2")
        graph.attr("edge", fontsize="6", penwidth="1.0", arrowsize="0.4")

    for mid, ndata in engine.nodes.items():
        score = engine.scores.get(mid, 1.0)
        score_pct = int(round(score * 100))
        val_tag = ndata.get("value_tag", "Logic")
        status  = engine.statuses.get(mid, "OUT")

        # Fill: muted red <-> muted forest-green gradient by score.
        # Interpolate in straight RGB. Endpoints are picked for contrast
        # with white text and to avoid the harsh lime / fire-engine look
        # of the earlier palette.
        if status == "IN":
            # Vivid emerald palette that reads well on the dark UI.
            # score 0.50 (borderline IN) -> soft mint (#66BB6A) - paler
            # score 1.00 (strongly IN)   -> rich emerald (#16A34A) - saturated
            t = max(0.0, min(1.0, (score - 0.5) * 2))
            r_c = int(round(102 + ( 22 - 102) * t))   # 102 -> 22
            g_c = int(round(187 + (163 - 187) * t))   # 187 -> 163
            b_c = int(round(106 + ( 74 - 106) * t))   # 106 -> 74
            fill = f"#{r_c:02x}{g_c:02x}{b_c:02x}"
            status_mark = "IN"
        else:
            # score 0.50 (borderline OUT) -> muted brick red
            # score 0.00 (strongly OUT)   -> deep crimson
            t = max(0.0, min(1.0, (0.5 - score) * 2))
            r_c = int(round(176 + (183 - 176) * t))   # 176 -> 183
            g_c = int(round( 88 + ( 28 -  88) * t))   #  88 -> 28
            b_c = int(round( 88 + ( 28 -  88) * t))   #  88 -> 28
            fill = f"#{r_c:02x}{g_c:02x}{b_c:02x}"
            status_mark = "OUT"

        side = side_map.get(mid, "")
        provider = provider_map.get(mid, "")

        if provider:
            if "OpenRouter" in provider:
                border_color = "#5865F2"
                fill = "#5865F2"
                owner_label = "OR"
            elif "fallback" in provider.lower():
                border_color = "#6c757d"
                fill = "#6c757d"
                owner_label = "FB"
            else:
                border_color = "#28a745"
                fill = "#16A34A"
                owner_label = "Groq"
        elif side == "Side A":
            border_color = "#F59E0B"   # amber
            owner_label = "A"
        elif side == "Side B":
            border_color = "#A855F7"   # purple
            owner_label = "B"
        else:
            border_color = "#9CA3AF"   # neutral grey
            owner_label = "-"

        premise_mark = " *" if mid in premise_set else ""
        label = f"{mid} [{owner_label}{premise_mark}]\n{status} {val_tag} {score_pct}%"
        graph.node(mid, label, fillcolor=fill, color=border_color)

    for m in messages:
        tgt = m.get("target")
        if tgt and tgt != "None":
            is_attack = (m.get("action") == "Attack")
            if is_attack:
                ecol  = "#F23F42"
                elabel = "atk"
                style = "solid"
            else:
                ecol  = "#5865F2"
                elabel = "sup"
                style = "dashed"
            graph.edge(m["id"], tgt, color=ecol, label=elabel,
                       fontcolor=ecol, style=style)
    return graph
