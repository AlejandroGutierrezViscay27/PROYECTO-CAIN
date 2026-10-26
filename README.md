# CAIN — AI Agent with Personality, Memory and Voice

CAIN is a Spanish-speaking personal AI agent with the persona of a theatrical
master of ceremonies. It remembers you, has moods, talks and listens, and acts
on its environment: it writes files and generates, runs and fixes real code
projects.

It is not a chatbot that answers questions. It understands context, remembers,
decides and acts — designed to behave more like a companion than a bot.

> Chatbot → Assistant → **Agent** → Intelligent System

---

## Features

**Conversation and personality**
- Master-of-ceremonies persona: theatrical and charismatic, but useful first.
- Intent detection (story, challenge, technical, conversation) adapts tone and depth.

**Three-layer memory**
- Short term: the last 30 messages.
- Profile: explicit user data (name, interests, notes).
- Long term, kept by a **memory director**: every 10 messages a background LLM
  pass rereads memory and conversation. Facts can only be appended or marked
  obsolete by index — the model never rewrites the list, so it can't silently
  forget. Notes are versioned; closed topics are archived, not deleted.
- Natural-language commands: *"recuerda que…"*, *"qué sabes de mí"*, *"olvida todo"*.
- Atomic JSON writes: an interrupted save never leaves a corrupt file.

**Tools (declarative function calling)**
- Create, read, edit and delete files, with coherence checks on edits.
- Generate web (HTML/CSS/JS, Three.js, Chart.js) or Python projects from a
  prompt, run them, and auto-fix errors (up to 2 retries).

**Mood**
- 10 emotions that decay over time (negative ones 3× faster).
- The model tags each reply with `[[animo: ...]]` — no extra LLM calls.
- Mood colors the reply, the 3D face and the voice prosody.

**Bidirectional local voice**
- Speech-to-text with faster-whisper and text-to-speech with Piper (es_MX),
  both on CPU — no external APIs.
- Push-to-talk or **hands-free** (energy VAD with an adaptive noise floor) and
  **barge-in**: talk over CAIN and it stops to listen.
- Voice replies are short and cleaned of emojis, markdown, code and URLs.

**The Face**
- Reactive 3D face in Three.js (simplex-noise deformed icosahedron with glow)
  showing CAIN's state live: idle, thinking, listening, executing, speaking —
  tinted by mood and pulsing with the real volume of its voice.

**One LLM per role**
- Conversation, router, intent, director and code can each use their own
  provider and model (OpenAI or local Ollama), set in `.env`.
- Usage log: calls, tokens and estimated cost per day, role and model.

---

## Tech Stack

| Area | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Uvicorn, WebSockets, Jinja2 |
| AI | OpenAI API (gpt-4o-mini by default), Ollama (llama3.1 / qwen2.5) |
| Voice | faster-whisper (small, CPU int8), Piper TTS |
| Frontend | Vanilla HTML/CSS/JS (no build step), Three.js |
| Tests | unittest |

---

## Architecture

```
PROYECTO-CAIN/
├── core/       agent (orchestrator), memory, memory director, mood,
│               intent, tools + JSON tool schemas, prompts, project executor
├── llm/        LLMProvider interface, OpenAI/Ollama providers,
│               per-role factory, usage log
├── voice/      SpeechToText/TextToSpeech interfaces, faster-whisper,
│               Piper / HTTP TTS, text cleanup for speech
├── web/        FastAPI app, templates and static JS (chat, voice, face…)
├── tests/      unittest suite (never touches real user data)
└── main.py     entry point (web or terminal)
```

Each swappable subsystem (LLM, STT, TTS) follows the same pattern: an abstract
interface in `base.py` plus concrete implementations chosen via environment
variables. CAIN never talks to OpenAI or Ollama directly — only to
`LLMProvider` — so changing models touches `.env`, not code.

**How a turn works**
1. The **router** decides via function calling whether the message needs a tool.
2. **Intent** classifies the message and extracts interests.
3. **Conversation** replies with a prompt built from profile, long-term memory,
   channel (text or voice) and current mood.
4. Every 10 messages the **director** updates long-term memory in a background thread.

---

## How to Run

```bash
git clone https://github.com/AlejandroGutierrezViscay27/PROYECTO-CAIN.git
cd PROYECTO-CAIN
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Piper voice (needed for speech)
python -m piper.download_voices --download-dir data/voices es_MX-claude-high
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here

# Optional: per-role provider/model (LLM_PROVIDER_<ROLE>, LLM_MODEL_<ROLE>)
# Roles: CONVERSACION, ENRUTADOR, INTENCION, DIRECTOR, CODIGO
# LLM_PROVIDER_DIRECTOR=ollama
# LLM_MODEL_DIRECTOR=qwen2.5:7b
# OLLAMA_URL=http://localhost:11434/v1
```

Run it:

```bash
python main.py              # web UI at http://localhost:8000
python main.py terminal     # terminal mode
```

Run the tests:

```bash
python -m unittest discover -s tests -t .
```

---

## Roadmap

- [x] 1 — Conversational base and personality
- [x] 2 — Memory
- [x] 3 — File tools
- [x] 4 — Code generation and execution
- [x] 5 — Web interface
- [x] 6 — Declarative tool system (function calling)
- [x] 7 — Bidirectional local voice
- [x] 8 — The Face (reactive 3D HUD)
- [x] 8.5 — OpenSakura-inspired upgrades: hands-free voice, memory director, mood, one LLM per role
- [ ] 9 — CAIN as a service across the local network
- [ ] 10 — Operating system control
- [ ] 11 — Advanced memory (ChromaDB, semantic recall)
- [ ] 12 — Proactivity
- [ ] 13 — Fully local model with Ollama
- [ ] 14 — Home automation (Home Assistant)

---

Created by **Alejandro Gutierrez Viscay** — Systems Engineering, UCEVA, Tuluá, Colombia.
