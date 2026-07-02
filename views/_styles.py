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
import html
import time

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
.typing-cursor {
    display: inline-block;
    margin-left: 2px;
    opacity: 0.85;
    animation: latBlink 0.8s infinite;
}
@keyframes latBlink {
    0%, 45% { opacity: 1; }
    46%, 100% { opacity: 0; }
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

.chat-composer-panel {
    margin-top: 16px;
}

.lat-thread-header {
    position: sticky;
    top: 0;
    z-index: 30;
    background: #1E1F22;
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
    padding: 22px 0 18px;
    margin-bottom: 16px;
}

.lat-thread-header h1 {
    margin: 0;
    color: #E7E9ED;
    font-size: 42px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: 0;
}

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

[data-testid="stForm"] [data-testid="stTextArea"] textarea {
    min-height: 118px !important;
    font-size: 16px !important;
    line-height: 1.45 !important;
    padding: 14px 16px !important;
    border-radius: 14px !important;
    resize: vertical !important;
}

[data-testid="stForm"] [data-testid="stButton"] button {
    min-height: 50px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}

[data-testid="stTextArea"] textarea {
    min-height: 118px !important;
    font-size: 16px !important;
    line-height: 1.45 !important;
    padding: 16px 18px !important;
    border-radius: 10px !important;
    resize: vertical !important;
}

[data-testid="stButton"] button {
    min-height: 46px !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
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

/* =================================== Codex-style polish (Issue: composer & header) === */

/* Reinforce the thread header sticky behaviour and centre it inside the chat column. */
.lat-thread-header {
    position: sticky;
    top: 0;
    z-index: 50;
    background: rgba(30, 31, 34, 0.92);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 22px 0 18px;
    margin: 0 0 14px 0;
    text-align: center;
}
.lat-thread-header h1 {
    margin: 0;
    color: #E7E9ED;
    font-size: 42px;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: -0.2px;
    text-align: center;
}

/* The composer wrapper. We wrap the existing st.container in a .lat-composer
   div so we can target it without affecting other containers in the chat
   column. */
.lat-composer + div [data-testid="stVerticalBlockBorderWrapper"],
.lat-composer + div [data-testid="stContainer"] {
    border-radius: 22px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(38, 40, 44, 0.92) !important;
    padding: 12px 14px !important;
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.18);
    max-width: 880px;
    margin: 0 auto;
}

/* Pill-shaped textarea inside the composer wrapper. */
.lat-composer + div [data-testid="stTextArea"] textarea {
    min-height: 88px !important;
    background: transparent !important;
    border: none !important;
    border-radius: 14px !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
    padding: 8px 6px !important;
    resize: none !important;
    box-shadow: none !important;
}
.lat-composer + div [data-testid="stTextArea"] textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}

/* Compact rounded control buttons inside the composer. */
.lat-composer + div [data-testid="stButton"] button {
    min-height: 36px !important;
    padding: 4px 14px !important;
    border-radius: 999px !important;
    font-weight: 600 !important;
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #E7E9ED !important;
}
.lat-composer + div [data-testid="stButton"] button:hover {
    background: rgba(255, 255, 255, 0.10) !important;
    border-color: rgba(255, 255, 255, 0.20) !important;
}
.lat-composer + div [data-testid="stButton"] button[kind="primary"] {
    background: #5865F2 !important;
    border-color: #4752C4 !important;
    color: white !important;
    width: 44px !important;
    min-width: 44px !important;
    padding: 0 !important;
    border-radius: 999px !important;
}
.lat-composer + div [data-testid="stButton"] button[kind="primary"]:hover {
    background: #4752C4 !important;
}

/* The + popover button (attach evidence) */
.lat-composer + div [data-testid="stPopover"] button {
    min-height: 36px !important;
    width: 44px !important;
    padding: 0 !important;
    border-radius: 999px !important;
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #E7E9ED !important;
    font-size: 18px !important;
}
.lat-composer + div [data-testid="stPopover"] button:hover {
    background: rgba(255, 255, 255, 0.10) !important;
}

/* Move-controls row (Value Tag, Action, Target selectors) gets a softer look. */
.lat-move-controls {
    max-width: 880px;
    margin: 0 auto 8px auto;
    padding: 6px 4px;
}


/* =================================== Claude-like flowing chat & floating pill === */

/* Drop the default Streamlit container border outline on the chat scroll area.
   We previously asked for border=True; now even without it, certain themes
   render a faint outline. Kill it. */
[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]:has(.proponent-bubble),
[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"]:has(.opponent-bubble) {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

/* The chat scroll container: smoother scroll, hide hard outline. */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    scroll-behavior: smooth;
}

/* The .lat-composer wrapper pulls the pill closer to Claude's look:
   floating with rounded corners, faint border, soft shadow, centred,
   max-width capped. */
.lat-composer + div [data-testid="stVerticalBlockBorderWrapper"],
.lat-composer + div [data-testid="stContainer"] {
    border-radius: 26px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(38, 40, 44, 0.94) !important;
    backdrop-filter: blur(8px);
    padding: 14px 16px !important;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.30);
    max-width: 900px;
    margin: 12px auto 0 auto;
}

/* Textarea inside the pill: borderless, transparent, large hit area. */
.lat-composer + div [data-testid="stTextArea"] textarea {
    background: transparent !important;
    border: 0 !important;
    border-radius: 14px !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
    padding: 6px 4px !important;
    resize: none !important;
    box-shadow: none !important;
    min-height: 64px !important;
    color: #E7E9ED !important;
}
.lat-composer + div [data-testid="stTextArea"] textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}
.lat-composer + div [data-testid="stTextArea"] label {
    display: none !important;
}

/* Suppress the bordered look around the inner textarea wrapper. */
.lat-composer + div [data-baseweb="textarea"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Smoother scroll bar in the chat container. */
.stApp [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar {
    width: 8px;
}
.stApp [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.10);
    border-radius: 4px;
}
.stApp [data-testid="stVerticalBlockBorderWrapper"] ::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.18);
}


/* === Claude-style invisible bottom-stuck composer (REVISED) ====================
   - Composer container is bottom-sticky (always pinned at the lower edge of
     the chat column as you scroll).
   - The visible box around it is almost invisible (no border, barely-there
     background, no hard shadow). Free-flowing.
   - Textarea inside is fully borderless.
================================================================================== */
.lat-composer + div [data-testid="stVerticalBlockBorderWrapper"],
.lat-composer + div [data-testid="stContainer"] {
    position: sticky !important;
    bottom: 0 !important;
    z-index: 60 !important;
    background: linear-gradient(180deg,
        rgba(30, 31, 34, 0.00) 0%,
        rgba(30, 31, 34, 0.78) 18%,
        rgba(30, 31, 34, 0.94) 60%) !important;
    backdrop-filter: blur(10px);
    border: none !important;
    border-radius: 22px !important;
    box-shadow: none !important;
    padding: 14px 18px 12px !important;
    max-width: 940px !important;
    margin: 0 auto !important;
}

/* The textarea: invisible, free-flowing, no border, no background. */
.lat-composer + div [data-testid="stTextArea"] textarea,
.lat-composer + div [data-baseweb="textarea"] textarea {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 18px !important;
    color: #E7E9ED !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
    padding: 12px 16px !important;
    min-height: 56px !important;
    resize: none !important;
    box-shadow: none !important;
    transition: border-color 0.12s ease, background 0.12s ease;
}
.lat-composer + div [data-testid="stTextArea"] textarea:hover,
.lat-composer + div [data-baseweb="textarea"] textarea:hover {
    background: rgba(255, 255, 255, 0.06) !important;
    border-color: rgba(255, 255, 255, 0.14) !important;
}
.lat-composer + div [data-testid="stTextArea"] textarea:focus,
.lat-composer + div [data-baseweb="textarea"] textarea:focus {
    background: rgba(255, 255, 255, 0.07) !important;
    border-color: rgba(255, 255, 255, 0.22) !important;
    outline: none !important;
    box-shadow: none !important;
}
.lat-composer + div [data-testid="stTextArea"] label,
.lat-composer + div [data-baseweb="textarea"]::before {
    display: none !important;
}
.lat-composer + div [data-baseweb="textarea"] {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

/* Compact rounded control buttons on the row below the textarea. */
.lat-composer + div [data-testid="stButton"] button {
    min-height: 34px !important;
    padding: 4px 14px !important;
    border-radius: 999px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    color: #E7E9ED !important;
    box-shadow: none !important;
}
.lat-composer + div [data-testid="stButton"] button:hover {
    background: rgba(255, 255, 255, 0.09) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
}
.lat-composer + div [data-testid="stButton"] button[kind="primary"] {
    background: #5865F2 !important;
    border-color: #4752C4 !important;
    color: white !important;
    width: 40px !important;
    min-width: 40px !important;
    padding: 0 !important;
    border-radius: 999px !important;
}
.lat-composer + div [data-testid="stButton"] button[kind="primary"]:hover {
    background: #4752C4 !important;
}
.lat-composer + div [data-testid="stPopover"] button {
    min-height: 34px !important;
    width: 40px !important;
    padding: 0 !important;
    border-radius: 999px !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    color: #E7E9ED !important;
    font-size: 17px !important;
    line-height: 1 !important;
}
.lat-composer + div [data-testid="stPopover"] button:hover {
    background: rgba(255, 255, 255, 0.09) !important;
}

/* ============================================================
 * Logic-map fullscreen view
 * Streamlit shows a fullscreen-expand button on chart elements
 * (top-right corner on hover). Recent Streamlit versions do NOT
 * use the browser's Fullscreen API — instead they inline-style
 * the wrapper with `position: fixed; top: 0; ...` to *fake*
 * fullscreen. So we have to target both the inline-style state
 * and the legacy :fullscreen state, plus any class-based variant
 * Streamlit may use. The goal: anywhere a graphviz chart is
 * shown expanded, give the wrapper a white backdrop so the
 * transparent SVG renders cleanly on white instead of the dark
 * app background bleeding through.
 * ============================================================ */

/* Modern Streamlit: fake-fullscreen via inline positioning. */
[data-testid="stFullScreenFrame"][style*="position: fixed"],
[data-testid="stFullScreenFrame"][style*="position:fixed"] {
    background: #FFFFFF !important;
    padding: 24px !important;
    overflow: auto !important;
}
[data-testid="stElementFullscreenWrapper"][style*="position: fixed"],
[data-testid="stElementFullscreenWrapper"][style*="position:fixed"],
div[style*="position: fixed"]:has([data-testid="stGraphVizChart"]),
div[style*="position:fixed"]:has([data-testid="stGraphVizChart"]) {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    padding: 24px !important;
    overflow: auto !important;
}
[data-testid="stFullScreenFrame"][style*="position: fixed"] *,
[data-testid="stFullScreenFrame"][style*="position:fixed"] * {
    background-color: #FFFFFF !important;
}
[data-testid="stElementFullscreenWrapper"][style*="position: fixed"] *,
[data-testid="stElementFullscreenWrapper"][style*="position:fixed"] *,
div[style*="position: fixed"]:has([data-testid="stGraphVizChart"]) *,
div[style*="position:fixed"]:has([data-testid="stGraphVizChart"]) * {
    background-color: #FFFFFF !important;
}
[data-testid="stFullScreenFrame"][style*="position: fixed"] [data-testid="stGraphVizChart"],
[data-testid="stFullScreenFrame"][style*="position: fixed"] .stGraphVizChart,
[data-testid="stFullScreenFrame"][style*="position: fixed"] svg,
[data-testid="stFullScreenFrame"][style*="position:fixed"] svg,
[data-testid="stElementFullscreenWrapper"][style*="position: fixed"] svg,
[data-testid="stElementFullscreenWrapper"][style*="position:fixed"] svg,
div[style*="position: fixed"]:has([data-testid="stGraphVizChart"]) svg,
div[style*="position:fixed"]:has([data-testid="stGraphVizChart"]) svg {
    background: #FFFFFF !important;
}

/* Class-based fullscreen variants used in some Streamlit builds. */
.stFullScreenFrame--expanded,
.fullScreenFrame--expanded,
[data-testid="stFullScreenFrame"][data-expanded="true"],
[data-testid="stFullScreenFrame"][aria-expanded="true"] {
    background: #FFFFFF !important;
    padding: 24px !important;
}
.stFullScreenFrame--expanded svg,
.fullScreenFrame--expanded svg,
[data-testid="stFullScreenFrame"][data-expanded="true"] svg,
[data-testid="stFullScreenFrame"][aria-expanded="true"] svg {
    background: #FFFFFF !important;
}

/* Legacy browser-API fullscreen (older Streamlit). Kept as fallback. */
[data-testid="stFullScreenFrame"]:fullscreen,
:fullscreen,
:-webkit-full-screen,
:-moz-full-screen {
    background: #FFFFFF !important;
}
:fullscreen svg,
:-webkit-full-screen svg,
:-moz-full-screen svg {
    background: #FFFFFF !important;
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
    white-space: nowrap;
    word-break: keep-all;
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

.lat-thread-header {
    background: var(--lat-page);
    border-bottom-color: var(--lat-border);
}

.lat-thread-header h1 {
    color: var(--lat-text);
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


def reveal_typing_bubble(mid, content, side, value_tag="Logic",
                         seconds_per_word=0.055, max_seconds=5.0) -> None:
    """Show a generated message word-by-word before it is committed."""
    words = content.split()
    if not words:
        return

    side_class = "proponent-bubble" if side == "Side A" else "opponent-bubble"
    delay = min(seconds_per_word, max_seconds / max(1, len(words)))
    placeholder = st.empty()

    for i in range(1, len(words) + 1):
        partial = html.escape(" ".join(words[:i]))
        placeholder.markdown(
            f'<div class="{side_class}">'
            f'<b>{html.escape(mid)} Â· {html.escape(value_tag)}</b>'
            f'{partial}<span class="typing-cursor">|</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    placeholder.empty()


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
    # Hard size cap so the SVG stays comfortable inside the 600px-tall map
    # column without internal scroll. Streamlit's use_container_width=True
    # then scales the bounded SVG to the column width, so nodes shrink
    # proportionally instead of growing past the container. Tight
    # nodesep/ranksep keep the layout compact in both modes.
    graph.attr(rankdir="TB", bgcolor="transparent",
               nodesep="0.08",
               ranksep="0.14",
               margin="0.03", pad="0.03",
               fontname="Helvetica",
               size="3.0,4.9!", ratio="compress")
    # Defaults so every node uses the same compact rounded-box shape.
    # Smaller font, fixed node dimensions, and tighter margins help 6-9 nodes fit
    # in the 600px map container without scrolling.
    graph.attr("node", shape="box", style="rounded,filled",
               fontname="Helvetica", fontsize="8",
               fontcolor="white", color="#3F4147",
               margin="0.04,0.025", penwidth="1.6",
               width="1.45", height="0.48", fixedsize="true")
    graph.attr("edge", fontname="Helvetica", fontsize="7",
               penwidth="1.15", arrowsize="0.50")

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
        # Human-vs-Human path: same caps apply (set above). No-op here
        # so the per-side colouring below still runs.
        pass

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
            fill = "#5865F2"
            border_color = "#22C55E" if status == "IN" else "#EF4444"
            owner_label = "A"
        elif side == "Side B":
            fill = "#F23F42"
            border_color = "#22C55E" if status == "IN" else "#EF4444"
            owner_label = "B"
        else:
            fill = "#6B7280"
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


def inject_enter_to_send():
    """Inject a JS handler: plain Enter in the composer textarea clicks
    the Send button (the only primary button on screen).
    Shift+Enter still inserts a newline, matching Claude/ChatGPT behaviour.

    Safe to call once per page render — the script self-guards so it only
    attaches the listener once per browser session.
    """
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        (function() {
            try {
                const doc = window.parent.document;
                if (doc.__latEnterToSendAttached) return;
                doc.__latEnterToSendAttached = true;
                doc.addEventListener('keydown', function(e) {
                    if (e.key !== 'Enter') return;
                    if (e.shiftKey || e.isComposing) return;
                    if (!e.target || e.target.tagName !== 'TEXTAREA') return;
                    // Pick the visible primary button (Send) on the page
                    const btns = doc.querySelectorAll('button[kind=\"primary\"]');
                    let sendBtn = null;
                    for (const b of btns) {
                        if (b.offsetParent !== null) { sendBtn = b; break; }
                    }
                    if (!sendBtn) return;
                    e.preventDefault();
                    sendBtn.click();
                }, true);
            } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )


def inject_logic_map_fullscreen_white():
    """JS fallback that forces a WHITE backdrop on the Streamlit chart
    fullscreen wrapper. CSS alone isn't reliable because Streamlit's
    fullscreen state is implemented differently across versions (some
    use the browser :fullscreen API, some inline-style position:fixed,
    some toggle a class). A MutationObserver watches the document for
    any stFullScreenFrame whose state changes to "expanded" and writes
    background:white directly on it. Safe to call every render — the
    observer self-guards so it only attaches once per browser session.
    """
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        (function() {
            try {
                const doc = window.parent.document;
                if (doc.__latFsWhiteAttachedV4) return;
                doc.__latFsWhiteAttachedV4 = true;
                // Clean up the over-broad V3 paint if the page still has it.
                doc.body.style.removeProperty('background');
                doc.body.style.removeProperty('background-color');
                const initialApp = doc.querySelector('.stApp');
                if (initialApp) {
                    initialApp.style.removeProperty('background');
                    initialApp.style.removeProperty('background-color');
                }

                function isExpanded(el) {
                    if (!el) return false;
                    // Heuristic 1: inline-positioned fixed/absolute fullscreen
                    const s = el.getAttribute('style') || '';
                    if (s.indexOf('position: fixed') !== -1) return true;
                    if (s.indexOf('position:fixed') !== -1) return true;
                    const r = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
                    if (s.indexOf('position: absolute') !== -1 &&
                        r && r.width > window.innerWidth * 0.65) return true;
                    // Heuristic 2: explicit data/aria attributes
                    if (el.getAttribute('data-expanded') === 'true') return true;
                    if (el.getAttribute('aria-expanded') === 'true') return true;
                    // Heuristic 3: class-name based variants
                    const c = el.className || '';
                    if (typeof c === 'string') {
                        if (c.indexOf('expanded') !== -1) return true;
                        if (c.indexOf('Expanded') !== -1) return true;
                    }
                    // Heuristic 4: native fullscreen API
                    if (doc.fullscreenElement === el) return true;
                    return false;
                }

                function paintWhite(el) {
                    el.style.setProperty('background', '#FFFFFF', 'important');
                    el.style.setProperty('background-color', '#FFFFFF', 'important');
                    el.style.setProperty('padding', '24px', 'important');
                    el.style.setProperty('overflow', 'auto', 'important');
                    // Repaint inner SVG / chart wrappers as well so the
                    // graphviz transparent bgcolor reads white.
                    const inner = el.querySelectorAll(
                        '[data-testid="stGraphVizChart"], .stGraphVizChart, svg, div'
                    );
                    inner.forEach(function(n) {
                        n.style.setProperty('background', '#FFFFFF', 'important');
                        n.style.setProperty('background-color', '#FFFFFF', 'important');
                    });
                }

                function unpaint(el) {
                    el.style.removeProperty('background');
                    el.style.removeProperty('background-color');
                    el.style.removeProperty('padding');
                    el.style.removeProperty('overflow');
                }

                function isLogicMapSvg(svg) {
                    if (!svg) return false;
                    const text = svg.textContent || '';
                    return text.indexOf('Msg_') !== -1 &&
                           (text.indexOf('IN ') !== -1 || text.indexOf('OUT ') !== -1);
                }

                function paintAncestors(svg) {
                    let el = svg;
                    let painted = false;
                    for (let depth = 0; el && depth < 10; depth += 1, el = el.parentElement) {
                        if (isExpanded(el)) {
                            paintWhite(el);
                            painted = true;
                        }
                    }
                    return painted;
                }

                function sweep() {
                    let paintedAny = false;
                    const frames = doc.querySelectorAll(
                        '[data-testid="stFullScreenFrame"], ' +
                        '[data-testid="stElementFullscreenWrapper"], ' +
                        'div[style*="position: fixed"], ' +
                        'div[style*="position:fixed"], ' +
                        'section[style*="position: fixed"], ' +
                        'section[style*="position:fixed"]'
                    );
                    frames.forEach(function(f) {
                        const hasMap = f.querySelector(
                            '[data-testid="stGraphVizChart"], .stGraphVizChart, svg'
                        );
                        if (hasMap && isExpanded(f)) {
                            paintWhite(f);
                            paintedAny = true;
                        }
                        else unpaint(f);
                    });
                    const svgs = doc.querySelectorAll('svg');
                    svgs.forEach(function(svg) {
                        if (isLogicMapSvg(svg) && paintAncestors(svg)) {
                            paintedAny = true;
                        }
                    });
                    doc.body.style.removeProperty('background');
                    doc.body.style.removeProperty('background-color');
                    const app = doc.querySelector('.stApp');
                    if (app) {
                        app.style.removeProperty('background');
                        app.style.removeProperty('background-color');
                    }
                }

                // Re-evaluate on any style/class/attribute mutation anywhere
                // in the body. Cheap enough at this app's DOM size.
                const obs = new MutationObserver(function() { sweep(); });
                obs.observe(doc.body, {
                    attributes: true,
                    subtree: true,
                    attributeFilter: ['style', 'class', 'data-expanded',
                                      'aria-expanded']
                });
                // Initial pass in case a frame is already expanded.
                sweep();
                // Also re-sweep when the user uses the browser Fullscreen API.
                doc.addEventListener('fullscreenchange', sweep);
            } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )
