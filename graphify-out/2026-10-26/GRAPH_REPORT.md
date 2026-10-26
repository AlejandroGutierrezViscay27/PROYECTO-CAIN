# Graph Report - PROYECTO-CAIN  (2026-09-15)

## Corpus Check
- 30 files · ~9,704 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 221 nodes · 262 edges · 22 communities (15 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `054877a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN - AI Agent with Personality and Memory
- app.py
- agent.py
- memory.py
- intent.py
- tools.py
- CAIN
- prompts.py
- chat.js
- modal.js
- state.js
- websocket.js
- memoria.js
- TextToSpeech
- face.js

## God Nodes (most connected - your core abstractions)
1. `Cain` - 20 edges
2. `LLMProvider` - 9 edges
3. `OpenAIProvider` - 9 edges
4. `TextToSpeech` - 8 edges
5. `ejecutar_proyecto()` - 6 edges
6. `OllamaProvider` - 6 edges
7. `SpeechToText` - 6 edges
8. `FasterWhisperSTT` - 6 edges
9. `PiperTTS` - 6 edges
10. `APITTS` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Cain` --uses--> `OpenAIProvider`  [INFERRED]
  core/agent.py → llm/openai_provider.py
- `modo_terminal()` --calls--> `Cain`  [EXTRACTED]
  main.py → core/agent.py
- `abrir_proyecto()` --calls--> `encontrar_puerto_libre()`  [EXTRACTED]
  web/app.py → core/executor.py
- `corregir_y_reintentar()` --calls--> `generar_correccion_codigo()`  [EXTRACTED]
  core/executor.py → core/prompts.py
- `OllamaProvider` --inherits--> `LLMProvider`  [EXTRACTED]
  llm/ollama_provider.py → llm/base.py

## Import Cycles
- None detected.

## Communities (22 total, 2 thin omitted)

### Community 0 - "executor.py"
Cohesion: 0.14
Nodes (16): abrir_servidor_web(), corregir_y_reintentar(), describir_comando(), detectar_tipo(), ejecutar_proyecto(), ejecutar_python(), guardar_archivo_proyecto(), preparar_carpeta_proyecto() (+8 more)

### Community 1 - "Cain"
Cohesion: 0.13
Nodes (5): Cain, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, Flujo completo con confirmación. - Modo terminal: usa input() clásico - Modo…, Procesa un mensaje del usuario y retorna la respuesta de CAIN., modo_terminal()

### Community 2 - "CAIN - AI Agent with Personality and Memory"
Cohesion: 0.33
Nodes (5): Architecture Overview, CAIN - AI Agent with Personality and Memory, Core Features, How to Run, Tech Stack

### Community 3 - "app.py"
Cohesion: 0.21
Nodes (11): encontrar_puerto_libre(), Busca el primer puerto disponible en el rango dado., get, post, Request, abrir_proyecto(), get_memory(), get_proyectos() (+3 more)

### Community 4 - "agent.py"
Cohesion: 0.09
Nodes (13): Declaraciones JSON de las herramientas de CAIN (Fase 6). Cada entrada sigue el…, LLMProvider, ABC, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, OllamaProvider, Implementación de LLMProvider usando Ollama (modelo local). Para activarla,… (+5 more)

### Community 5 - "memory.py"
Cohesion: 0.11
Nodes (10): agregar_nota(), consultar_memoria(), limpiar_historial_completo(), olvidar_campo(), olvidar_nota(), Agrega una nota a la memoria del usuario si no existe ya., Elimina notas que contengan el fragmento dado., Elimina un campo específico del usuario (nombre, rol, intereses, notas). (+2 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.17
Nodes (6): evitar_sobrescritura(), generar_nombre_timestamp(), normalizar_nombre_txt(), Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna., Nombre de fallback con timestamp si la IA no genera uno.

### Community 11 - "CAIN"
Cohesion: 0.33
Nodes (5): CAIN, Comandos, Convenciones, Estructura, Stack

### Community 12 - "prompts.py"
Cohesion: 0.20
Nodes (8): construir_prompt(), generar_correccion_codigo(), generar_edicion_archivo(), generar_plan_proyecto(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, Pide al LLM el contenido completo actualizado de un archivo existente., Le pide al LLM que genere el plan completo del proyecto: nombre + archivos con…, Le pide al LLM que corrija código Python que falló al ejecutarse.

### Community 13 - "chat.js"
Cohesion: 0.16
Nodes (8): agregarMensaje(), autoResize(), formatearContenido(), mostrarTyping(), scrollAbajo(), audioChunks, detenerGrabacion(), iniciarGrabacion()

### Community 14 - "modal.js"
Cohesion: 0.57
Nodes (6): cerrarModal(), escapeHtml(), mostrarModalCargando(), mostrarModalCodigo(), mostrarModalConfirmacion(), responderConfirmacion()

### Community 15 - "state.js"
Cohesion: 0.25
Nodes (7): chatContainer, messageInput, micBtn, sendBtn, state, statusDot, statusText

### Community 19 - "TextToSpeech"
Cohesion: 0.11
Nodes (15): ABC, Transcribe audio a texto. Args: audio_bytes: Audio crudo (cualquier contenedor…, Interfaz común para cualquier motor de síntesis de voz. Cualquier motor que…, Sintetiza texto a audio. Args: texto: Texto a convertir en habla. Returns:…, Interfaz común para cualquier motor de reconocimiento de voz. Cualquier motor…, SpeechToText, TextToSpeech, FasterWhisperSTT (+7 more)

### Community 21 - "face.js"
Cohesion: 0.36
Nodes (6): ajustarTamanoFace(), animarFace(), crearTexturaGlow(), FACE_PRESETS, faceCurrent, initFace()

## Knowledge Gaps
- **18 isolated node(s):** `FACE_PRESETS`, `faceCurrent`, `state`, `chatContainer`, `messageInput` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 115 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `app.py`, `agent.py`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `OpenAIProvider` connect `agent.py` to `Cain`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **What connects `FACE_PRESETS`, `faceCurrent`, `state` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1437908496732026 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09116809116809117 - nodes in this community are weakly interconnected._
- **Should `memory.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._