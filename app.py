import streamlit as st
import ollama

st.set_page_config(page_title="TrailQuest AI", page_icon="🥾", layout="centered")

st.title("🥾 TrailQuest AI")
st.subheader("Offline Outdoor Adventure Generator")

st.markdown(
    "Get off your screen and explore the outdoors! "
    "Powered by local, open-source AI running 100% on your device."
)

st.divider()

# Inputs
duration = st.slider("How much time do you have? (minutes)", 10, 120, 30, step=10)
vibe = st.selectbox(
    "Choose your outdoor vibe:",
    ["Mindful & Chill", "Explorer / Scavenger Hunt", "Energetic Walk / Jog", "Nature Photography"]
)
location_type = st.text_input("Nearby setting (e.g., city street, local park, neighborhood):", "neighborhood street")

if st.button("Generate Outdoor Quest 🚀"):
    with st.spinner("Asking local AI to generate your quest..."):
        prompt = f"""
        You are an outdoor adventure guide encouraging people to touch grass and spend time offline.
        Create a short, fun, 3-step physical challenge card for a person spending {duration} minutes outdoors in a {location_type}.
        Their goal vibe is: {vibe}.
        
        Keep rules simple:
        1. A clear goal or route rule (e.g., 'walk until you spot 3 green items').
        2. A mindfulness or observation task (e.g., 'stop and listen for 2 distinct bird sounds').
        3. A quick photo/reflection challenge.
        
        Keep the text punchy, concise, and inspiring.
        """
        
        try:
            response = ollama.chat(
                model="qwen2.5:3b",
                messages=[{"role": "user", "content": prompt}]
            )
            
            quest_text = response['message']['content']
            
            st.success("Your Quest is Ready! Put your PC away and head outside!")
            st.markdown("### 📜 Your Outdoor Quest Card")
            st.info(quest_text)
            
        except Exception as e:
            st.error(f"Error connecting to Ollama: {e}. Make sure Ollama is running in the background!")

st.divider()
st.caption("🔒 Privacy Note: Runs locally via Ollama. No location data or personal queries ever leave your machine.")