# 🥾 TrailQuest AI — Offline Outdoor Adventure Generator

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

---

## What I Built
**TrailQuest AI** is a lightweight, local-first web application that turns screen time into offline real-world outdoor adventures.

Instead of endlessly scrolling through social media or struggling to decide what to do outside, users pick their available time (e.g., 10–120 minutes), their desired outdoor vibe (*Mindful & Chill, Scavenger Hunt, Energetic Walk, Nature Photography, Rainy Day Walks, Fall Foliage Tracker, Night Sky Observation, etc.*), weather/season setting, and immediate location. 

In seconds, **TrailQuest AI** generates a personalized, 3-step physical "Quest Card" with clear goals, observation challenges, reflection prompts, and safety tips. Once generated, the screen experience ends and the user steps outside to "touch grass."

It is built for students, remote workers, and anyone looking to break screen fatigue without exposing their daily location habits to third-party cloud trackers.

---

## Key Features & Production Highlights

* 🖼️ **Printable & Exportable Graphic Quest Cards:** 1-click export of generated quest cards as high-resolution PNG graphic cards (for smartphone screen reference) or clean printable PDFs.
* 🔥 **Offline Streak & Journal Analytics:** Local SQLite storage (`trailquest.db`) logs completed quests, tracks daily "Days Touched Grass" streaks, and logs total outdoor minutes without cloud tracking.
* 🌦️ **Dynamic Seasonal & Weather-Aware Quests:** Specialized vibes and environmental prompts for Rainy Day Walks, Autumn Foliage Tracking, Night Sky Stargazing, Crisp Winter Strolls, and Spring Bloom Hunts.
* ⚡ **Real-Time Token Streaming:** Tokens stream character-by-character directly in Streamlit so quest cards appear live during inference instead of blocking.
* 🛡️ **Automatic Fallback Strategy:** Production-grade model resilience that seamlessly falls back to secondary local models (e.g., from `qwen2.5:3b` to `gemma:2b` or other installed models) if the primary model is un-loaded or fails.
* 🎯 **Pydantic Structured JSON Output:** Utilizes Pydantic V2 schemas with Ollama format constraints to guarantee strict `[Goal, Observation, Reflection]` task structure every time.
* 🔒 **100% Offline & Pure Python:** Zero cloud API dependencies and zero third-party data egress.

---

## Demo

![TrailQuest AI App Screenshot](https://github.com/RiyaDhami13/trailquest-ai/blob/main/screenshot.PNG)

> **Example Quest Output:**
> 1. **Route Goal:** Walk 15 minutes down your neighborhood street while looking for 3 different types of leaves.
> 2. **Observation Challenge:** Pause at a quiet spot for 60 seconds and identify 2 distinct nature sounds.
> 3. **Reflection Task:** Take 1 photo of the most interesting tree bark or shadow pattern you find before heading back.
> 4. **Safety Tip:** Stay alert near crosswalks and keep hydrated.

---

## Architecture & Code

* `app.py`: Main Streamlit web application with token streaming, model fallback handler, Pydantic schema validation, Pillow card generator, SQLite streak tracker, and styled UI.
* `requirements.txt`: Pure-Python dependencies (`streamlit`, `ollama`, `pydantic`, `pillow`, `pandas`).

---

## Quickstart / Local Setup

1. **Ensure Ollama is installed and running:**
   ```bash
   ollama serve
   ```

2. **Pull local models:**
   ```bash
   ollama pull qwen2.5:3b
   ollama pull gemma:2b
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the web application:**
   ```bash
   streamlit run app.py
   ```
