import os
from urllib.parse import quote_plus
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from elevenlabs import ElevenLabs
from gtts import gTTS
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Output folder for audio
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)


# === NEWS URL + SCRAPING UTILITIES ===

def generate_valid_news_url(keyword: str) -> str:
    q = quote_plus(keyword)
    return f"https://news.google.com/search?q={q}&tbs=sbd:1"

def generate_news_urls_to_scrape(keywords):
    return {kw: generate_valid_news_url(kw) for kw in keywords}

def scrape_with_brightdata(url: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "zone": os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'),
        "url": url,
        "format": "raw"
    }
    try:
        response = requests.post("https://api.brightdata.com/request", json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"BrightData error: {e}")


# === TEXT CLEANING & HEADLINE EXTRACTION ===

def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n").strip()

def extract_headlines(text: str) -> str:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    headlines, current_block = [], []
    for line in lines:
        if line == "More":
            if current_block:
                headlines.append(current_block[0])
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        headlines.append(current_block[0])
    return "\n".join(headlines)


# === GEMINI SUMMARIZATION FOR HEADLINES ===

def summarize_with_gemini_news_script(headlines: str) -> str:
    prompt = f"""
You are an expert news editor. Summarize the following headlines into a formal, spoken TV news script.

⚠️ Important: This text will be converted to audio by a text-to-speech engine.
So:
- No emojis, symbols, markdown, or formatting
- No headings or lists
- Use full, grammatically correct sentences
- Formal tone, like a professional news anchor
- Start directly with the news — no preamble

Headlines:
{headlines}

News Script:
"""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=800,
            top_p=1.0,
            top_k=1
        )
    )
    return response.text


# === GEMINI COMBINED BROADCAST SCRIPT ===

def generate_broadcast_news_gemini(news_data, reddit_data, topics):
    model = genai.GenerativeModel("gemini-pro")
    topic_blocks = []
    for topic in topics:
        news = news_data.get("news_analysis", {}).get(topic, "")
        reddit = reddit_data.get("reddit_analysis", {}).get(topic, "")
        context = ""
        if news:
            context += f"OFFICIAL NEWS:\n{news}\n"
        if reddit:
            context += f"REDDIT OPINIONS:\n{reddit}"
        if context:
            topic_blocks.append(f"TOPIC: {topic}\n{context}")
    
    if not topic_blocks:
        return ""

    prompt = """
You are a virtual news broadcaster. Using the content provided for each topic, generate a spoken-news script optimized for a podcast.

Guidelines:
- Start directly with the news (no introductions or headings)
- Use full, clear sentences and natural transitions
- Maintain a neutral, professional tone
- Mention Reddit opinions where available with phrasing like “Reddit users believe...”
- End each topic block with a short wrap-up sentence

Avoid:
- Emojis, markdown, or formatting
- Any usernames or Reddit-specific jargon

Topics:
""" + "\n\n--- NEW TOPIC ---\n\n".join(topic_blocks)

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=1000,
            top_p=1.0,
            top_k=1
        )
    )
    return response.text


# === TEXT TO SPEECH (TTS) CONVERSION ===

def text_to_audio_elevenlabs_sdk(
    text: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    output_dir: str = "audio",
    api_key: str = None
) -> str:
    try:
        api_key = api_key or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key missing")

        client = ElevenLabs(api_key=api_key)
        stream = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format
        )

        os.makedirs(output_dir, exist_ok=True)
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            for chunk in stream:
                f.write(chunk)

        return filepath
    except Exception as e:
        raise e


def tts_to_audio(text: str, language: str = 'en') -> str:
    try:
        filename = AUDIO_DIR / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        gTTS(text=text, lang=language, slow=False).save(str(filename))
        return str(filename)
    except Exception as e:
        print(f"gTTS Error: {e}")
        return None
