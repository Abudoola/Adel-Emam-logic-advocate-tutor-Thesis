"""
ROLE: BACKEND (Data Layer)
DESCRIPTION: Handles saving and loading the debate history to a JSON file.
"""
import os
import json
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "adel_battle_history.json")

def save_db(history):
    with open(DB_PATH, "w") as f: 
        json.dump(history, f)
    st.toast("✅ Battle saved to database!")

def load_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f: 
                return json.load(f)
        except: 
            return []
    return []
