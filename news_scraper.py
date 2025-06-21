import os
import asyncio
from typing import Dict, List
from dotenv import load_dotenv

from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

import google.generativeai as genai

from utils import (
    generate_news_urls_to_scrape,
    scrape_with_brightdata,
    clean_html_to_text,
    extract_headlines
)

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# MCP server configuration
server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("API_TOKEN"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
    },
    args=["@brightdata/mcp"]
)

scraper_limiter = AsyncLimiter(5, 1)  # 5 requests per second


class MCPOverloadedError(Exception):
    """Custom exception to handle Bright Data API overloads."""
    pass


class NewsScraper:
    """Handles scraping and summarization of news topics."""

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(MCPOverloadedError),
        reraise=True
    )
    async def _process_news_topic(agent, topic: str) -> str:
        async with scraper_limiter:
            try:
                urls = generate_news_urls_to_scrape([topic])
                html = scrape_with_brightdata(urls[topic])
                cleaned_text = clean_html_to_text(html)
                headlines = extract_headlines(cleaned_text)

                prompt = f"""
You are a news summarization expert. Summarize the following headlines into a spoken-news format script.

Important Notes:
- This script will be converted into audio for a podcast.
- Use formal, clear, and fluent language like a news anchor.
- Avoid emojis, symbols, markdown, and special characters.
- Do not include any headings, bullet points, or introductory phrases.
- Get straight to the news.

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

            except Exception as e:
                if "Overloaded" in str(e):
                    raise MCPOverloadedError("Bright Data MCP overloaded.")
                else:
                    raise

    @staticmethod
    async def scrape_news(topics: List[str]) -> Dict[str, str]:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                agent = create_react_agent(None, tools)

                results = {}
                for topic in topics:
                    try:
                        summary = await NewsScraper._process_news_topic(agent, topic)
                        results[topic] = summary
                    except Exception as e:
                        results[topic] = f"Error: {e}"
                    await asyncio.sleep(1)

                return {"news_analysis": results}
