# CAIN - AI Agent with Personality and Memory

CAIN is a personal AI agent designed to simulate a theatrical master of ceremonies with persistent memory, contextual understanding, and adaptive interaction.

This project explores the design of intelligent agents beyond simple chatbots, focusing on personality, memory, and user context.

---

##  Core Features

 **Personality System**
  - Theatrical, creative AI inspired by a master of ceremonies
  - Context-aware tone adjustment (technical vs creative)

 **Memory System**
  - Short-term memory (conversation history)
  - Long-term user memory (name, interests, role)
  - Dynamic memory summarization

 **Intent Detection**
  - AI-powered classification:
    - conversation
    - story
    - challenge
    - technical

 **Interest Extraction**
  - Detects user preferences using AI
  - Builds a persistent user profile

 **Contextual Interaction**
  - Uses user memory to personalize responses
  - Maintains conversational coherence

---

## Tech Stack

- Python
- OpenAI API
- JSON (persistent memory storage)

---

## Architecture Overview

CAIN is built using a modular approach:

- Intent detection module
- Memory system (history + summary)
- User profiling (name, interests, role)
- Prompt engineering layer
- Conversational engine

---

## How to Run

1. Clone the repository:
git clone https://github.com/tu_usuario/PROYECTO-CAIN.git
cd PROYECTO-CAIN

2. Install dependecies:
pip install openai

3. pip install openai:
setx OPENAI_API_KEY "your_api_key_here"

4. Run the project:
phyton cain.py

Future Improvements
- Tool system (file creation, automation)
- Autonomous behavior (proactive interaction)
- Voice integration (text-to-speech)
- Advanced memory (semantic / vector-based)

Future Improvements
- Tool system (file creation, automation)
- Autonomous behavior (proactive interaction)
- Voice integration (text-to-speech)
- Advanced memory (semantic / vector-based)
