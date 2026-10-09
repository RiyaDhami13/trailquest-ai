import streamlit as st
import ollama
import json
import time
import io
import sqlite3
import textwrap
from datetime import datetime, timedelta
from typing import Generator, Tuple, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TrailQuest AI — Offline Outdoor Adventure Generator",
    page_icon="🥾",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-mode aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    
    /* Stat Badge Metric Container */
    .stat-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
    }
    .stat-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .stat-val.streak { color: #f97316; }
    .stat-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    /* Badges */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    .badge {
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-local { background-color: #065f4625; color: #34d399; border: 1px solid #05966960; }
    .badge-stream { background-color: #1e40af25; color: #60a5fa; border: 1px solid #2563eb60; }
    .badge-pydantic { background-color: #5b21b625; color: #a78bfa; border: 1px solid #7c3aed60; }
    .badge-fallback { background-color: #92400e25; color: #fbbf24; border: 1px solid #d9770660; }

    /* Quest Card Layout */
    .quest-card {
        background: #111827;
        border-radius: 20px;
        border: 1px solid #1f2937;
        padding: 28px;
        margin-top: 20px;
        margin-bottom: 24px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .quest-brand-header {
        color: #38bdf8;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .quest-subtitle {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 14px;
    }
    .quest-header-divider {
        border-bottom: 1px solid #1f2937;
        margin-bottom: 18px;
    }
    .quest-main-title {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 20px;
        line-height: 1.25;
    }
    .step-box {
        background: #0b1120;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        border: 1.5px solid #38bdf8;
    }
    .step-box.goal { border-color: #38bdf8; }
    .step-box.observation { border-color: #34d399; }
    .step-box.reflection { border-color: #c084fc; }
    .step-box.safety { border-color: #fbbf24; }
    
    .step-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .label-goal { color: #38bdf8; }
    .label-observation { color: #34d399; }
    .label-reflection { color: #c084fc; }
    .label-safety { color: #fbbf24; }
    
    .step-text {
        font-size: 1rem;
        line-height: 1.5;
        color: #f1f5f9;
        margin: 0;
    }
    .quest-footer-divider {
        border-top: 1px solid #1f2937;
        margin-top: 24px;
        padding-top: 14px;
    }
    .quest-footer-meta {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }
    .quest-footer-sub {
        color: #38bdf8;
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "trailquest.db"

# -----------------------------------------------------------------------------
# 2. SQLite Database & Streak Analytics
# -----------------------------------------------------------------------------
def init_db():
    """Initializes local SQLite database for logging completed quests and streaks."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS completed_quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        goal TEXT,
        observation TEXT,
        reflection TEXT,
        safety_tip TEXT,
        duration INTEGER,
        vibe TEXT,
        location TEXT,
        weather TEXT,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_date TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def log_completed_quest(quest_dict: dict, meta_dict: dict) -> bool:
    """Logs a completed quest into SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO completed_quests 
        (title, goal, observation, reflection, safety_tip, duration, vibe, location, weather, completed_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quest_dict.get("title", "Outdoor Quest"),
            quest_dict.get("goal", ""),
            quest_dict.get("observation", ""),
            quest_dict.get("reflection", ""),
            quest_dict.get("safety_tip", ""),
            meta_dict.get("duration", 30),
            meta_dict.get("vibe", "General"),
            meta_dict.get("location", "Outdoors"),
            meta_dict.get("weather", "Clear"),
            today_str
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_streak_stats() -> Dict[str, Any]:
    """Calculates total quests, total outdoor minutes, and consecutive daily streak."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(duration), 0) FROM completed_quests")
        row = cursor.fetchone()
        total_quests = row[0] or 0
        total_minutes = row[1] or 0
        
        cursor.execute("SELECT DISTINCT completed_date FROM completed_quests ORDER BY completed_date DESC")
        dates = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT title, duration, vibe, completed_date FROM completed_quests ORDER BY id DESC LIMIT 10")
        recent_logs = cursor.fetchall()
        conn.close()

        if not dates:
            streak = 0
        else:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            latest_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
            
            if latest_date not in (today, yesterday):
                streak = 0
            else:
                streak = 1
                curr = latest_date
                for d_str in dates[1:]:
                    d_date = datetime.strptime(d_str, "%Y-%m-%d").date()
                    if d_date == curr - timedelta(days=1):
                        streak += 1
                        curr = d_date
                    elif d_date == curr:
                        continue
                    else:
                        break
        return {
            "total_quests": total_quests,
            "total_minutes": total_minutes,
            "streak_days": streak,
            "recent_logs": recent_logs
        }
    except Exception:
        return {"total_quests": 0, "total_minutes": 0, "streak_days": 0, "recent_logs": []}

init_db()


# -----------------------------------------------------------------------------
# 3. Pillow Graphic & Printable PDF Quest Card Generator
# -----------------------------------------------------------------------------
def generate_quest_card_files(
    title: str,
    goal: str,
    observation: str,
    reflection: str,
    safety_tip: str,
    duration: int,
    vibe: str,
    location: str,
    weather: str
) -> Tuple[bytes, bytes]:
    """Generates high-resolution PNG graphic card and printable PDF bytes using Pillow."""
    width, height = 800, 1000
    
    bg_color = (11, 15, 25)
    card_color = (30, 41, 59)
    border_color = (51, 65, 85)
    accent_blue = (56, 189, 248)
    accent_green = (52, 211, 153)
    accent_purple = (192, 132, 252)
    accent_gold = (251, 191, 36)
    text_white = (241, 245, 249)
    text_sub = (148, 163, 184)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Outer Card Container
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=24, fill=card_color, outline=border_color, width=3)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 24)
        font_label = ImageFont.truetype("arialbd.ttf", 15)
        font_body = ImageFont.truetype("arial.ttf", 17)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_header = font_title = font_label = font_body = font_sub = ImageFont.load_default()

    # Header
    draw.text((60, 55), "🥾 TRAILQUEST AI", font=font_header, fill=accent_blue)
    draw.text((60, 95), f"OFFLINE OUTDOOR QUEST CARD • {duration} MINS", font=font_sub, fill=text_sub)
    draw.line([60, 125, width - 60, 125], fill=border_color, width=2)

    # Title
    draw.text((60, 145), title[:45], font=font_title, fill=text_white)
    
    def draw_box(y_pos, label, color, text):
        b_left, b_top, b_right, b_height = 60, y_pos, width - 60, 145
        draw.rounded_rectangle([b_left, b_top, b_right, b_top + b_height], radius=12, fill=(15, 23, 42), outline=color, width=2)
        draw.text((b_left + 18, b_top + 12), label.upper(), font=font_label, fill=color)
        
        words = text.split()
        lines = []
        curr = []
        for w in words:
            curr.append(w)
            test_str = " ".join(curr)
            bbox = font_body.getbbox(test_str) if hasattr(font_body, "getbbox") else (0, 0, len(test_str)*10, 20)
            if bbox[2] > (b_right - b_left - 36):
                curr.pop()
                lines.append(" ".join(curr))
                curr = [w]
        if curr:
            lines.append(" ".join(curr))
            
        ly = b_top + 40
        for l in lines[:3]:
            draw.text((b_left + 18, ly), l, font=font_body, fill=text_white)
            ly += 24
        return b_top + b_height + 16

    y = 200
    y = draw_box(y, "🎯 STEP 1: ROUTE & GOAL", accent_blue, goal)
    y = draw_box(y, "👁️ STEP 2: OBSERVATION & MINDFULNESS", accent_green, observation)
    y = draw_box(y, "🧘 STEP 3: REFLECTION & PHOTO CHALLENGE", accent_purple, reflection)
    y = draw_box(y, "💡 SAFETY & TRAIL TIP", accent_gold, safety_tip)

    # Footer Metadata
    draw.line([60, height - 90, width - 60, height - 90], fill=border_color, width=2)
    footer_str = f"Setting: {location[:20]}  |  Vibe: {vibe[:20]}  |  Weather: {weather[:20]}"
    draw.text((60, height - 70), footer_str, font=font_sub, fill=text_sub)
    draw.text((60, height - 45), "Generated 100% locally by TrailQuest AI • 0 Egress", font=font_sub, fill=accent_blue)

    png_io = io.BytesIO()
    img.save(png_io, format="PNG")
    png_bytes = png_io.getvalue()

    pdf_io = io.BytesIO()
    img.save(pdf_io, format="PDF")
    pdf_bytes = pdf_io.getvalue()

    return png_bytes, pdf_bytes


# -----------------------------------------------------------------------------
# 4. Pydantic Structured Data Model
# -----------------------------------------------------------------------------
class OutdoorQuest(BaseModel):
    title: str = Field(
        description="A catchy, adventurous title for this quest card (e.g., 'The Whispering Pines Scavenger Run')"
    )
    goal: str = Field(
        description="Step 1 Goal: Clear physical walking route or target count (e.g., 'Walk for 15 minutes towards the park while spotting 3 green mailboxes')"
    )
    observation: str = Field(
        description="Step 2 Observation: Sensory mindfulness or focus task (e.g., 'Pause near a tree for 60 seconds; listen and identify 2 distinct bird calls')"
    )
    reflection: str = Field(
        description="Step 3 Reflection: Offline reflection or photo challenge (e.g., 'Take 1 photo of an intricate shadow pattern before returning home')"
    )
    safety_tip: str = Field(
        description="A friendly, concise outdoor tip (e.g., 'Watch for curb steps and stay hydrated')"
    )


import requests

# -----------------------------------------------------------------------------
# 5. Local Ollama Pipeline & Fallback Manager
# -----------------------------------------------------------------------------
def get_installed_ollama_models() -> List[str]:
    """Fetch list of locally available models in Ollama with a connection timeout."""
    try:
        # First verify server is responsive within 5 seconds to prevent cold-boot hangs
        res = requests.get("http://localhost:11434/api/tags", timeout=5)
        if res.status_code != 200:
            return []
        
        models_res = ollama.list()
        return [m.model for m in models_res.models if m.model is not None]
    except Exception:
        return []

def clean_json_string(raw_text: str) -> str:
    """Strips markdown code blocks or surrounding whitespace from JSON string."""
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    return text.strip()

def stream_quest_generation(
    prompt: str,
    primary_model: str,
    fallback_model: str
) -> Generator[Tuple[str, bool, str, Optional[OutdoorQuest]], None, None]:
    """Streams tokens from local Ollama model with schema constraint and automatic fallback."""
    installed = get_installed_ollama_models()
    if not installed:
        raise RuntimeError(
            "Ollama service is offline or unreachable. "
            "Please start Ollama by running `ollama serve` in your terminal."
        )

    candidates = [primary_model]
    if fallback_model and fallback_model not in candidates:
        candidates.append(fallback_model)
    for m in installed:
        if m not in candidates:
            candidates.append(m)

    schema = OutdoorQuest.model_json_schema()
    last_exception = None

    for idx, model_name in enumerate(candidates):
        is_fallback = (idx > 0)
        accumulated_text = ""
        
        try:
            response_stream = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                format=schema,
                stream=True
            )
            
            for chunk in response_stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    accumulated_text += token
                    yield (model_name, is_fallback, token, None)
            
            cleaned_json = clean_json_string(accumulated_text)
            quest_obj = OutdoorQuest.model_validate_json(cleaned_json)
            yield (model_name, is_fallback, "", quest_obj)
            return

        except Exception as err:
            last_exception = err
            warning_msg = f"\n⚠️ [Model '{model_name}' failed ({err}). Retrying with fallback model...]\n"
            yield (model_name, is_fallback, warning_msg, None)
            continue

    raise RuntimeError(
        f"All local models failed. Last error: {last_exception}. "
        "Please check that Ollama is running (`ollama serve`) and models are pulled."
    )


# -----------------------------------------------------------------------------
# 6. Session State Initialization
# -----------------------------------------------------------------------------
if "quest_history" not in st.session_state:
    st.session_state["quest_history"] = []
if "current_quest" not in st.session_state:
    st.session_state["current_quest"] = None
if "current_meta" not in st.session_state:
    st.session_state["current_meta"] = None
if "completion_status" not in st.session_state:
    st.session_state["completion_status"] = None


# -----------------------------------------------------------------------------
# 7. Sidebar Diagnostics & Streak Stats Widget
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🏆 Touch Grass Stats")
    stats = get_streak_stats()
    
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(textwrap.dedent(f"""
            <div class="stat-card">
                <div class="stat-val streak">🔥 {stats['streak_days']}</div>
                <div class="stat-label">Day Streak</div>
            </div>
        """), unsafe_allow_html=True)
    with sc2:
        st.markdown(textwrap.dedent(f"""
            <div class="stat-card">
                <div class="stat-val">🌲 {stats['total_quests']}</div>
                <div class="stat-label">Quests Done</div>
            </div>
        """), unsafe_allow_html=True)

    st.caption(f"⏱️ **Total Outdoor Time:** {stats['total_minutes']} minutes logged")
    
    st.divider()
    st.header("⚙️ Local AI Engine")
    
    installed_models = get_installed_ollama_models()
    if installed_models:
        st.success(f"🟢 Ollama Running ({len(installed_models)} model{'s' if len(installed_models)>1 else ''})")
    else:
        st.error("🔴 Ollama Offline or No Models Loaded")
        st.info("Start Ollama in terminal:\n`ollama serve`\n\nPull models:\n`ollama pull qwen2.5:3b`\n`ollama pull gemma:2b`")

    default_primary_idx = 0
    if "qwen2.5:3b" in installed_models:
        default_primary_idx = installed_models.index("qwen2.5:3b")
        
    primary_model = st.selectbox(
        "Primary Model",
        options=installed_models if installed_models else ["qwen2.5:3b"],
        index=default_primary_idx
    )
    
    fallback_options = [m for m in installed_models if m != primary_model] + ["gemma:2b", "llama3.2:3b", "llama3.2:1b"]
    fallback_options = list(dict.fromkeys(fallback_options))
    
    fallback_model = st.selectbox(
        "Fallback Model",
        options=fallback_options,
        index=0 if fallback_options else 0
    )

    st.divider()
    st.subheader("📜 Recent Completed Logs")
    if stats["recent_logs"]:
        for title, dur, v, dt in stats["recent_logs"][:5]:
            st.markdown(f"• **{title[:22]}...**  \n<small>{dt} | {dur} mins | {v}</small>", unsafe_allow_html=True)
    else:
        st.caption("No completed quests logged yet. Complete your first quest card to start your streak!")


# -----------------------------------------------------------------------------
# 8. Main UI Header & Inputs
# -----------------------------------------------------------------------------
st.title("🥾 TrailQuest AI")
st.subheader("Offline Outdoor Adventure Generator")

# Badges
st.markdown("""
<div class="badge-container">
    <span class="badge badge-local">🔒 100% Local & Offline</span>
    <span class="badge badge-stream">⚡ Real-Time Streaming</span>
    <span class="badge badge-pydantic">🎯 Pydantic Schema</span>
    <span class="badge badge-fallback">🛡️ Multi-Model Fallback</span>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "Break screen fatigue and step outside. "
    "TrailQuest AI generates structured physical quest cards running 100% locally on your machine."
)

st.divider()

# Input Form
col1, col2 = st.columns([1, 1])

with col1:
    duration = st.slider("⏱️ Available Time (minutes):", 10, 120, 30, step=10)
    difficulty = st.selectbox(
        "🎯 Challenge Level:",
        ["Casual Walker", "Curious Explorer", "Trail Master / Active"]
    )
    weather_condition = st.selectbox(
        "🌦️ Weather / Season Context:",
        [
            "☀️ Clear / Sunny Day",
            "🌧️ Rainy Day / Drizzle",
            "🍁 Autumn Foliage & Falling Leaves",
            "❄️ Snowy / Crisp Cold Winter",
            "🌸 Spring Bloom & Mild Breeze",
            "🌅 Golden Hour / Sunset Walk",
            "🌌 Night Sky & Stargazing",
            "🌤️ Overcast & Mild"
        ]
    )

with col2:
    vibe = st.selectbox(
        "🌿 Outdoor Vibe & Quest Type:",
        [
            "Mindful & Chill",
            "Explorer / Scavenger Hunt",
            "Energetic Walk / Jog",
            "Nature Photography",
            "Urban Wilderness",
            "Sunset / Twilight Walk",
            "Rainy Day Puddle & Sound Trek",
            "Fall Foliage & Bark Tracker",
            "Night Sky Observation",
            "Crisp Winter Stroll",
            "Spring Wildflower Hunt",
            "Summer Shade & Cooling Trek"
        ]
    )
    location_type = st.text_input("📍 Nearby Setting:", "local park & neighborhood street")

# Generation Action
if st.button("Generate Outdoor Quest 🚀", use_container_width=True, type="primary"):
    st.session_state["completion_status"] = None
    
    prompt = f"""
    You are an outdoor adventure guide encouraging people to spend time offline outdoors.
    Generate a fun 3-step physical challenge quest card for someone spending {duration} minutes in a {location_type}.
    Outdoor Vibe: {vibe}.
    Weather/Season Context: {weather_condition}.
    Difficulty Level: {difficulty}.

    You must populate all 5 JSON fields with concise, non-empty text:
    1. title: A catchy quest title incorporating the vibe and weather.
    2. goal: Step 1 Goal (Clear route rule or physical target count).
    3. observation: Step 2 Observation (Sensory mindfulness or observation task suited for {weather_condition}).
    4. reflection: Step 3 Reflection (Offline reflection or photo challenge).
    5. safety_tip: Friendly outdoor safety advice.
    """

    st.markdown("### ⚡ Live Token Stream")
    
    status_container = st.status("Connecting to local Ollama model...", expanded=True)
    stream_placeholder = status_container.empty()
    
    raw_stream_text = ""
    used_model_name = primary_model
    fallback_triggered = False
    generated_quest = None
    
    start_time = time.time()
    
    try:
        stream_gen = stream_quest_generation(prompt, primary_model, fallback_model)
        
        for active_model, is_fb, token_chunk, parsed_quest in stream_gen:
            used_model_name = active_model
            if is_fb:
                fallback_triggered = True
                status_container.update(
                    label=f"⚡ Fallback Strategy Active! Streaming with model `{active_model}`...",
                    state="running"
                )
            else:
                status_container.update(
                    label=f"⚡ Streaming tokens with primary model `{active_model}`...",
                    state="running"
                )

            if parsed_quest:
                generated_quest = parsed_quest
            elif token_chunk:
                raw_stream_text += token_chunk
                stream_placeholder.code(raw_stream_text, language="json")

        elapsed_time = round(time.time() - start_time, 2)

        if generated_quest:
            status_container.update(
                label=f"✅ Quest Generated in {elapsed_time}s using `{used_model_name}`" + (" (Fallback Model)" if fallback_triggered else ""),
                state="complete",
                expanded=False
            )
            
            meta_data = {
                "duration": duration,
                "vibe": vibe,
                "weather": weather_condition,
                "location": location_type,
                "model": used_model_name,
                "is_fallback": fallback_triggered,
                "time": elapsed_time
            }
            
            st.session_state["current_quest"] = generated_quest
            st.session_state["current_meta"] = meta_data
            
            st.session_state["quest_history"].append({
                "quest": generated_quest,
                "meta": meta_data
            })
            
            st.success("Your Outdoor Quest Card is Ready! Put your device away and step outside!")

    except Exception as e:
        status_container.update(label="❌ Generation Failed", state="error", expanded=True)
        st.error(f"Error during quest generation: {e}")


# -----------------------------------------------------------------------------
# 9. Render Interactive Quest Card UI & Exports
# -----------------------------------------------------------------------------
if st.session_state["current_quest"]:
    quest: OutdoorQuest = st.session_state["current_quest"]
    meta = st.session_state.get("current_meta", {})
    
    st.divider()
    
    if meta.get("is_fallback"):
        st.warning(
            f"⚡ **Fallback Strategy Triggered:** Primary model was unavailable or encountered an error. "
            f"Quest was successfully generated using fallback model `{meta.get('model')}`."
        )

    # Main Card Render matching Image 2
    duration_val = meta.get("duration", 30)
    location_val = meta.get("location", "local park & neighborhood")
    vibe_val = meta.get("vibe", "Mindful & Chill")
    weather_val = meta.get("weather", "Clear / Sunny Day")

    card_html = (
        f'<div class="quest-card">'
        f'<div class="quest-brand-header">🥾 TRAILQUEST AI</div>'
        f'<div class="quest-subtitle">OFFLINE OUTDOOR QUEST CARD • {duration_val} MINS</div>'
        f'<div class="quest-header-divider"></div>'
        f'<div class="quest-main-title">{quest.title}</div>'
        f'<div class="step-box goal">'
        f'<div class="step-label label-goal">🥾 STEP 1: ROUTE & GOAL</div>'
        f'<div class="step-text">{quest.goal}</div>'
        f'</div>'
        f'<div class="step-box observation">'
        f'<div class="step-label label-observation">👁️ STEP 2: OBSERVATION & MINDFULNESS</div>'
        f'<div class="step-text">{quest.observation}</div>'
        f'</div>'
        f'<div class="step-box reflection">'
        f'<div class="step-label label-reflection">🧘 STEP 3: REFLECTION & PHOTO CHALLENGE</div>'
        f'<div class="step-text">{quest.reflection}</div>'
        f'</div>'
        f'<div class="step-box safety">'
        f'<div class="step-label label-safety">💡 SAFETY & TRAIL TIP</div>'
        f'<div class="step-text">{quest.safety_tip}</div>'
        f'</div>'
        f'<div class="quest-footer-divider"></div>'
        f'<div class="quest-footer-meta">Setting: {location_val} | Vibe: {vibe_val} | Weather: {weather_val}</div>'
        f'<div class="quest-footer-sub">Generated 100% locally by TrailQuest AI • 0 Egress</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Completion Tracker Button
    st.markdown("---")
    if st.session_state.get("completion_status") == "logged":
        st.success("🎉 Quest Logged! Your 'Days Touched Grass' streak has been updated!")
    else:
        if st.button("Mark Quest as Completed & Log Streak 🔥", use_container_width=True, type="secondary"):
            success = log_completed_quest(quest.model_dump(), meta)
            if success:
                st.session_state["completion_status"] = "logged"
                st.rerun()

    # Printable & Downloadable Exports Section
    st.markdown("### 📥 Export & Print Quest Card")
    
    # Generate PNG and PDF files using Pillow
    png_bytes, pdf_bytes = generate_quest_card_files(
        title=quest.title,
        goal=quest.goal,
        observation=quest.observation,
        reflection=quest.reflection,
        safety_tip=quest.safety_tip,
        duration=meta.get("duration", 30),
        vibe=meta.get("vibe", "Outdoor"),
        location=meta.get("location", "Park"),
        weather=meta.get("weather", "Clear")
    )
    
    ec1, ec2, ec3, ec4 = st.columns(4)
    
    with ec1:
        st.download_button(
            label="🖼️ Card (.png)",
            data=png_bytes,
            file_name=f"trailquest_card_{int(time.time())}.png",
            mime="image/png",
            use_container_width=True
        )
    with ec2:
        st.download_button(
            label="🖨️ PDF (.pdf)",
            data=pdf_bytes,
            file_name=f"trailquest_card_{int(time.time())}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with ec3:
        quest_plain_text = f"""📜 OUTDOOR QUEST CARD: {quest.title}
--------------------------------------------------
🎯 Step 1 (Goal): {quest.goal}
👁️ Step 2 (Observation): {quest.observation}
🧘 Step 3 (Reflection): {quest.reflection}
💡 Safety Tip: {quest.safety_tip}
--------------------------------------------------
Duration: {meta.get('duration', 30)} mins | Setting: {meta.get('location', 'Outdoors')}
Generated 100% locally by TrailQuest AI ({meta.get('model', 'Ollama')})
"""
        st.download_button(
            label="📝 Text (.txt)",
            data=quest_plain_text,
            file_name=f"trailquest_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with ec4:
        st.download_button(
            label="📊 Data (.json)",
            data=quest.model_dump_json(indent=2),
            file_name=f"trailquest_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )

st.divider()
st.caption(
    "🔒 **Privacy & Offline Guarantee:** Runs 100% locally via Ollama. "
    "All quest history, streaks, and generated cards are stored locally in SQLite (`trailquest.db`) with zero external network calls."
)