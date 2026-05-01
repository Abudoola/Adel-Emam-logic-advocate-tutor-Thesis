"""
ROLE: BACKEND (AI Layer)
DESCRIPTION: Handles interactions with the Groq LLM for generating counter-arguments.
"""
import streamlit as st
import base64
from groq import Groq

# Initialize Groq client
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

def generate_counter_argument(messages, latest_text, uploaded_file=None, saved_media_path=None, media_type=None):
    transcript = ""
    for m in messages:
        transcript += f"{m['side']}: {m['content']}\n"
        if "media_path" in m:
            transcript += f"*[Attached Media Evidence]*\n"

    prompt = f"""
    You are a fierce, witty, and highly logical debate opponent. We are currently engaged in a debate.
    Here is the transcript of our debate so far:
    {transcript}
    
    My latest argument is: '{latest_text}'. 
    
    Your goal is to engage in a meaningful debate. 
    State your own reasoning clearly and present a strong perspective, but also actively challenge and attack my points. 
    DO NOT lazily say "you lack evidence" or "this is unsubstantiated". Instead, offer your own logic, point out absurdities in my argument, bring up counter-examples, and challenge the premises directly. Be engaging, logically rigorous, and combative when necessary.
    
    If my logic is completely sound, irrefutable, or effectively ends the debate, you MUST output exactly: 0|CONCEDE.
    Otherwise, provide a punchy, concise counter-argument in 1 or 2 sentences, and rate the logical strength of your counter on a scale of 1 to 25.
    Format MUST be exactly: Score|Your counter argument text here.
    """
    
    groq_messages = []
    
    # Default to text model
    model = 'llama-3.3-70b-versatile'
    
    if uploaded_file and saved_media_path and media_type and media_type.startswith("image"):
        # Switch to vision model
        model = 'llama-3.2-90b-vision-preview'
        base64_image = encode_image(saved_media_path)
        
        # Determine image format
        img_format = "jpeg"
        if media_type == "image/png":
            img_format = "png"
        elif media_type == "image/webp":
            img_format = "webp"
            
        groq_messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/{img_format};base64,{base64_image}"}}
            ]
        })
    else:
        # Text only request
        groq_messages.append({
            "role": "user",
            "content": prompt
        })

    response = client.chat.completions.create(
        model=model,
        messages=groq_messages,
        temperature=0.7,
        max_tokens=1024
    )
    
    response_text = response.choices[0].message.content.strip()
    
    try:
        llm_response_parts = response_text.split("|")
        llm_weight = int(llm_response_parts[0].strip()) 
        llm_text = llm_response_parts[1].strip()        
    except Exception:
        llm_weight = 10
        llm_text = response_text
        
    return llm_weight, llm_text
