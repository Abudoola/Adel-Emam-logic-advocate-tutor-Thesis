"""
ROLE: BACKEND (AI Layer)
DESCRIPTION: Handles interactions with the Gemini LLM for generating counter-arguments.
"""
import google.generativeai as genai
import streamlit as st
import time
from PIL import Image

# The API key must be configured before using the model.
genai.configure(api_key=st.secrets["GEMINI_API_KEY"]) 
llm_model = genai.GenerativeModel('gemini-2.5-flash')

def generate_counter_argument(messages, latest_text, uploaded_file=None, saved_media_path=None, media_type=None):
    transcript = ""
    for m in messages:
        transcript += f"{m['side']}: {m['content']}\n"
        if "media_path" in m:
            transcript += f"*[Attached Media Evidence]*\n"

    prompt = f"""
    We are in a debate. Here is the transcript of our debate so far:
    {transcript}
    
    My latest argument is: '{latest_text}'. 
    Evaluate my latest argument (and any attached visual evidence) strictly within the context of what we have been discussing.
    
    If my logic is completely sound, irrefutable, or effectively ends the debate, you MUST output exactly: 0|CONCEDE.
    If my logic has flaws, provide a concise counter-argument in 1 or 2 sentences, and rate the logical strength of your counter on a scale of 1 to 25.
    Format: Score|Your counter argument text here.
    """
    
    ai_request_payload = [prompt]
    
    if uploaded_file and saved_media_path and media_type:
        if media_type.startswith("image"):
            img_evidence = Image.open(saved_media_path)
            ai_request_payload.append(img_evidence)
        elif media_type.startswith("video"):
            video_evidence = genai.upload_file(saved_media_path)
            while video_evidence.state.name == "PROCESSING":
                time.sleep(2)
                video_evidence = genai.get_file(video_evidence.name)
            ai_request_payload.append(video_evidence)

    response = llm_model.generate_content(ai_request_payload)
    
    llm_response_parts = response.text.split("|")
    llm_weight = int(llm_response_parts[0].strip()) 
    llm_text = llm_response_parts[1].strip()        
    
    return llm_weight, llm_text
