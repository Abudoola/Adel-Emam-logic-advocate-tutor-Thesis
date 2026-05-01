"""
ROLE: FRONTEND
DESCRIPTION: Handles the Streamlit UI, user interactions, and display logic.
"""
import streamlit as st
import os
import graphviz
import tempfile
import time

from logic_engine import AcademicLogicEngine, PYARG_INSTALLED
from database import save_db, load_db
from ai_agent import generate_counter_argument, transcribe_audio

st.set_page_config(page_title="Logic Advocate Arena", layout="wide")

# Ensure an uploads directory exists to store evidence images/videos
os.makedirs("uploads", exist_ok=True)

# ==========================================
# UI STYLES & DATABASE
# ==========================================
st.markdown("""
<style>
    .stChatMessage { border-radius: 20px; margin-bottom: 5px; border: none !important; }
    .proponent-bubble { background-color: #007bff; color: white; border-radius: 20px 20px 0px 20px; padding: 15px; margin-left: 25%; }
    .opponent-bubble { background-color: #343a40; color: white; border-radius: 20px 20px 20px 0px; padding: 15px; margin-right: 25%; }
    .stat-card { padding: 10px; border-radius: 10px; text-align: center; border: 1px solid #444; background-color: #1e1e1e; }
    .victory-box { padding: 30px; border-radius: 15px; text-align: center; margin-top: 20px; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INITIALIZATION
# ==========================================
if 'history' not in st.session_state: st.session_state.history = load_db()
if 'engine' not in st.session_state:
    st.session_state.engine = AcademicLogicEngine()
    st.session_state.messages = []
    st.session_state.msg_counter = 1

if 'battle_over' not in st.session_state: st.session_state.battle_over = False

st.session_state.engine.evaluate_semantics()
existing_ids = list(st.session_state.engine.nodes.keys())

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚔️ Battle Controls")
    
    if existing_ids and not st.session_state.battle_over:
        if st.button("🏁 FINISH ARGUMENT", type="primary", use_container_width=True):
            st.session_state.battle_over = True
            st.rerun()
            
    if st.session_state.battle_over:
        if st.button("🔥 Start New Battle", use_container_width=True):
            if st.session_state.messages:
                session_name = f"Battle: {st.session_state.messages[0]['content'][:15]}..."
                st.session_state.history.append({"name": session_name, "data": st.session_state.messages})
                save_db(st.session_state.history)
            st.session_state.engine = AcademicLogicEngine()
            st.session_state.messages = []
            st.session_state.msg_counter = 1
            st.session_state.battle_over = False 
            st.rerun()

    st.divider()
    if st.button("💾 Save Current State", use_container_width=True):
        if st.session_state.messages:
            session_name = f"Battle: {st.session_state.messages[0]['content'][:15]}..."
            st.session_state.history.append({"name": session_name, "data": st.session_state.messages})
            save_db(st.session_state.history)
            st.rerun()

    st.divider()
    st.subheader("📜 History")
    for i, session in enumerate(st.session_state.history):
        if isinstance(session, dict) and 'name' in session:
            if st.button(f"📂 {session['name']}", key=f"hist_{i}"):
                st.session_state.messages = session['data']
                new_eng = AcademicLogicEngine()
                for m in session['data']:
                    new_eng.add_argument(m['id'], m['content'], m['weight'])
                    if m.get('target') and m['action'] == "Attack":
                        new_eng.add_direct_attack(m['id'], m['target'])
                st.session_state.engine = new_eng
                st.session_state.battle_over = False 
                st.rerun()

    if existing_ids:
        st.divider()
        st.subheader("🗺️ Logic Map")
        graph = graphviz.Digraph()
        graph.attr(bgcolor='transparent')
        for arg_id in st.session_state.engine.nodes.keys():
            col = "#28a745" if st.session_state.engine.statuses.get(arg_id) == "IN" else "#dc3545"
            graph.node(arg_id, arg_id, color='white', style='filled', fillcolor=col, fontcolor='white')
        for m in st.session_state.messages:
            if m.get('target'):
                ecol = "#dc3545" if m['action'] == "Attack" else "#28a745"
                graph.edge(m['id'], m['target'], color=ecol)
        st.graphviz_chart(graph)

# ==========================================
# MAIN DASHBOARD
# ==========================================
st.title("⚔️ Logic Advocate Arena")

if PYARG_INSTALLED:
    st.caption("🟢 Powered by: `python-argumentation` (PyArg Academic Standard)")
else:
    st.caption("🟠 Powered by: Local Semantics Engine (PyArg not detected)")

if existing_ids:
    c1, c2, c3 = st.columns(3)
    main_status = st.session_state.engine.statuses.get("Msg_1", "OUT")
    with c1: st.markdown(f'<div class="stat-card"><b>Claim Status</b><br><span style="color:{"#28a745" if main_status=="IN" else "#dc3545"};">{"● SURVIVING" if main_status=="IN" else "● DEFEATED"}</span></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><b>Winning Side</b><br><span style="color:#ffaa00;">🥇 {"PRO" if main_status=="IN" else "OPP"}</span></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><b>Total Logic</b><br><span>{len(existing_ids)} Nodes</span></div>', unsafe_allow_html=True)

st.write("")

# Render the chat bubbles
for msg in st.session_state.messages:
    side_class = "proponent-bubble" if msg["side"] == "Side A" else "opponent-bubble"
    with st.container():
        st.markdown(f'<div class="{side_class}"><b>{msg["id"]} ({msg["side"]})</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Display uploaded media if it exists
        if "media_path" in msg and os.path.exists(msg["media_path"]):
            if msg["media_type"].startswith("image"):
                st.image(msg["media_path"], width=300)
            elif msg["media_type"].startswith("video"):
                st.video(msg["media_path"])
                
        st.caption(f"Logic Power: {msg['weight']}/25")
        st.progress(min(1.0, msg['weight'] / 25))
    st.write("")

# ==========================================
# INPUT / VICTORY SCREEN
# ==========================================
st.divider()

if st.session_state.battle_over:
    st.header("🏁 The Debate Has Concluded!")
    main_status = st.session_state.engine.statuses.get("Msg_1", "OUT")
    
    if main_status == "IN":
        st.markdown('<div class="victory-box" style="background-color: rgba(40, 167, 69, 0.2); border: 2px solid #28a745; color: #28a745;">🏆 SIDE A (Proponent) emerges victorious!<br>The main claim stands strong.</div>', unsafe_allow_html=True)
        st.balloons() 
    else:
        st.markdown('<div class="victory-box" style="background-color: rgba(220, 53, 69, 0.2); border: 2px solid #dc3545; color: #dc3545;">💥 SIDE B (Opponent) claims victory!<br>The main claim has been shattered.</div>', unsafe_allow_html=True)
        
    st.info("Start a New Battle from the sidebar to play again, or load a past debate.")

else:
    # --- SMART TARGETING UI ---
    user_msgs = {m["id"]: m["content"] for m in st.session_state.messages if m["side"] == "Side A"}
    ai_msgs = {m["id"]: m["content"] for m in st.session_state.messages if m["side"] == "Side B"}

    if not existing_ids:
        st.info("🟢 You go first! Make your Main Claim below.")
        action_choice = "Main Claim"
        target = "None"
        action = "Attack"
    else:
        action_choice = st.radio("Choose your move:", ["⚔️ Attack AI", "🛡️ Support My Argument"], horizontal=True)
        
        if action_choice == "⚔️ Attack AI":
            if ai_msgs:
                target = st.selectbox("Which AI argument are you attacking?", list(ai_msgs.keys()), format_func=lambda x: f"[{x}] {ai_msgs[x]}")
                action = "Attack"
            else:
                st.warning("No AI arguments to attack yet.")
                target = "None"
                action = "Attack"
                
        elif action_choice == "🛡️ Support My Argument":
            if user_msgs:
                target = st.selectbox("Which of your arguments are you supporting?", list(user_msgs.keys()), format_func=lambda x: f"[{x}] {user_msgs[x]}")
                action = "Support"
            else:
                st.warning("You have no arguments to support.")
                target = "None"
                action = "Support"

    # --- NEW: MEDIA UPLOADER ---
    with st.expander("📎 Attach Evidence (Image/Video)"):
        uploaded_file = st.file_uploader("Upload visual proof", type=["png", "jpg", "jpeg", "mp4"])

    if "audio_key" not in st.session_state:
        st.session_state.audio_key = 0

    audio_val = st.audio_input("🎙️ Speak your argument", key=f"audio_{st.session_state.audio_key}")
    text_val = st.chat_input("...or type your argument here")

    text = None
    if text_val:
        text = text_val
    elif audio_val:
        with st.spinner("Transcribing your voice..."):
            audio_path = os.path.join("uploads", f"temp_audio_{int(time.time())}.wav")
            with open(audio_path, "wb") as f:
                f.write(audio_val.getbuffer())
            text = transcribe_audio(audio_path)
            
        st.session_state.audio_key += 1

    if text:
        # --- 1. PROCESS THE HUMAN'S TURN (SIDE A) ---
        user_mid = f"Msg_{st.session_state.msg_counter}"
        user_weight = min(25, len(text.split()) + 5)
        
        # Handle the uploaded file locally if there is one
        saved_media_path = None
        media_type = None
        if uploaded_file:
            media_type = uploaded_file.type
            saved_media_path = os.path.join("uploads", f"{user_mid}_{uploaded_file.name}")
            with open(saved_media_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.session_state.engine.add_argument(user_mid, text, user_weight)
        
        if target != "None":
            if action == "Attack": 
                st.session_state.engine.add_direct_attack(user_mid, target)
            else: 
                st.session_state.engine.add_support(user_mid, target)

        msg_data = {
            "id": user_mid, "content": text, "side": "Side A", 
            "target": target if target != "None" else None, 
            "action": action, "weight": user_weight
        }
        
        # Add media references to the message dictionary if evidence was attached
        if saved_media_path:
            msg_data["media_path"] = saved_media_path
            msg_data["media_type"] = media_type

        st.session_state.messages.append(msg_data)
        st.session_state.msg_counter += 1

        # --- 2. PROCESS THE LLM'S TURN (SIDE B) ---
        with st.spinner("The Advocate is analyzing your evidence and formulating a counter-argument..."):
            try:
                llm_weight, llm_text = generate_counter_argument(
                    st.session_state.messages, 
                    text, 
                    uploaded_file, 
                    saved_media_path, 
                    media_type
                )
                
                if llm_text == "CONCEDE":
                    st.toast("🏆 The AI has conceded to your logic!")
                    
                    # NEW: Add a final white-flag message to the chat history
                    st.session_state.messages.append({
                        "id": "Concession", 
                        "content": "I have no further counter-arguments. Your logic is sound. You win.", 
                        "side": "Side B", 
                        "target": user_mid, 
                        "action": "Support", # Registers as a neutral move visually
                        "weight": 0
                    })
                    
                    # End the battle
                    st.session_state.battle_over = True
                else:
                    llm_mid = f"Msg_{st.session_state.msg_counter}"
                    st.session_state.engine.add_argument(llm_mid, llm_text, llm_weight)
                    st.session_state.engine.add_direct_attack(llm_mid, user_mid)

                    st.session_state.messages.append({
                        "id": llm_mid, "content": llm_text, "side": "Side B", 
                        "target": user_mid, "action": "Attack", "weight": llm_weight
                    })
                    st.session_state.msg_counter += 1
                st.rerun()

            except Exception as e:
                st.error(f"The AI encountered an error: {e}")