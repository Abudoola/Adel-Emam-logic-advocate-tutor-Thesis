"""
views/mobile_multiplayer.py
---------------------------
Online multiplayer view: host dashboard + player/spectator screen.

Two debaters on different networks share state through a polled JSON
lobby file (lobby_db.lobbies.json). The host opens an ngrok tunnel
and shows a QR code; players scan it to join.
"""
from __future__ import annotations
import os
import socket
import time
from io import BytesIO

import streamlit as st
import qrcode

import lobby_db
from logic_engine import AcademicLogicEngine, VALID_VALUE_TAGS
from ai_agent import generate_hint_v2, transcribe_audio
from views._styles import (
    inject_css,
    render_argument_bubble,
    render_momentum_bar,
    render_logic_graph,
)
from views.engine_inspector import render_inspector_panel


def _get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def _rebuild_engine_for_lobby(lobby) -> AcademicLogicEngine:
    """Reconstruct the engine fresh from the lobby's message list."""
    return AcademicLogicEngine.rebuild_from_messages(lobby["messages"])


# =================================================================== PLAYER

def render_mobile_player(room_id, role=None) -> None:
    inject_css()

    lobby = lobby_db.get_lobby(room_id)
    if not lobby:
        st.error("❌ Invalid Room ID. This lobby does not exist.")
        st.stop()

    # ROLE SELECTION SCREEN
    if role is None:
        st.title("🌐 Join Online Debate")
        st.subheader(f"Room: {room_id}")

        side_a_taken = "Side A" in lobby.get("players", [])
        side_b_taken = "Side B" in lobby.get("players", [])

        st.markdown("### Choose your role:")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🎙️ Debater")
            if not side_a_taken:
                if st.button("Join as Side A (Pro)", use_container_width=True, type="primary"):
                    lobby_db.join_lobby(room_id, "Side A")
                    st.query_params["role"] = "Side A"
                    st.rerun()
            else:
                st.info("✅ Side A is taken")
            if not side_b_taken:
                if st.button("Join as Side B (Con)", use_container_width=True, type="primary"):
                    lobby_db.join_lobby(room_id, "Side B")
                    st.query_params["role"] = "Side B"
                    st.rerun()
            else:
                st.info("✅ Side B is taken")
            if side_a_taken and side_b_taken:
                st.warning("Both debate slots are full. Join as spectator!")
        with c2:
            st.markdown("#### 👁️ Spectator")
            if st.button("Watch the Debate", use_container_width=True):
                st.query_params["role"] = "Spectator"
                st.rerun()

        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=3000, limit=None, key="role_select_refresh")
        except ImportError:
            pass
        st.stop()

    # SPECTATOR VIEW
    if role == "Spectator":
        st.title(f"👁️ Spectating Room {room_id}")
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=3000, limit=None, key="spectator_refresh")
        except ImportError:
            pass

        if lobby["state"] == "WAITING":
            st.info("⏳ Waiting for the debate to begin...")
            st.stop()
        elif lobby["state"] == "FINISHED":
            st.header("🏁 The Debate Has Concluded!")

        st.markdown("### 📊 Live Momentum")
        engine = _rebuild_engine_for_lobby(lobby)
        render_momentum_bar(lobby["messages"], engine.statuses, engine.nodes)

        st.markdown("### The Debate")
        chat_container = st.container(height=400)
        with chat_container:
            for m in lobby["messages"]:
                render_argument_bubble(
                    m["id"], m["content"], m["side"], m["weight"],
                    m["action"], m["target"], m.get("value_tag", "Logic"),
                    engine.scores.get(m["id"], 1.0),
                    is_concession=(m.get("id") == "Concession"),
                )
        st.stop()

    # DEBATER VIEW
    st.title(f"🌐 Online Debate · Room {room_id}")
    st.subheader(f"You are: {role}")

    if lobby["state"] == "WAITING":
        st.info("⏳ Waiting for both players to join...")
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=2000, limit=None, key="player_waiting_refresh")
        except ImportError:
            pass
        st.stop()

    if lobby["state"] == "FINISHED":
        st.header("🏁 The Debate Has Concluded!")
        st.stop()

    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=3000, limit=None, key="player_active_refresh")
    except ImportError:
        pass

    engine = _rebuild_engine_for_lobby(lobby)
    render_momentum_bar(lobby["messages"], engine.statuses, engine.nodes)

    st.markdown("### The Debate So Far")
    chat_container = st.container(height=400)
    with chat_container:
        for m in lobby["messages"]:
            render_argument_bubble(
                m["id"], m["content"], m["side"], m["weight"],
                m["action"], m["target"], m.get("value_tag", "Logic"),
                engine.scores.get(m["id"], 1.0),
                is_concession=(m.get("id") == "Concession"),
            )

    # Waiting for opponent
    if lobby["current_turn"] != role:
        st.warning(f"⏳ Waiting for {lobby['current_turn']} to make their move...")
        if "p_hints_used" not in st.session_state:
            st.session_state.p_hints_used = 0
        st.stop()

    # IT IS YOUR TURN
    st.success("🟢 It is your turn. Make your move.")

    if "p_hints_used" not in st.session_state:
        st.session_state.p_hints_used = 0
    if "p_last_hint" not in st.session_state:
        st.session_state.p_last_hint = None

    enemy_msgs = {m["id"]: m["content"] for m in lobby["messages"]
                  if m["side"] != role}
    my_msgs    = {m["id"]: m["content"] for m in lobby["messages"]
                  if m["side"] == role}

    action = "Attack"
    target = "None"
    value_tag = "Logic"
    if lobby["messages"]:
        turn_idx = lobby["msg_counter"]
        col_act, col_tgt, col_val = st.columns([1, 1.5, 1])
        with col_act:
            action_choice = st.radio(
                "Move:", ["⚔️ Attack", "🛡️ Support"],
                horizontal=True, key=f"action_m_{turn_idx}",
            )
        with col_tgt:
            if action_choice == "⚔️ Attack" and enemy_msgs:
                target = st.selectbox(
                    "Target:", list(enemy_msgs.keys()),
                    index=len(enemy_msgs) - 1,
                    format_func=lambda x: f"[{x}] {enemy_msgs[x]}",
                    key=f"target_enemy_m_{turn_idx}",
                )
                action = "Attack"
            elif action_choice == "🛡️ Support" and my_msgs:
                target = st.selectbox(
                    "Target:", list(my_msgs.keys()),
                    index=len(my_msgs) - 1,
                    format_func=lambda x: f"[{x}] {my_msgs[x]}",
                    key=f"target_self_m_{turn_idx}",
                )
                action = "Support"
        with col_val:
            value_tag = st.selectbox(
                "Value Tag:", VALID_VALUE_TAGS, key=f"val_m_{turn_idx}",
            )
    else:
        st.info("Make your main claim.")
        value_tag = st.selectbox("Value Tag:", VALID_VALUE_TAGS, key="val_first_m")

    st.markdown("---")

    # Blitz timer
    if lobby.get("blitz_enabled"):
        elapsed = int(time.time() - lobby.get("turn_start_time", time.time()))
        remaining = max(0, 60 - elapsed)
        color = "red" if remaining <= 10 else "black"
        st.markdown(
            f"<h3 style='text-align: center; color: {color};'>"
            f"⏳ Time Remaining: {remaining}s</h3>",
            unsafe_allow_html=True,
        )
        if remaining == 0 and lobby["current_turn"] == role:
            new_turn = "Side B" if role == "Side A" else "Side A"
            lobby_db.update_lobby(room_id, current_turn=new_turn, turn_start_time=time.time())
            st.error("⏰ TIME'S UP! Turn forfeited.")
            time.sleep(2)
            st.rerun()

    # Hint button (MDP-guided)
    if enemy_msgs and st.button("💡 Get Hint", use_container_width=False):
        own_main_claim = my_msgs[next(iter(my_msgs))] if my_msgs else ""
        last_enemy_msg = list(enemy_msgs.values())[-1]
        with st.spinner("Strategising..."):
            result = generate_hint_v2(
                engine=engine,
                messages=lobby["messages"],
                learner_side=role,
                recent_hints=st.session_state.p_hints_used,
                enemy_argument=last_enemy_msg,
                own_main_claim=own_main_claim,
            )
        st.session_state.p_last_hint = result
        st.session_state.p_hints_used += 1

    if st.session_state.p_last_hint:
        h = st.session_state.p_last_hint
        st.markdown(
            f'<div class="hint-card">'
            f'<div class="hint-strategy">STRATEGY · {h["action"]}</div>'
            f'<div class="hint-body">{h["hint"]}</div>'
            f'<div class="hint-debug">MDP state: {h["state"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Composer
    turn_key = lobby["msg_counter"]
    uploaded_file, audio_file = None, None
    col_attach, col_input, col_send = st.columns([0.6, 8, 0.8])
    with col_attach:
        with st.popover("➕", use_container_width=True):
            uploaded_file = st.file_uploader(
                "📎 Attach evidence",
                type=["png", "jpg", "jpeg", "mp4"],
                key=f"mobile_file_{turn_key}",
            )
            if hasattr(st, "audio_input"):
                audio_file = st.audio_input("🎤 Record voice",
                                             key=f"mobile_audio_{turn_key}")
            elif hasattr(st, "experimental_audio_input"):
                audio_file = st.experimental_audio_input("🎤 Record voice",
                                                          key=f"mobile_audio_{turn_key}")
    with col_input:
        text_input = st.text_input("msg", placeholder="Type a message",
                                    key="mobile_text", label_visibility="collapsed")
    with col_send:
        submitted = st.button("➡️", use_container_width=True, type="primary",
                               key="mobile_submit")

    text = ""
    if submitted and text_input:
        text += text_input + "\n"
    if audio_file is not None:
        try:
            buffer = audio_file.getbuffer()
            if len(buffer) > 100:
                with st.spinner("Transcribing voice..."):
                    os.makedirs("uploads", exist_ok=True)
                    audio_path = os.path.join("uploads",
                                                f"temp_audio_{int(time.time())}.wav")
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

            mid = f"Msg_{lobby['msg_counter']}"
            weight = min(25, len(text.split()) + 5)

            saved_media_path, media_type = None, None
            if uploaded_file:
                media_type = uploaded_file.type
                os.makedirs("uploads", exist_ok=True)
                saved_media_path = os.path.join(
                    "uploads", f"{mid}_{uploaded_file.name}")
                with open(saved_media_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            msg_data = {
                "id":        mid,
                "content":   text,
                "side":      role,
                "target":    target if target != "None" else None,
                "action":    action,
                "weight":    weight,
                "value_tag": value_tag,
            }
            if saved_media_path:
                msg_data["media_path"] = saved_media_path
                msg_data["media_type"] = media_type

            lobby["messages"].append(msg_data)
            lobby["msg_counter"] += 1
            lobby["current_turn"] = "Side B" if role == "Side A" else "Side A"
            lobby["propose_end"][role] = False
            lobby_db.update_lobby(
                room_id,
                messages=lobby["messages"],
                msg_counter=lobby["msg_counter"],
                current_turn=lobby["current_turn"],
                propose_end=lobby["propose_end"],
                turn_start_time=time.time(),
            )
            st.session_state.p_hints_used = 0
            st.session_state.p_last_hint = None
            st.rerun()

    st.write("")
    if st.button("🚨 Propose Ending Debate"):
        lobby["propose_end"][role] = True
        lobby_db.update_lobby(room_id, propose_end=lobby["propose_end"])
        st.toast("End debate proposed. Waiting for opponent...")
        st.rerun()

    # Inspector panel
    if engine.nodes:
        render_inspector_panel(engine, lobby["messages"], role,
                               st.session_state.p_hints_used)


# =================================================================== HOST

def render_mobile_host() -> None:
    inject_css()

    if "host_room" not in st.session_state:
        st.session_state.host_room = None

    if st.session_state.host_room is None:
        st.title("🌐 Create Online Debate Room")
        room_id = st.text_input("Enter a Room ID:", value="Room123")
        blitz_mode = st.checkbox("⚡ Enable Blitz Mode (60s timer)", value=False)

        if st.button("Create Room", type="primary"):
            lobby_db.create_lobby(room_id, blitz_enabled=blitz_mode)
            st.session_state.host_room = room_id
            try:
                from pyngrok import ngrok
                tunnel = ngrok.connect(8502, "http")
                public_url = tunnel.public_url
                st.session_state.host_base_url = public_url
            except Exception as e:
                local_ip = _get_ip()
                st.session_state.host_base_url = f"http://{local_ip}:8502"
                st.warning(f"⚠️ Could not create public tunnel: {e}. Using local network.")
            st.rerun()

    else:
        room_id = st.session_state.host_room
        lobby = lobby_db.get_lobby(room_id)

        if not lobby:
            st.error("Lobby was destroyed.")
            del st.session_state.host_room
            st.rerun()

        st.title(f"🎮 Host Dashboard · Room {room_id}")

        if lobby["state"] == "WAITING":
            st.subheader("📲 Scan to Join the Debate!")
            base_url = st.session_state.get("host_base_url",
                                              f"http://{_get_ip()}:8502")
            join_link = f"{base_url}/?room_id={room_id}"

            col_qr, col_info = st.columns([1, 1])
            with col_qr:
                qr_img = qrcode.make(join_link)
                img_buf = BytesIO()
                qr_img.save(img_buf, format="PNG")
                st.image(img_buf.getvalue(), width=300)
            with col_info:
                st.markdown(f"**Join Link:** [{join_link}]({join_link})")
                st.markdown("---")
                players = lobby.get("players", [])
                st.markdown(f"**Side A:** {'✅ Joined' if 'Side A' in players else '⏳ Waiting...'}")
                st.markdown(f"**Side B:** {'✅ Joined' if 'Side B' in players else '⏳ Waiting...'}")
                st.markdown(f"**Spectators:** Welcome anytime!")

            st.markdown("---")
            st.info("Waiting for both debaters to join...")

            if st.button("Force Start Debate 🚀"):
                lobby_db.update_lobby(room_id, state="ACTIVE",
                                       turn_start_time=time.time())
                st.rerun()

            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=3000, limit=None, key="host_waiting_refresh")
            except ImportError:
                pass

        elif lobby["state"] == "ACTIVE":
            st.success("🔴 Debate is LIVE!")
            if lobby.get("blitz_enabled"):
                elapsed = int(time.time() - lobby.get("turn_start_time", time.time()))
                remaining = max(0, 60 - elapsed)
                color = "red" if remaining <= 10 else "black"
                st.markdown(
                    f"<h3 style='text-align: center; color: {color};'>"
                    f"⏳ Time Remaining: {remaining}s</h3>",
                    unsafe_allow_html=True,
                )
            st.write(f"**Current Turn:** {lobby['current_turn']}")

            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=2000, limit=None, key="host_active_refresh")
            except ImportError:
                pass

            engine = _rebuild_engine_for_lobby(lobby)
            render_momentum_bar(lobby["messages"], engine.statuses, engine.nodes)

            with st.expander("🗺️ View Interactive Logic Map", expanded=False):
                st.graphviz_chart(render_logic_graph(engine, lobby["messages"]))

            st.markdown("### The Debate So Far")
            chat_container = st.container(height=400)
            with chat_container:
                for m in lobby["messages"]:
                    render_argument_bubble(
                        m["id"], m["content"], m["side"], m["weight"],
                        m["action"], m["target"], m.get("value_tag", "Logic"),
                        engine.scores.get(m["id"], 1.0),
                        is_concession=(m.get("id") == "Concession"),
                    )

            st.markdown("---")
            if lobby["propose_end"].get("Side A") and lobby["propose_end"].get("Side B"):
                st.warning("Both players proposed to end the debate.")
                lobby_db.update_lobby(room_id, state="FINISHED")
                st.rerun()

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Host Override: End Debate Now", type="primary"):
                    lobby_db.update_lobby(room_id, state="FINISHED")
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete Room & Reset"):
                    lobby_db.delete_lobby(room_id)
                    del st.session_state.host_room
                    st.rerun()

            if engine.nodes:
                render_inspector_panel(engine, lobby["messages"], "Side A", 0)

        if lobby["state"] == "FINISHED":
            st.balloons()
            st.success("The debate has concluded! Check the graph to see whose logic survived.")
            if st.button("🔄 Start New Debate", type="primary", use_container_width=True):
                lobby_db.update_lobby(
                    room_id, state="WAITING", messages=[], msg_counter=1,
                    current_turn="Side A",
                    propose_end={"Side A": False, "Side B": False},
                    players=[],
                )
                st.rerun()
            if st.button("Close Room", use_container_width=True):
                lobby_db.delete_lobby(room_id)
                del st.session_state.host_room
                st.rerun()
