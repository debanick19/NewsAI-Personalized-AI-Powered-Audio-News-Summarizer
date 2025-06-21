import streamlit as st
import requests
from typing import Literal

SOURCE_TYPES = Literal["news", "reddit", "both"]
BACKEND_URL = "http://localhost:1234"

def main(): 
    st.title("🗞️ NewsAI")
    st.markdown("#### 🎙️ Personalized AI News & Reddit Audio Summarizer")

    if 'topics' not in st.session_state:
        st.session_state.topics = []
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0

    with st.sidebar:
        st.header("Settings")
        source_type = st.selectbox("Data Sources", options=["both", "news", "reddit"])

    st.markdown("##### 📝 Add Topic")
    col1, col2 = st.columns([4, 1])
    with col1:
        new_topic = st.text_input("Enter a topic", key=f"topic_input_{st.session_state.input_key}")
    with col2:
        if st.button("Add ➕", disabled=not new_topic.strip()):
            st.session_state.topics.append(new_topic.strip())
            st.session_state.input_key += 1
            st.rerun()

    if st.session_state.topics:
        st.subheader("✅ Selected Topics")
        for i, topic in enumerate(st.session_state.topics[:3]):
            cols = st.columns([4, 1])
            cols[0].write(f"{i+1}. {topic}")
            if cols[1].button("Remove ❌", key=f"remove_{i}"):
                del st.session_state.topics[i]
                st.rerun()

    st.markdown("---")
    st.subheader("🔊 Generate Audio Summary")

    if st.button("🚀 Generate", disabled=len(st.session_state.topics) == 0):
        with st.spinner("Processing..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate-news-audio",
                    json={"topics": st.session_state.topics, "source_type": source_type}
                )
                if response.status_code == 200:
                    st.audio(response.content, format="audio/mpeg")
                    st.download_button("⬇️ Download MP3", data=response.content, file_name="summary.mp3")
                else:
                    st.error("API Error")
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
