"""
tests/conftest.py
-----------------
PyTest configuration. Makes the project root importable from inside
test modules so they can `from logic_engine import ...` etc.
"""
import os
import sys
import types

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(THIS_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Stub Streamlit and Groq so we can import modules that depend on them
# (ai_agent.py needs both at import time) without installing them.
if "streamlit" not in sys.modules:
    streamlit = types.ModuleType("streamlit")
    streamlit.secrets = {"GROQ_API_KEY": "stub-for-tests"}
    sys.modules["streamlit"] = streamlit

if "groq" not in sys.modules:
    groq = types.ModuleType("groq")
    class _FakeGroq:
        def __init__(self, **kw): pass
    groq.Groq = _FakeGroq
    sys.modules["groq"] = groq
