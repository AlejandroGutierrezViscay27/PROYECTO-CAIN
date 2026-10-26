# Graph Report - PROYECTO-CAIN  (2026-09-03)

## Corpus Check
- 17 files · ~6,603 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 166 nodes · 232 edges · 12 communities
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4237873e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- app.js
- Cain
- CAIN - AI Agent with Personality and Memory
- executor.py
- agent.py
- memory.py
- intent.py
- tools.py

## God Nodes (most connected - your core abstractions)
1. `Cain` - 25 edges
2. `manejarMensaje()` - 11 edges
3. `cerrarModal()` - 9 edges
4. `LLMProvider` - 8 edges
5. `OpenAIProvider` - 8 edges
6. `agregarMensaje()` - 7 edges
7. `ejecutar_proyecto()` - 6 edges
8. `encontrar_puerto_libre()` - 5 edges
9. `OllamaProvider` - 5 edges
10. `conectar()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Cain` --uses--> `OpenAIProvider`  [INFERRED]
  core/agent.py → llm/openai_provider.py
- `modo_terminal()` --calls--> `Cain`  [EXTRACTED]
  main.py → core/agent.py
- `abrir_proyecto()` --calls--> `encontrar_puerto_libre()`  [EXTRACTED]
  web/app.py → core/executor.py
- `OllamaProvider` --inherits--> `LLMProvider`  [EXTRACTED]
  llm/ollama_provider.py → llm/base.py
- `OpenAIProvider` --inherits--> `LLMProvider`  [EXTRACTED]
  llm/openai_provider.py → llm/base.py

## Import Cycles
- None detected.

## Communities (12 total, 0 thin omitted)

### Community 0 - "app.js"
Cohesion: 0.15
Nodes (29): abrirProyecto(), actualizarMemoriaPanel(), agregarMensaje(), autoResize(), bloquearInput(), cargarMemoria(), cargarProyectos(), cerrarModal() (+21 more)

### Community 1 - "Cain"
Cohesion: 0.11
Nodes (9): Cain, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, Flujo completo con confirmación. - Modo terminal: usa input() clásico - Modo…, Intenta corregir el código automáticamente cuando hay un error. Máximo 2…, Procesa un mensaje del usuario y retorna la respuesta de CAIN., Le pide al LLM que genere el plan completo del proyecto: nombre + archivos con…, Genera una descripción legible del comando que se va a ejecutar., Maneja comandos explícitos de memoria: recordar, olvidar, consultar. (+1 more)

### Community 2 - "CAIN - AI Agent with Personality and Memory"
Cohesion: 0.33
Nodes (5): Architecture Overview, CAIN - AI Agent with Personality and Memory, Core Features, How to Run, Tech Stack

### Community 3 - "executor.py"
Cohesion: 0.10
Nodes (23): abrir_servidor_web(), detectar_tipo(), ejecutar_proyecto(), ejecutar_python(), encontrar_puerto_libre(), guardar_archivo_proyecto(), preparar_carpeta_proyecto(), Flujo completo: crea carpeta, guarda archivos, ejecuta y retorna resultado.… (+15 more)

### Community 4 - "agent.py"
Cohesion: 0.11
Nodes (12): ABC, construir_prompt(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, LLMProvider, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, OllamaProvider, Implementación de LLMProvider usando Ollama (modelo local). Para activarla,… (+4 more)

### Community 5 - "memory.py"
Cohesion: 0.11
Nodes (10): agregar_nota(), consultar_memoria(), limpiar_historial_completo(), olvidar_campo(), olvidar_nota(), Agrega una nota a la memoria del usuario si no existe ya., Elimina notas que contengan el fragmento dado., Elimina un campo específico del usuario (nombre, rol, intereses, notas). (+2 more)

### Community 6 - "intent.py"
Cohesion: 0.12
Nodes (16): detectar_accion_llm(), detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), detectar_tipo_proyecto_llm(), es_misma_intencion_archivo(), extraer_contenido_memoria() (+8 more)

### Community 7 - "tools.py"
Cohesion: 0.17
Nodes (8): evitar_sobrescritura(), extraer_nombre_archivo(), generar_nombre_timestamp(), Si el archivo ya existe, agrega sufijo numérico., Extrae un nombre de archivo .txt mencionado en el mensaje., Determina qué archivo usar: 1. Nombre explícito en el mensaje 2. Último archivo…, Nombre de fallback con timestamp si la IA no genera uno., resolver_archivo()

## Knowledge Gaps
- **10 isolated node(s):** `state`, `chatContainer`, `messageInput`, `sendBtn`, `statusDot` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 72 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `executor.py`, `agent.py`?**
  _High betweenness centrality (0.231) - this node is a cross-community bridge._
- **Why does `OpenAIProvider` connect `agent.py` to `Cain`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **What connects `state`, `chatContainer`, `messageInput` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `app.js` be split into smaller, more focused modules?**
  _Cohesion score 0.1471264367816092 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.11330049261083744 - nodes in this community are weakly interconnected._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10461538461538461 - nodes in this community are weakly interconnected._
- **Should `agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11067193675889328 - nodes in this community are weakly interconnected._