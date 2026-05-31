import os
import base64
import requests
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
STABILITY_KEY = os.getenv("STABILITY_API_KEY")

client = Groq(api_key=GROQ_KEY)

st.set_page_config(page_title="AI Notes + Image Generator", layout="wide")
# Session history
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.title("History")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history[::-1]):
        if st.sidebar.button(item["topic"], key=f"hist_{i}"):
            st.session_state.selected = item

if st.sidebar.button("Clear History"):
    st.session_state.history = []
    st.session_state.selected = None

# Main UI
st.title("AI Notes + Image Generator")

topic = st.text_input("Enter Topic")
generate_img = st.checkbox("Generate Image also")

if st.button("Generate"):
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        # -------------------- NOTES GENERATION --------------------
        with st.spinner("Generating notes using Groq..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": f"Generate detailed notes on: {topic}"}
                ]
            )
            notes = response.choices[0].message.content

        image_data = None

        # -------------------- IMAGE GENERATION --------------------
        if generate_img:
            with st.spinner("Generating image using Stability AI..."):

                url = "https://api.stability.ai/v2beta/stable-image/generate/core"

                # MUST be multipart/form-data
                files = {
                    "prompt": (None, topic),
                    "mode": (None, "text-to-image"),
                    "output_format": (None, "png"),
                }

                headers = {
                    "Authorization": f"Bearer {STABILITY_KEY}",
                    "Accept": "application/json",
                }

                response = requests.post(url, headers=headers, files=files)

                if response.status_code != 200:
                    st.error("Image generation failed:")
                    st.code(response.text)
                else:
                    data = response.json()

                    if "image" not in data:
                        st.error("Image key missing from API response.")
                        st.code(data)
                    else:
                        image_data = base64.b64decode(data["image"])

        # Save to history
        entry = {
            "topic": topic,
            "notes": notes,
            "image": image_data
        }
        st.session_state.history.append(entry)
        st.session_state.selected = entry

# ------------ DISPLAY SELECTED ------------
if "selected" in st.session_state and st.session_state.selected:
    st.subheader(st.session_state.selected["topic"])
    st.write(st.session_state.selected["notes"])

    if st.session_state.selected["image"]:
        st.image(st.session_state.selected["image"], caption="Generated Image")
