"""
ROLE: BACKEND (AI Layer)
DESCRIPTION: Handles interactions with the Groq LLM for generating counter-arguments.
"""
import streamlit as st
import base64
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model="whisper-large-v3",
            response_format="json"
        )
        return transcription.text

def generate_counter_argument(messages, latest_text, saved_media_path=None, media_type=None):
    transcript = ""
    for m in messages:
        transcript += f"{m['side']}: {m['content']}\n"
        if "media_path" in m:
            transcript += "*[Attached Media Evidence]*\n"

    system_message = (
        "You are a fierce, witty, and highly logical debate opponent. "
        "Challenge arguments with logic, counter-examples, and sharp reasoning. "
        "Never lazily dismiss arguments — always engage with the substance directly."
    )

    prompt = f"""Here is the transcript of our debate so far:
{transcript}

The user's latest argument is: '{latest_text}'.

Your task:
1. Rate the logical strength of the user's argument on a scale of 1 to 25.
2. If the user's logic is completely sound and irrefutable, output exactly: user_score|0|CONCEDE
3. Otherwise, provide a punchy 1-2 sentence counter-argument and rate its logical strength 1 to 25.

Output format MUST be exactly: user_score|your_score|Your counter argument text here.
Example: 18|14|Your premise assumes X but ignores Y, which fundamentally undermines the claim.
"""

    model = 'llama-3.3-70b-versatile'
    user_content = prompt

    if saved_media_path and media_type and media_type.startswith("image"):
        model = 'llama-3.2-90b-vision-preview'
        img_format = "jpeg"
        if media_type == "image/png":
            img_format = "png"
        elif media_type == "image/webp":
            img_format = "webp"
        base64_image = encode_image(saved_media_path)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/{img_format};base64,{base64_image}"}}
        ]

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
        max_tokens=1024
    )

    response_text = response.choices[0].message.content.strip()

    try:
        parts = response_text.split("|", 2)
        user_weight = max(1, min(25, int(parts[0].strip())))
        llm_weight = max(0, min(25, int(parts[1].strip())))
        llm_text = parts[2].strip()
    except Exception:
        user_weight = 10
        llm_weight = 10
        llm_text = response_text

    if llm_text.upper() == "CONCEDE":
        return user_weight, 0, "CONCEDE"

    return user_weight, llm_weight, llm_text
