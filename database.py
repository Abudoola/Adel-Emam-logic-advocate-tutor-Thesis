"""
ROLE: BACKEND (Data Layer)
DESCRIPTION: Handles saving and loading the debate history to a JSON file.
"""
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "adel_battle_history.json")

def save_db(history):
    try:
        with open(DB_PATH, "w") as f:
            json.dump(history, f)
    except OSError as e:
        raise RuntimeError(f"Failed to save battle history: {e}") from e

def load_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []
