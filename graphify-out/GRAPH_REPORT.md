# Graph Report - PROYECTO-CAIN  (2026-10-26)

## Corpus Check
- 43 files · ~23,248 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 504 nodes · 709 edges · 26 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0341a335`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN — AI Agent with Personality, Memory and Voice
- director.py
- agent.py
- memory.py
- intent.py
- tools.py
- test_servicio.py
- CAIN
- test_director.py
- voice.js
- modal.js
- state.js
- websocket.js
- app.py
- test_emocion.py
- face.js
- EstadoEmocional
- HiloSincrono
- limpiar_para_voz
- acceso.py

## God Nodes (most connected - your core abstractions)
1. `Cain` - 24 edges
2. `RegistroUso` - 15 edges
3. `OpenAIProvider` - 13 edges
4. `limpiar_para_voz()` - 13 edges
5. `extraer_animo()` - 11 edges
6. `EstadoEmocional` - 10 edges
7. `TestLimpiarParaVoz` - 10 edges
8. `TestConfigRol` - 9 edges
9. `TestAccesoHTTP` - 9 edges
10. `TestProyectos` - 9 edges

## Surprising Connections (you probably didn't know these)
- `Cain` --uses--> `RegistroUso`  [INFERRED]
  core/agent.py → llm/registro.py
- `modo_terminal()` --calls--> `Cain`  [EXTRACTED]
  main.py → core/agent.py
- `get_historial()` --calls--> `extraer_animo()`  [EXTRACTED]
  web/app.py → core/emocion.py
- `TestEstadoEmocional` --uses--> `EstadoEmocional`  [INFERRED]
  tests/test_emocion.py → core/emocion.py
- `TestConfigRol` --uses--> `OllamaProvider`  [INFERRED]
  tests/test_llm_roles.py → llm/ollama_provider.py

## Import Cycles
- None detected.

## Communities (26 total, 0 thin omitted)

### Community 0 - "executor.py"
Cohesion: 0.09
Nodes (26): abrir_servidor_web(), corregir_y_reintentar(), describir_comando(), detectar_tipo(), ejecutar_proyecto(), ejecutar_python(), encontrar_puerto_libre(), guardar_archivo_proyecto() (+18 more)

### Community 1 - "Cain"
Cohesion: 0.10
Nodes (7): Cain, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, Flujo completo con confirmación. - Modo terminal: usa input() clásico - Modo…, Copia lo que necesita la pasada. Se llama con _lock_memoria tomado., Borra historial y memoria a largo plazo (no el perfil explícito)., Procesa un mensaje del usuario y retorna la respuesta de CAIN. canal: "texto" o…, modo_terminal()

### Community 2 - "CAIN — AI Agent with Personality, Memory and Voice"
Cohesion: 0.29
Nodes (6): Architecture, CAIN — AI Agent with Personality, Memory and Voice, Features, How to Run, Roadmap, Tech Stack

### Community 3 - "director.py"
Cohesion: 0.13
Nodes (17): aplicar_resultado(), bloque_para_prompt(), _formatear_conversacion(), _formatear_hechos(), _formatear_perfil(), _lista_de_textos(), llamar_director(), parsear_json() (+9 more)

### Community 4 - "agent.py"
Cohesion: 0.06
Nodes (27): Declaraciones JSON de las herramientas de CAIN (Fase 6). Cada entrada sigue el…, LLMProvider, ABC, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, config_rol(), crear_llms() (+19 more)

### Community 5 - "memory.py"
Cohesion: 0.12
Nodes (21): agregar_nota(), _cargar_json(), cargar_memoria(), cargar_memoria_larga(), cargar_usuario(), consultar_memoria(), _escribir_atomico(), _guardar_json() (+13 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.17
Nodes (6): evitar_sobrescritura(), generar_nombre_timestamp(), normalizar_nombre_txt(), Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna., Nombre de fallback con timestamp si la IA no genera uno.

### Community 10 - "test_servicio.py"
Cohesion: 0.06
Nodes (12): dict, CainFalso, Fase 9 — CAIN como servicio: acceso desde la red local, varios dispositivos a…, Lo mínimo que usa web/app.py del agente, sin LLM ni memoria real., Mensajes recibidos hasta (e incluido) el primero del tipo dado., recibir_hasta(), TestAcceso, TestAccesoHTTP (+4 more)

### Community 11 - "CAIN"
Cohesion: 0.25
Nodes (7): CAIN, Comandos, Convenciones, Cómo funciona un turno, Estructura, Pruebas, Stack

### Community 12 - "test_director.py"
Cohesion: 0.05
Nodes (15): construir_prompt(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, mismo_llm_para_todos(), Sustituto de crear_llms(): una sola instancia de prueba para todos los roles., BaseAgente, LLMFalso, LLM de prueba: registra las pasadas del director y responde algo fijo., TestAplicarResultado (+7 more)

### Community 13 - "voice.js"
Cohesion: 0.11
Nodes (22): agregarBotonProyecto(), agregarMensaje(), autoResize(), formatearContenido(), mostrarTyping(), scrollAbajo(), abrirPanel(), actualizarMemoriaPanel() (+14 more)

### Community 14 - "modal.js"
Cohesion: 0.57
Nodes (6): cerrarModal(), escapeHtml(), mostrarModalCargando(), mostrarModalCodigo(), mostrarModalConfirmacion(), responderConfirmacion()

### Community 15 - "state.js"
Cohesion: 0.22
Nodes (8): chatContainer, messageInput, micBtn, sendBtn, state, statusDot, statusText, vadBtn

### Community 17 - "websocket.js"
Cohesion: 0.60
Nodes (3): cargarHistorial(), conectar(), manejarMensaje()

### Community 18 - "app.py"
Cohesion: 0.07
Nodes (30): archivo_de_proyecto(), carpeta_de_proyecto(), html_principal(), Ruta absoluta de un proyecto, o None si no existe o el nombre intenta salirse…, Ruta absoluta de un archivo dentro de un proyecto, o None (igual que arriba)., El HTML con el que se abre un proyecto web: index.html si existe., get, middleware (+22 more)

### Community 19 - "test_emocion.py"
Cohesion: 0.06
Nodes (25): LLMConAnimo, TestProsodia, hacer_wav(), TestWavAMuestras, ABC, Transcribe audio a texto. Args: audio_bytes: Audio crudo (cualquier contenedor…, Interfaz común para cualquier motor de síntesis de voz. Cualquier motor que…, Sintetiza texto a audio. Args: texto: Texto a convertir en habla. emocion:… (+17 more)

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

### Community 25 - "acceso.py"
Cohesion: 0.23
Nodes (10): autorizado(), es_local(), ip_local(), Acceso a CAIN desde la red local (Fase 9). Desde la propia máquina (localhost)…, Compara en tiempo constante. Sin token esperado, nada es válido., Token que trae una petición HTTP o un WebSocket (ambos de Starlette): query…, IP de esta máquina en la red local (la que usarían otros dispositivos)., token_configurado() (+2 more)

## Knowledge Gaps
- **26 isolated node(s):** `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION`, `faceCurrent`, `faceEmocion` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 233 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `app.py`, `agent.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `RegistroUso` connect `agent.py` to `Cain`, `memory.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `limpiar_para_voz()` connect `limpiar_para_voz` to `app.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `RegistroUso` (e.g. with `Cain` and `TestConfigRol`) actually correct?**
  _`RegistroUso` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08866995073891626 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.09846153846153846 - nodes in this community are weakly interconnected._