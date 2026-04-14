# CAIN - Intelligent AI Agent with Personality, Memory and Tool Use

CAIN is an intelligent AI agent designed as a theatrical master of ceremonies, capable of maintaining context, remembering users, and interacting with real-world tools such as file systems.

This project goes beyond traditional chatbots by combining:
- Personality-driven interaction
- Persistent memory
- Intent-aware behavior
- Tool execution with decision-making

---

## Core Features

### Personality System
- Theatrical and expressive AI persona
- Context-aware tone adaptation:
  - Technical → clear and direct
  - Creative → expressive and immersive
- Dynamic response style control

---

### Memory System

**Short-Term Memory**
- Conversation history (sliding window)

**Long-Term Memory**
- User profile stored in JSON:
  - Name
  - Interests
  - Role (e.g. creator)

**Dynamic Memory**
- Automatic conversation summarization
- Context compression to avoid overload

---

### Intent & Action Detection

AI-powered classification of user input:

- conversation
- story
- challenge
- technical

AND tool-based actions:

- create_file
- read_file
- edit_file
- delete_file

---

### Tool System (Agent Capabilities)

CAIN can interact with the local environment:

- Create files
- Read files
- Edit files intelligently
- Delete files

---

### Intelligent File Editing

- Not just appending text
- Reads → understands → rewrites content
- Maintains coherence and structure
- Adapts content based on user intent

---

### Context Awareness

- Tracks the **last active file**
- Resolves implicit references:
  - "add more"
  - "modify that"
  - "continue"

---

### Semantic Validation (Advanced)

Before modifying a file, CAIN evaluates:

> “Does this action make sense for this file?”

- Prevents mixing unrelated topics
- Avoids logical inconsistencies
- Suggests better actions when needed

---

## Architecture Overview

CAIN is built using a modular architecture:

- Intent detection module (AI-based)
- Action detection system
- Memory system:
  - History
  - User profile
  - Summary memory
- Tool execution layer
- Prompt engineering system
- Context manager (`ultimo_archivo` logic)
- Semantic validation layer

---

## Tech Stack

- Python
- OpenAI API
- JSON (persistent storage)

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
- Autonomous behavior (proactive interaction)
- Voice integration (text-to-speech)
- Advanced memory (semantic / vector-based)
