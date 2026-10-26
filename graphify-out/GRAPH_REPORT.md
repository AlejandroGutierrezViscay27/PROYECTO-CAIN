# Graph Report - PROYECTO-CAIN  (2026-10-26)

## Corpus Check
- 40 files · ~19,398 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 412 nodes · 585 edges · 32 communities (20 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `47341707`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN - AI Agent with Personality and Memory
- test_emocion.py
- test_llm_roles.py
- memory.py
- intent.py
- tools.py
- agent.py
- CAIN
- test_director.py
- voice.js
- modal.js
- state.js
- websocket.js
- memoria.js
- app.py
- face.js
- EstadoEmocional
- HiloSincrono
- limpiar_para_voz
- parametros_prosodia
- consultar_memoria
- TestDirectorEnElAgente
- LLMFalso
- TestAplicarResultado
- TestPersistencia
- agregar_nota

## God Nodes (most connected - your core abstractions)
1. `Cain` - 24 edges
2. `RegistroUso` - 15 edges
3. `OpenAIProvider` - 13 edges
4. `limpiar_para_voz()` - 13 edges
5. `EstadoEmocional` - 10 edges
6. `TestLimpiarParaVoz` - 10 edges
7. `extraer_animo()` - 9 edges
8. `TestConfigRol` - 9 edges
9. `TestEstadoEmocional` - 8 edges
10. `TestRegistroUso` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Cain` --uses--> `RegistroUso`  [INFERRED]
  core/agent.py → llm/registro.py
- `modo_terminal()` --calls--> `Cain`  [EXTRACTED]
  main.py → core/agent.py
- `TestEstadoEmocional` --uses--> `EstadoEmocional`  [INFERRED]
  tests/test_emocion.py → core/emocion.py
- `TestConfigRol` --uses--> `OllamaProvider`  [INFERRED]
  tests/test_llm_roles.py → llm/ollama_provider.py
- `TestRegistroUso` --uses--> `OpenAIProvider`  [INFERRED]
  tests/test_llm_roles.py → llm/openai_provider.py

## Import Cycles
- None detected.

## Communities (32 total, 8 thin omitted)

### Community 0 - "executor.py"
Cohesion: 0.09
Nodes (26): abrir_servidor_web(), corregir_y_reintentar(), describir_comando(), detectar_tipo(), ejecutar_proyecto(), ejecutar_python(), encontrar_puerto_libre(), guardar_archivo_proyecto() (+18 more)

### Community 1 - "Cain"
Cohesion: 0.10
Nodes (7): Cain, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, Flujo completo con confirmación. - Modo terminal: usa input() clásico - Modo…, Copia lo que necesita la pasada. Se llama con _lock_memoria tomado., Borra historial y memoria a largo plazo (no el perfil explícito)., Procesa un mensaje del usuario y retorna la respuesta de CAIN. canal: "texto" o…, modo_terminal()

### Community 2 - "CAIN - AI Agent with Personality and Memory"
Cohesion: 0.33
Nodes (5): Architecture Overview, CAIN - AI Agent with Personality and Memory, Core Features, How to Run, Tech Stack

### Community 3 - "test_emocion.py"
Cohesion: 0.09
Nodes (19): aplicar_resultado(), bloque_para_prompt(), _formatear_conversacion(), _formatear_hechos(), _formatear_perfil(), _lista_de_textos(), llamar_director(), parsear_json() (+11 more)

### Community 4 - "test_llm_roles.py"
Cohesion: 0.06
Nodes (25): LLMProvider, ABC, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, config_rol(), crear_llms(), _env() (+17 more)

### Community 5 - "memory.py"
Cohesion: 0.20
Nodes (13): _cargar_json(), cargar_memoria(), cargar_memoria_larga(), cargar_usuario(), _escribir_atomico(), _guardar_json(), guardar_memoria(), guardar_memoria_larga() (+5 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.17
Nodes (6): evitar_sobrescritura(), generar_nombre_timestamp(), normalizar_nombre_txt(), Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna., Nombre de fallback con timestamp si la IA no genera uno.

### Community 11 - "CAIN"
Cohesion: 0.25
Nodes (7): CAIN, Comandos, Convenciones, Cómo funciona un turno, Estructura, Pruebas, Stack

### Community 12 - "test_director.py"
Cohesion: 0.18
Nodes (8): construir_prompt(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, mismo_llm_para_todos(), Sustituto de crear_llms(): una sola instancia de prueba para todos los roles., BaseAgente, TestCanalVoz, TestDirectorEnSegundoPlano, TestParsearJson

### Community 13 - "voice.js"
Cohesion: 0.14
Nodes (17): agregarMensaje(), autoResize(), formatearContenido(), mostrarTyping(), scrollAbajo(), abrirMicrofono(), alternarManosLibres(), cainHablando() (+9 more)

### Community 14 - "modal.js"
Cohesion: 0.57
Nodes (6): cerrarModal(), escapeHtml(), mostrarModalCargando(), mostrarModalCodigo(), mostrarModalConfirmacion(), responderConfirmacion()

### Community 15 - "state.js"
Cohesion: 0.22
Nodes (8): chatContainer, messageInput, micBtn, sendBtn, state, statusDot, statusText, vadBtn

### Community 19 - "app.py"
Cohesion: 0.07
Nodes (28): get, Request, hacer_wav(), TestWavAMuestras, ABC, Transcribe audio a texto. Args: audio_bytes: Audio crudo (cualquier contenedor…, Interfaz común para cualquier motor de síntesis de voz. Cualquier motor que…, Sintetiza texto a audio. Args: texto: Texto a convertir en habla. emocion:… (+20 more)

### Community 21 - "face.js"
Cohesion: 0.22
Nodes (12): ajustarTamanoFace(), animarFace(), crearTexturaGlow(), FACE_EMOCIONES, FACE_ESTADOS_CON_EMOCION, FACE_PRESETS, faceCurrent, faceEmocion (+4 more)

### Community 22 - "EstadoEmocional"
Cohesion: 0.12
Nodes (6): EstadoEmocional, Texto corto del ánimo actual para el prompt de sistema., Un turno de conversación: desvanece las emociones que no aparecen en deltas,…, (emocion, intensidad) de la emoción más fuerte, o ("neutral", 0.0)., Reloj, TestEstadoEmocional

### Community 23 - "HiloSincrono"
Cohesion: 0.14
Nodes (5): HiloSincrono, Sustituto de threading.Thread que corre el target en el momento., LLMDeRol, LLM de prueba que apunta qué rol recibió cada llamada., TestRutasEnElAgente

### Community 24 - "limpiar_para_voz"
Cohesion: 0.25
Nodes (3): TestLimpiarParaVoz, limpiar_para_voz(), Convierte una respuesta pensada para el chat en texto apto para TTS. Quita…

### Community 25 - "parametros_prosodia"
Cohesion: 0.24
Nodes (5): TestProsodia, _curva_s(), parametros_prosodia(), Sigmoide normalizada a [0, 1] (como la de OpenSakura): las emociones suaves…, Mezcla la prosodia neutral con la de la emoción según su intensidad.

### Community 26 - "consultar_memoria"
Cohesion: 0.20
Nodes (6): consultar_memoria(), limpiar_historial_completo(), olvidar_nota(), Elimina notas que contengan el fragmento dado., Borra el historial de conversación y la memoria a largo plazo., Genera un resumen legible de todo lo que CAIN sabe del usuario.

## Knowledge Gaps
- **25 isolated node(s):** `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION`, `faceCurrent`, `faceEmocion` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 186 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `agent.py`, `app.py`, `test_llm_roles.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `RegistroUso` connect `test_llm_roles.py` to `Cain`, `agent.py`, `memory.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `limpiar_para_voz()` connect `limpiar_para_voz` to `app.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `RegistroUso` (e.g. with `Cain` and `TestConfigRol`) actually correct?**
  _`RegistroUso` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08620689655172414 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.09846153846153846 - nodes in this community are weakly interconnected._