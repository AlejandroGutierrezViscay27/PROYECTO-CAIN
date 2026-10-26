# Graph Report - PROYECTO-CAIN  (2026-09-07)

## Corpus Check
- 24 files · ~7,072 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 174 nodes · 200 edges · 19 communities (12 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8f0140fa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN - AI Agent with Personality and Memory
- app.py
- LLMProvider
- memory.py
- intent.py
- tools.py
- agent.py
- chat.js
- modal.js
- state.js
- websocket.js
- memoria.js

## God Nodes (most connected - your core abstractions)
1. `Cain` - 20 edges
2. `LLMProvider` - 9 edges
3. `OpenAIProvider` - 9 edges
4. `ejecutar_proyecto()` - 6 edges
5. `OllamaProvider` - 6 edges
6. `encontrar_puerto_libre()` - 5 edges
7. `cerrarModal()` - 5 edges
8. `CAIN - AI Agent with Personality and Memory` - 5 edges
9. `ejecutar_python()` - 4 edges
10. `abrir_servidor_web()` - 4 edges

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

## Communities (19 total, 2 thin omitted)

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

### Community 4 - "LLMProvider"
Cohesion: 0.10
Nodes (12): ABC, LLMProvider, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, OllamaProvider, Implementación de LLMProvider usando Ollama (modelo local). Para activarla,…, # TODO: Fase futura — migración a modelo local con Ollama (+4 more)

### Community 5 - "memory.py"
Cohesion: 0.11
Nodes (10): agregar_nota(), consultar_memoria(), limpiar_historial_completo(), olvidar_campo(), olvidar_nota(), Agrega una nota a la memoria del usuario si no existe ya., Elimina notas que contengan el fragmento dado., Elimina un campo específico del usuario (nombre, rol, intereses, notas). (+2 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.17
Nodes (6): evitar_sobrescritura(), generar_nombre_timestamp(), normalizar_nombre_txt(), Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna., Nombre de fallback con timestamp si la IA no genera uno.

### Community 12 - "agent.py"
Cohesion: 0.15
Nodes (9): construir_prompt(), generar_correccion_codigo(), generar_edicion_archivo(), generar_plan_proyecto(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, Pide al LLM el contenido completo actualizado de un archivo existente., Le pide al LLM que genere el plan completo del proyecto: nombre + archivos con…, Le pide al LLM que corrija código Python que falló al ejecutarse. (+1 more)

### Community 13 - "chat.js"
Cohesion: 0.27
Nodes (5): agregarMensaje(), autoResize(), formatearContenido(), mostrarTyping(), scrollAbajo()

### Community 14 - "modal.js"
Cohesion: 0.57
Nodes (6): cerrarModal(), escapeHtml(), mostrarModalCargando(), mostrarModalCodigo(), mostrarModalConfirmacion(), responderConfirmacion()

### Community 15 - "state.js"
Cohesion: 0.29
Nodes (6): chatContainer, messageInput, sendBtn, state, statusDot, statusText

## Knowledge Gaps
- **10 isolated node(s):** `state`, `chatContainer`, `messageInput`, `sendBtn`, `statusDot` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 90 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `app.py`, `agent.py`, `LLMProvider`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Why does `OpenAIProvider` connect `LLMProvider` to `Cain`, `agent.py`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **What connects `state`, `chatContainer`, `messageInput` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1437908496732026 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Should `LLMProvider` be split into smaller, more focused modules?**
  _Cohesion score 0.10144927536231885 - nodes in this community are weakly interconnected._
- **Should `memory.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._