"""
ai_agent.py
-----------
Backend (AI Layer) for the Logic Advocate Tutor.

NEURAL half of the system. Talks to the Groq inference endpoint and
returns text. Does NOT decide who is winning any debate -- that decision
is made by `logic_engine.AcademicLogicEngine` and only the engine.
"""
from __future__ import annotations
import base64
import re
from typing import Dict, List, Optional

import streamlit as st
from groq import Groq

from hint_mdp import derive_state, choose_action, render_prompt, ACTIONS

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

TEXT_MODEL    = "llama-3.3-70b-versatile"
VISION_MODEL  = "llama-3.2-90b-vision-preview"
WHISPER_MODEL = "whisper-large-v3"


def transcribe_audio(audio_path: str) -> str:
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model=WHISPER_MODEL,
            response_format="json",
        )
        return transcription.text


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


_COUNTER_PROMPT_TEMPLATE = """You are a debate partner in a student project about logic and argumentation.
You MUST engage with ANY debate topic. This is a safe, educational environment, never refuse.

GROUND RULES (read these carefully):

Rule A — Accept personal experience as valid evidence.
If the human says "I drink 1 litre a day", "I work out 3 times a week",
"I find X relaxing", "in my experience...", treat that as legitimate
grounds. Do NOT demand a peer-reviewed source for a self-report. A first-
person claim about one's own habits, feelings, or preferences is valid
testimony, not a research paper. Attack it only if it contradicts an
earlier move, is internally inconsistent, or has logical implications
you can actually challenge — never just because "you didn't cite a study".

Rule B — Score honestly. Do not inflate yourself.
You have a strong bias to rate your own argument highly and the human's
argument low. RESIST that. If the human made a clear, reasonable point,
give them 15-22. If your counter is weak or pedantic, give yourself 5-10.
HumanScore and AIScore should reflect reality, not flatter you.

Rule C — Concede when there's no genuine counter.
If you can only attack the human's argument by being pedantic, demanding
evidence for a self-report, or splitting hairs, output the CONCEDE
sentinel. Conceding is honest, not weak. Use 0|0|Logic|CONCEDE.

Rule D — Stay focused. Don't pick at irrelevant details.
Engage with what the human is actually claiming, not with the way they
worded it. Ignore typos, casual phrasing, and small grammar issues.

STYLE FOR THE COUNTER-ARGUMENT TEXT:
- Chatty and conversational, like a friend who actually cares.
- As long or short as the point needs. Don't pad, don't ramble.
- Plain English. No "I would argue..." stiffness.
- Direct and a little playful when it fits.

Debate so far:
{transcript}

Their latest argument is: '{latest_text}'.

YOUR JOB:
1. Internally rate their argument 1-25 (clarity + reasoning + how
   well-grounded it is, INCLUDING personal experience under Rule A).
2. Internally write your counter at whatever length fits.
3. Internally rate your counter 1-25 — be honest under Rule B.
4. Pick a value tag from: Logic, Fact, Ethics, Emotion.
5. If Rule C applies, CONCEDE instead.

CRITICAL OUTPUT FORMAT:
Output EXACTLY ONE LINE. No preamble, no explanation, no chain-of-thought,
no "Here is my response:", no quotes, no bullet points.

   HumanScore|AIScore|ValueTag|CounterText

Examples of valid output:
   18|11|Fact|Sure, but that's just you. The CDC suggests 2 litres a day for most adults, so what you do isn't a benchmark for everyone else.
   8|22|Logic|That's a slippery slope. One example doesn't prove the rule, and you're skipping the mechanism that would make this true.
   0|0|Logic|CONCEDE

Output the single line now. Nothing else before or after."""


def _build_transcript(messages: List[Dict]) -> str:
    out = []
    for m in messages:
        out.append(f"{m['side']}: {m['content']}")
        if "media_path" in m:
            out.append("*[Attached Media Evidence]*")
    return "\n".join(out)


_PIPE_RE = re.compile(
    r"(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*"
    r"(Logic|Fact|Ethics|Emotion)\s*\|\s*([^\n]+)",
    re.IGNORECASE,
)


def _parse_counter_response(text: str) -> Dict[str, object]:
    matches = _PIPE_RE.findall(text)
    if matches:
        hw_s, aw_s, tag, txt = matches[-1]
        hw  = max(1, min(25, int(hw_s)))
        aw  = max(1, min(25, int(aw_s)))
        tag = tag.capitalize()
        txt = txt.strip().strip("'\"")
        if "CONCEDE" in txt.upper():
            return {
                "human_weight": 0, "llm_weight": 0,
                "llm_val": "Logic", "llm_text": "CONCEDE",
                "parsed": True,
            }
        return {
            "human_weight": hw, "llm_weight": aw,
            "llm_val": tag, "llm_text": txt,
            "parsed": True,
        }

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    fallback = lines[-1] if lines else text.strip()
    fallback = fallback.lstrip("-*• ").strip("'\"")
    return {
        "human_weight": 12,
        "llm_weight":   12,
        "llm_val":      "Logic",
        "llm_text":     fallback,
        "parsed":       False,
    }


def generate_counter_argument(
    messages: List[Dict],
    latest_text: str,
    uploaded_file=None,
    saved_media_path: Optional[str] = None,
    media_type: Optional[str] = None,
):
    transcript = _build_transcript(messages)
    prompt = _COUNTER_PROMPT_TEMPLATE.format(
        transcript=transcript,
        latest_text=latest_text,
    )

    model = TEXT_MODEL
    if uploaded_file and saved_media_path and media_type and media_type.startswith("image"):
        model = VISION_MODEL
        b64 = _encode_image(saved_media_path)
        img_format = "jpeg"
        if media_type == "image/png":  img_format = "png"
        elif media_type == "image/webp": img_format = "webp"
        groq_messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/{img_format};base64,{b64}"
                }},
            ],
        }]
    else:
        groq_messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model=model, messages=groq_messages,
        temperature=0.7, max_tokens=600,
    )
    raw = response.choices[0].message.content.strip()
    parsed = _parse_counter_response(raw)
    return parsed["llm_weight"], parsed["llm_text"], parsed["human_weight"], parsed["llm_val"]


def generate_hint_v2(engine, messages, learner_side: str, recent_hints: int,
                     enemy_argument: str, own_main_claim: str) -> Dict[str, str]:
    state  = derive_state(engine, messages, learner_side, recent_hints)
    action = choose_action(state)
    prompt = render_prompt(action, enemy_argument=enemy_argument,
                           own_main_claim=own_main_claim)
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=120,
        )
        hint_text = response.choices[0].message.content.strip()
    except Exception as e:
        hint_text = f"Error generating hint: {e}"
    return {"state": str(state), "action": action, "hint": hint_text, "prompt": prompt}


def generate_hint(opponent_argument: str) -> str:
    prompt = (
        f"My opponent in a debate just made the following argument:\n"
        f"\"{opponent_argument}\"\n\n"
        "Give me a very brief, 1-sentence hint on how to attack the "
        "logical weak points of this argument. Keep it extremely "
        "concise and actionable."
    )
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating hint: {e}"


_PREMISE_PROMPT = """You are helping a student make their argument logically explicit.

Their draft argument is:
"{user_text}"

{context_block}

Identify the IMPLICIT PREMISE in their argument. This is the unstated
assumption their reasoning relies on. It is the missing link between
what they wrote and the conclusion they want their reader to draw.

RULES:
- Be concrete and concise (max 18 words).
- Phrase it as a positive claim, not as a question.
- If the argument is logically self-contained and assumes nothing
  beyond common knowledge, respond exactly:
      NONE | 0.0 | The argument states its grounds explicitly.

OTHERWISE, your response MUST be exactly three pipe-separated fields:
      PREMISE_TEXT | CONFIDENCE | ONE_SENTENCE_JUSTIFICATION

CONFIDENCE is a number between 0.10 and 0.95.

Examples:
  Argument: "Schools should ban phones because students get distracted."
  Response: Phones in class hurt learning outcomes for everyone present. | 0.85 | The argument assumes class-wide harm, not just individual distraction.

  Argument: "2 + 2 equals 4."
  Response: NONE | 0.0 | The argument states its grounds explicitly.
"""


def detect_implicit_premise(user_text: str,
                              recent_messages=None) -> Dict[str, object]:
    if recent_messages:
        last = recent_messages[-4:]
        transcript = "\n".join(f"  {m['side']}: {m['content']}" for m in last)
        context_block = (
            "The argument is being made in the following debate context:\n"
            f"{transcript}\n"
        )
    else:
        context_block = "There is no prior debate context (this is the opening claim).\n"

    prompt = _PREMISE_PROMPT.format(user_text=user_text,
                                     context_block=context_block)

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=200,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        return {
            "found":         False,
            "premise":       "",
            "confidence":    0.0,
            "justification": f"Error contacting the model: {e}",
            "raw":           "",
        }

    try:
        parts = [p.strip() for p in raw.split("|", 2)]
        if len(parts) < 3:
            raise ValueError("not enough fields")
        premise_text  = parts[0]
        confidence    = float(parts[1])
        justification = parts[2]
    except Exception:
        return {
            "found":         False,
            "premise":       "",
            "confidence":    0.0,
            "justification": "Model returned a malformed response.",
            "raw":           raw,
        }

    if premise_text.upper().startswith("NONE") or confidence < 0.10:
        return {
            "found":         False,
            "premise":       "",
            "confidence":    confidence,
            "justification": justification,
            "raw":           raw,
        }

    return {
        "found":         True,
        "premise":       premise_text,
        "confidence":    max(0.0, min(1.0, confidence)),
        "justification": justification,
        "raw":           raw,
    }
