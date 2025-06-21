from fastapi import FastAPI, HTTPException, Response
from pathlib import Path
from dotenv import load_dotenv
import os
import traceback

from models import NewsRequest
from utils import generate_broadcast_news_gemini, text_to_audio_elevenlabs_sdk
from news_scraper import NewsScraper  # Fixed: use the class
from reddit_scraper import scrape_reddit_topics

app = FastAPI()
load_dotenv()

@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        results = {}

        # Step 1: Scrape News (if requested)
        if request.source_type in ["news", "both"]:
            results["news"] = await NewsScraper.scrape_news(request.topics)

        # Step 2: Scrape Reddit (if requested)
        if request.source_type in ["reddit", "both"]:
            results["reddit"] = await scrape_reddit_topics(request.topics)

        news_data = results.get("news", {})
        reddit_data = results.get("reddit", {})

        # Step 3: Validate .env keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        eleven_key = os.getenv("ELEVEN_API_KEY")
        if not gemini_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        if not eleven_key:
            raise ValueError("Missing ELEVEN_API_KEY in .env")

        # Step 4: Generate spoken summary using Gemini
        summary_text = generate_broadcast_news_gemini(
            api_key=gemini_key,
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )

        # Step 5: Convert summary to audio using ElevenLabs
        audio_path = text_to_audio_elevenlabs_sdk(
            text=summary_text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Changeable
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            output_dir="audio"
        )

        # Step 6: Return audio response
        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=news-summary.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Audio file not generated.")

    except Exception as e:
        print("❌ ERROR OCCURRED:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=1234, reload=True)
