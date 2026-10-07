# 🥾 TrailQuest AI — Offline Outdoor Adventure Generator

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

---

## What I Built
**TrailQuest AI** is a lightweight, local-first web application that turns screen time into offline real-world outdoor adventures.

Instead of endlessly scrolling through social media or struggling to decide what to do outside, users pick their available time (e.g., 15–60 minutes), their desired outdoor vibe (*Mindful & Chill, Scavenger Hunt, Energetic Walk, or Photography*), and their immediate location setting. 

In under 10 seconds, **TrailQuest AI** generates a personalized, 3-step physical "Quest Card" with clear goals, observation challenges, and reflection prompts. Once generated, the screen experience ends and the user steps outside to "touch grass."

It is built for students, remote workers, and anyone looking to break screen fatigue without exposing their daily location habits to third-party cloud trackers.

---

## Demo
*(Include a screenshot or GIF of your Streamlit app running locally here)*

![TrailQuest AI App Screenshot](https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/trailquest-ai/main/screenshot.png)

> **Example Quest Output:**
> 1. **Route Goal:** Walk 15 minutes down your neighborhood street while looking for 3 different types of leaves.
> 2. **Observation Challenge:** Pause at a quiet spot for 60 seconds and identify 2 distinct nature sounds.
> 3. **Reflection Task:** Take 1 photo of the most interesting tree bark or shadow pattern you find before heading back.

---

## Code
{% github https://github.com/YOUR_GITHUB_USERNAME/trailquest-ai %}

---

## How I Built It
TrailQuest AI relies entirely on local open-source AI models and open-weight inference:

* **Frontend & UI:** Built using **Streamlit** in pure Python for a zero-boilerplate, clean web UI.
* **Local Inference Engine:** Powered by **Ollama**, running open-weight local models (`qwen2.5:3b` / `gemma:2b`) on consumer hardware.
* **Prompt Architecture:** Utilizes targeted role-prompting and constrained output formatting to ensure generated quests are immediate, concise, and focused on offline activities.

### Quickstart / Local Setup
1. **Ensure Ollama is installed and running:**
   ```bash
   ollama pull qwen2.5:3b# trailquest-ai
