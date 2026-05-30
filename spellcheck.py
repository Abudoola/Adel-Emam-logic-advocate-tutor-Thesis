"""
spellcheck.py
-------------
Lightweight pre-submission spell check for the Logic Advocate Tutor.

Uses pyspellchecker (offline, no network). Falls back to a no-op
implementation if the package is not installed so the rest of the app
keeps working.

The check is opt-in. The AI counter-argument prompt already tells the
LLM to ignore typos and move on. The pedagogical value of the spell
check is for the GRAPH VISUALISATION (the chat bubbles and the TikZ
export show the verbatim text), not for the AI's interpretation.
"""
from __future__ import annotations
import re
from typing import Dict, List, Tuple

try:
    from spellchecker import SpellChecker
    _SPELL = SpellChecker(language="en", distance=1)
    _AVAILABLE = True
except Exception:
    _SPELL = None
    _AVAILABLE = False


# Domain-specific words the engine talks about that the dictionary will
# otherwise flag. Keeping them in a whitelist saves the user from
# having to dismiss them every turn.
_DOMAIN_WHITELIST = {
    # technical terms
    "graphviz", "llm", "llms", "groq", "llama", "whisper", "tikz",
    "mdp", "dung", "wachsmuth", "prakken", "cayrol", "bench-capon",
    "amgoud", "besnard", "stamper", "rapanta", "macagno", "toulmin",
    # internal vocabulary
    "bipolar", "ethics", "emotion", "ethical", "logically", "rebut",
    "rebuttal", "undercut", "premise", "premises", "wifi",
}


def is_available() -> bool:
    """True if pyspellchecker is installed and the checker is ready."""
    return _AVAILABLE


def _is_word_token(tok: str) -> bool:
    return any(c.isalpha() for c in tok) and len(tok) >= 3


def _normalise(tok: str) -> str:
    return tok.lower().strip(".,!?;:()[]\"'")


def find_typos(text: str, max_typos: int = 8) -> List[Dict]:
    """
    Return a list of typo records:
        [{"word": str, "suggestions": [str, ...]}, ...]

    Stops after `max_typos` entries to keep the UI compact. Returns []
    if the spell checker is not available or the text is clean.
    """
    if not _AVAILABLE or not text.strip():
        return []

    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    candidates = []
    seen = set()
    for tok in tokens:
        norm = _normalise(tok)
        if not _is_word_token(norm) or norm in seen:
            continue
        seen.add(norm)
        if norm in _DOMAIN_WHITELIST:
            continue
        if _SPELL.unknown([norm]):
            sugs = list(_SPELL.candidates(norm) or [])
            sugs = [s for s in sugs if s != norm][:3]
            candidates.append({"word": tok, "suggestions": sugs})
            if len(candidates) >= max_typos:
                break
    return candidates


def apply_corrections(text: str, corrections: Dict[str, str]) -> str:
    """
    Replace each `bad_word -> good_word` mapping in `corrections`
    inside `text`. Whole-word substitution, case-sensitive.
    """
    out = text
    for bad, good in corrections.items():
        out = re.sub(rf"\b{re.escape(bad)}\b", good, out)
    return out
