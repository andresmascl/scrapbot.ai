# scrapbot.ai

**scrapbot** is an open-source, local, Linux-based voice assistant designed to behave like a personal Alexa-style system — but **fully under your control**.

It combines **Rhasspy** for offline voice processing and **Playwright** for controlling a **real, headful browser with your personal user session**, enabling voice-driven interaction with services like YouTube, Gmail, and local applications.

scrapbot is intentionally minimal, explicit, and hackable.

---

## What scrapbot Does (Today)

- Runs **locally on Linux** (PC, NUC, or laptop)
- Listens for a wake word: **"scrapbot"**
- Converts voice → text using Rhasspy
- Translates voice intents into actions
- Controls a **real browser window** (Brave / Chrome / Firefox)
  - Headful (visible)
  - Persistent user profile (your real login, cookies, sessions)
- Automates websites like:
  - YouTube (search, play, navigate)
  - Gmail (read / open emails — WIP)

Everything runs on your machine. No cloud dependency is required.

---

## What scrapbot Explicitly Does NOT Do

- ❌ No hidden automation behind APIs you don’t control
- ❌ No smart-home vendor lock-in
- ❌ No attempt to replace full Alexa / Google Assistant ecosystems

scrapbot.io is **not** a consumer product. It is a **personal automation platform**.

---

## Supported Platform

- **OS:** Linux (primary target)
- **Architecture:** x86_64
- **Browsers:**
  - Brave
  - Google Chrome
  - Firefox
- **Python:** 3.10+

---

## High-Level Architecture

```
Voice (Mic)
   ↓
Rhasspy
   ↓  (intent)
stt
   ↓
intent detection
   ↓
return json
   ↓
tts
   ↓
Browser Controller (Playwright)
   ↓
Website App (YouTube, Gmail, etc.)
```

Rhasspy is treated as a **black-box voice frontend**.
Browser apps are **browser-agnostic** and operate on Playwright pages.

---

## Project Structure

The project is structured around clear separation of concerns:

- `assist/` → Voice & intent extraction (Rhasspy)
- `browser/` → Browser control and website automation
- `browser/apps/` → Website-specific logic (YouTube, Gmail, …)
- `browser/apps/test/` → Headful Playwright tests

See [`PROJECT_STRUCTURE.md`](./PROJECT_STRUCTURE.md) for the full architectural breakdown.

---

## Running Alekz (Happy Path)

> This describes the *intended* usage flow. Setup scripts may evolve.

1. Start Rhasspy
2. Start scrapbot services
3. Say:
   
   **“scrapbot, play lo-fi music on YouTube”**

4. A real browser window opens
5. YouTube loads using your logged-in account
6. The requested video starts playing

---

## Design Principles

- **Local-first** — works without internet (except for websites)
- **User-owned sessions** — real browser, real account
- **Headful automation** — visible, debuggable, honest
- **Explicit over magical** — no hidden behavior
- **Composable** — voice, browser, and apps are decoupled

---

## Current Status

⚠️ Early-stage / experimental

- Architecture is stable
- APIs and behavior may change
- Focus is on correctness, not polish

---

## License

Open-source. License to be defined.

---

## Who This Is For

- Developers
- Tinkerers
- Linux users
- People who want voice control **without giving up control**

If you’re looking for convenience, buy an Alexa.
If you’re looking for ownership, build Scrapbot.ai.