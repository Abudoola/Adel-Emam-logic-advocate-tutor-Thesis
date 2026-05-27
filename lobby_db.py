"""
lobby_db.py
-----------
Backend (Data Layer) for online-mode lobbies.

Persists the shared debate state between clients via a single JSON
file (`lobbies.json`). Polled at 3-second intervals from both clients;
race conditions are mathematically possible but in practice rare given
the polling cadence. A future production version would replace this
with a proper key-value store.
"""
from __future__ import annotations
import json
import os
import time
from typing import Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "lobbies.json")


def load_lobbies() -> Dict[str, Dict]:
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_lobbies(data: Dict[str, Dict]) -> None:
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_lobby(room_id: str) -> Optional[Dict]:
    return load_lobbies().get(room_id)


def create_lobby(room_id: str, blitz_enabled: bool = False) -> Dict:
    lobbies = load_lobbies()
    lobbies[room_id] = {
        "room_id":         room_id,
        "state":           "WAITING",
        "players":         [],
        "messages":        [],
        "msg_counter":     1,
        "current_turn":    "Side A",
        "propose_end":     {"Side A": False, "Side B": False},
        "blitz_enabled":   blitz_enabled,
        "turn_start_time": time.time(),
    }
    save_lobbies(lobbies)
    return lobbies[room_id]


def update_lobby(room_id: str, **kwargs) -> Optional[Dict]:
    lobbies = load_lobbies()
    if room_id not in lobbies:
        return None
    lobbies[room_id].update(kwargs)
    save_lobbies(lobbies)
    return lobbies[room_id]


def join_lobby(room_id: str, role: str) -> Optional[Dict]:
    lobbies = load_lobbies()
    if room_id not in lobbies:
        return None
    if role not in lobbies[room_id]["players"]:
        lobbies[room_id]["players"].append(role)
    if len(lobbies[room_id]["players"]) >= 2 and lobbies[room_id]["state"] == "WAITING":
        lobbies[room_id]["state"] = "ACTIVE"
    save_lobbies(lobbies)
    return lobbies[room_id]


def delete_lobby(room_id: str) -> None:
    """Remove a stale lobby record. Fixes the 'residual lobby' bug
    observed in informal testing."""
    lobbies = load_lobbies()
    if room_id in lobbies:
        del lobbies[room_id]
        save_lobbies(lobbies)
