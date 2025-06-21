# NewsAI-Personalized-AI-Powered-Audio-News-Summarizer
 “Your daily AI-powered news podcast, generated on demand.”
---
NewsAI — a Personalized AI-Powered News & Reddit Audio Summarizer:

---

# 📰 NewsAI — Personalized AI News & Reddit Audio Summarizer

> Summarize. Synthesize. Speak.
> NewsAI delivers personalized audio briefings from real-time news & Reddit discussions using cutting-edge AI tools like Gemini, BrightData MCP, and ElevenLabs.

---

## 📌 Features

* 🔍 **News + Reddit Analysis** — Scrapes and analyzes news headlines and Reddit threads on user-defined topics.
* 🧠 **Smart Summarization** — Uses **Google Gemini Pro** to generate polished, spoken-style summaries.
* 🗣️ **Text-to-Speech** — Converts summaries to podcast-ready audio using **ElevenLabs TTS**.
* ⚙️ **Fully Automated Pipeline** — From topic input to audio output, all in a click.
* 🌐 **Web UI** — Built with **Streamlit** for a sleek user experience.

---

## 🛠️ Tech Stack

| Layer         | Tools & Libraries                               |
| ------------- | ----------------------------------------------- |
| 🖥 Frontend   | Streamlit (UI for input & summary control)      |
| 🔗 Backend    | FastAPI (API server), Python 3.11               |
| 🔎 Scraping   | BrightData MCP + LangGraph + Langchain Adapters |
| 🧠 LLM        | Google Gemini Pro (summarization)               |
| 🎙 TTS        | ElevenLabs API                                  |
| 🧹 Preprocess | BeautifulSoup, Custom headline extractor        |
| 🔐 Secrets    | dotenv (.env API key loading)                   |

---


## 🚀 How It Works

1. **User Input**: User enters topic(s) + data source (News, Reddit, or both) via Streamlit UI.
2. **Data Scraping**:

   * News is scraped via **Google News + BrightData MCP**.
   * Reddit is queried using **LangChain-MCP agents**.
3. **Data Cleaning**: Raw HTML is cleaned to plain text using BeautifulSoup.
4. **Summarization**:

   * Gemini Pro generates formal, TTS-friendly spoken summaries.
   * Reddit content is polished for audio narration.
5. **Text-to-Speech**:

   * Summaries are converted to `.mp3` using **ElevenLabs SDK**.
6. **Download**: Audio summary is returned via the browser.

---

## 🧪 Example Use Case

> 🎧 Imagine you're a busy entrepreneur.
> With **NewsAI**, just enter a topic like `AI innovation` and instantly get a podcast-style briefing from recent news and Reddit chatter — voiced professionally by ElevenLabs.

---

## 📂 Project Structure

```
📦NewsAI
├── frontend.py
├── backend.py
├── models.py
├── news_scraper.py
├── reddit_scraper.py
├── utils.py
├── .env
├── audio/
├── requirements.txt
└── README.md
```

---

## 🔑 Environment Variables (.env)

Create a `.env` file with the following:

```env
GEMINI_API_KEY=your_gemini_key
ELEVEN_API_KEY=your_elevenlabs_key
BRIGHTDATA_API_TOKEN=your_brightdata_token
API_TOKEN=your_mcp_api_token
WEB_UNLOCKER_ZONE=news_ai
```

---

## 📦 Installation & Running

```bash
# 1. Clone the repo
git clone https://github.com/your-username/NewsAI.git
cd NewsAI

# 2. Create & activate conda environment
conda create -n newsai-py311 python=3.11
conda activate newsai-py311

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run backend
python backend.py

# 5. In a new terminal, run frontend
streamlit run frontend.py
```

---

## ✅ Status

🟢 MVP Complete
🔜 Future Plans:

* Add voice selection UI
* Export as RSS podcast
* Add translation for multilingual audio
* Save summaries in a knowledge base

---

## 🤝 Contributors

* 💡 **Debanek Banarjee** — Developer, Data Scientist, AI Enthusiast
* 🙏 Inspired by modern journalism, podcasting, and GenAI tools.

---

## 📄 License

MIT License — use freely, contribute, and credit!





