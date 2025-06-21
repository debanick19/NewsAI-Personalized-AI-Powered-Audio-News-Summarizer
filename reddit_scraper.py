import os
import asyncio
from typing import List
from datetime import datetime, timedelta
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Time-based Reddit filter
two_weeks_ago = datetime.today() - timedelta(days=14)
two_weeks_ago_str = two_weeks_ago.strftime('%Y-%m-%d')

# BrightData MCP Setup
server_params = StdioServerParameters(
    command="npx",
    env={
        "API_TOKEN": os.getenv("API_TOKEN"),
        "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE")
    },
    args=["@brightdata/mcp"]
)

# Custom exception for retry logic
class MCPOverloadedError(Exception):
    pass

# Limit rate of MCP usage
mcp_limiter = AsyncLimiter(1, 15)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=15, max=60),
    retry=retry_if_exception_type(MCPOverloadedError),
    reraise=True
)
async def process_topic(agent, topic: str) -> str:
    async with mcp_limiter:
        messages = [
            {
                "role": "system",
                "content": f"""
You are a Reddit data gathering agent. Use MCP tools to find top 2 Reddit posts about '{topic}' posted AFTER {two_weeks_ago_str}.
Extract the post content and return key talking points, patterns, and sentiments.
"""
            },
            {
                "role": "user",
                "content": f"""
Summarize Reddit discussions on '{topic}' based on:
- Main themes and opinions
- Interesting comments (quoted, no usernames)
- Notable patterns or sentiments
- Use a spoken-news format (as if narrated on a podcast)
"""
            }
        ]

        try:
            # Get the content using LangGraph + MCP
            response = await agent.ainvoke({"messages": messages})
            raw_reddit_summary = response["messages"][-1].content

            # Use Gemini to polish it into a spoken-news format
            model = genai.GenerativeModel("gemini-pro")
            gemini_response = model.generate_content(
                f"""
You are a podcast narrator. Convert the following Reddit analysis into a polished, spoken-news style briefing:
- Make it smooth, clear, and voice-friendly
- No usernames, no formatting, no extra comments

{raw_reddit_summary}
""",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=800,
                    top_p=1.0,
                    top_k=1
                )
            )
            return gemini_response.text

        except Exception as e:
            if "Overloaded" in str(e):
                raise MCPOverloadedError("Service overloaded")
            else:
                raise

async def scrape_reddit_topics(topics: List[str]) -> dict:
    """Main function to orchestrate Reddit scraping + summarization"""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(None, tools)

            reddit_results = {}
            for topic in topics:
                try:
                    summary = await process_topic(agent, topic)
                    reddit_results[topic] = summary
                except Exception as e:
                    reddit_results[topic] = f"Error: {e}"
                await asyncio.sleep(5)

            return {"reddit_analysis": reddit_results}
