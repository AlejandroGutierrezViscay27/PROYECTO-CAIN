# Graph Report - PROYECTO-CAIN  (2026-10-28)

## Corpus Check
- 60 files · ~48,468 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1088 nodes · 1793 edges · 79 communities (55 shown, 20 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1979db61`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN — AI Agent with Personality, Memory and Voice
- director.py
- test_llm_roles.py
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
- stt.py
- face.js
- EstadoEmocional
- ClienteSpotify
- limpiar_para_voz
- acceso.py
- Fase 10 — Control del sistema operativo: plan y arnés de seguridad
- .usar
- .denegada
- TestAgenteConArnes
- .conectar
- test_spotify.py
- test_so.py
- SimuladoSO
- windows.py
- .autorizar
- TestCambiarDispositivo
- Denegado
- reglas.py
- agent.py
- arnes/__init__.py
- rutas.py
- TestActuar
- GestorConexiones
- TestContexto
- ._spotify_sonar
- revision_codigo.py
- sistema.py
- test_arnes.py
- test_emocion.py
- RegistroUso
- TestEstadoEmocional
- TextToSpeech
- APITTS
- .chat
- auditoria.py
- LLMProvider
- crear_control_so
- WindowsSO
- mismo_llm_para_todos
- TestEvaluar
- SpotifyFalso
- ._mostrar
- TestLimites
- carpeta_de_proyecto
- _lanzar
- TestConfigRol
- TestRevisionCodigo
- TestTeclaMultimediaConSpotify
- ._conversar
- ._memoria_olvidar
- archivo_de_proyecto
- registro.py
- ._buscar_dispositivo
- ._multimedia_por_spotify
- LLMConAnimo
- TestFormato
- ._preparar_proyecto
- _version_estaticos

## God Nodes (most connected - your core abstractions)
1. `Cain` - 52 edges
2. `Denegado` - 45 edges
3. `TestHerramientas` - 29 edges
4. `ClienteSpotify` - 28 edges
5. `SimuladoSO` - 25 edges
6. `cancion()` - 19 edges
7. `TestCambiarDispositivo` - 19 edges
8. `TestActuar` - 18 edges
9. `WindowsSO` - 17 edges
10. `Fase 10 — Control del sistema operativo: plan y arnés de seguridad` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Cain` --uses--> `RegistroUso`  [INFERRED]
  core/agent.py → llm/registro.py
- `SimuladoSO` --uses--> `Denegado`  [INFERRED]
  so/simulado.py → core/arnes/rutas.py
- `WindowsSO` --uses--> `Denegado`  [INFERRED]
  so/windows.py → core/arnes/rutas.py
- `ConEspacio` --uses--> `Denegado`  [INFERRED]
  tests/test_arnes.py → core/arnes/rutas.py
- `TestApps` --uses--> `Denegado`  [INFERRED]
  tests/test_arnes.py → core/arnes/rutas.py

## Import Cycles
- None detected.

## Communities (79 total, 20 thin omitted)

### Community 0 - "executor.py"
Cohesion: 0.10
Nodes (26): abrir_servidor_web(), describir_comando(), detectar_tipo(), ejecutar_proyecto(), ejecutar_python(), encontrar_puerto_libre(), entorno_minimo(), guardar_archivo_proyecto() (+18 more)

### Community 1 - "Cain"
Cohesion: 0.13
Nodes (3): Cain, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, modo_terminal()

### Community 2 - "CAIN — AI Agent with Personality, Memory and Voice"
Cohesion: 0.29
Nodes (6): Architecture, CAIN — AI Agent with Personality, Memory and Voice, Features, How to Run, Roadmap, Tech Stack

### Community 3 - "director.py"
Cohesion: 0.09
Nodes (23): aplicar_resultado(), bloque_para_prompt(), _formatear_conversacion(), _formatear_hechos(), _formatear_perfil(), _lista_de_textos(), llamar_director(), parsear_json() (+15 more)

### Community 4 - "test_llm_roles.py"
Cohesion: 0.15
Nodes (8): OllamaProvider, LLMProvider para modelos locales con Ollama (https://ollama.com). Ollama expone…, OpenAIProvider, Implementación de LLMProvider usando la API de OpenAI. Es la única clase en…, Llama a OpenAI y retorna la respuesta como string., Llama a OpenAI con function calling y retorna texto o una llamada a herramienta., ClienteFalso, Imita client.chat.completions.create() con un uso de tokens fijo.

### Community 5 - "memory.py"
Cohesion: 0.12
Nodes (21): agregar_nota(), _cargar_json(), cargar_memoria(), cargar_memoria_larga(), cargar_usuario(), consultar_memoria(), _escribir_atomico(), _guardar_json() (+13 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.14
Nodes (12): evitar_sobrescritura(), generar_nombre_timestamp(), leer_archivo(), mover_a_papelera(), normalizar_nombre_txt(), Nombre de fallback con timestamp si la IA no genera uno., Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna. (+4 more)

### Community 10 - "test_servicio.py"
Cohesion: 0.05
Nodes (13): CainFalso, dict, Fase 9 — CAIN como servicio: acceso desde la red local, varios dispositivos a…, Lo mínimo que usa web/app.py del agente, sin LLM ni memoria real., Mensajes recibidos hasta (e incluido) el primero del tipo dado., recibir_hasta(), TestAcceso, TestAccesoHTTP (+5 more)

### Community 11 - "CAIN"
Cohesion: 0.25
Nodes (7): CAIN, Comandos, Convenciones, Cómo funciona un turno, Estructura, Pruebas, Stack

### Community 12 - "test_director.py"
Cohesion: 0.04
Nodes (17): construir_prompt(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, BaseAgente, HiloSincrono, LLMFalso, LLM de prueba: registra las pasadas del director y responde algo fijo., Sustituto de threading.Thread que corre el target en el momento., TestAplicarResultado (+9 more)

### Community 13 - "voice.js"
Cohesion: 0.11
Nodes (22): agregarBotonProyecto(), agregarMensaje(), autoResize(), formatearContenido(), mostrarTyping(), scrollAbajo(), abrirPanel(), actualizarMemoriaPanel() (+14 more)

### Community 14 - "modal.js"
Cohesion: 0.62
Nodes (6): cerrarModal(), escapeHtml(), mostrarModalCargando(), mostrarModalCodigo(), mostrarModalConfirmacion(), responderConfirmacion()

### Community 15 - "state.js"
Cohesion: 0.22
Nodes (8): chatContainer, messageInput, micBtn, sendBtn, state, statusDot, statusText, vadBtn

### Community 17 - "websocket.js"
Cohesion: 0.60
Nodes (3): cargarHistorial(), conectar(), manejarMensaje()

### Community 18 - "app.py"
Cohesion: 0.21
Nodes (16): get, middleware, Request, control_de_acceso(), estaticos_sin_cache_vieja(), get_historial(), get_memory(), get_uso() (+8 more)

### Community 19 - "stt.py"
Cohesion: 0.26
Nodes (6): hacer_wav(), TestWavAMuestras, FasterWhisperSTT, Si el audio es WAV PCM 16-bit mono a 16 kHz (lo que manda el navegador), lo…, Reconocimiento de voz local con faster-whisper (CTranslate2). Corre en CPU a…, wav_a_muestras()

### Community 21 - "face.js"
Cohesion: 0.22
Nodes (12): ajustarTamanoFace(), animarFace(), crearTexturaGlow(), FACE_EMOCIONES, FACE_ESTADOS_CON_EMOCION, FACE_PRESETS, faceCurrent, faceEmocion (+4 more)

### Community 22 - "EstadoEmocional"
Cohesion: 0.27
Nodes (4): EstadoEmocional, Texto corto del ánimo actual para el prompt de sistema., Un turno de conversación: desvanece las emociones que no aparecen en deltas,…, (emocion, intensidad) de la emoción más fuerte, o ("neutral", 0.0).

### Community 23 - "ClienteSpotify"
Cohesion: 0.06
Nodes (28): ErrorConector, Exception, Conectores de sitio (Fase 10): CAIN habla con un servicio por su API o por su…, Un fallo del servicio que se le explica al usuario tal cual (en español)., artistas_de(), ClienteSpotify, crear_cliente_spotify(), describir() (+20 more)

### Community 24 - "limpiar_para_voz"
Cohesion: 0.25
Nodes (3): TestLimpiarParaVoz, limpiar_para_voz(), Convierte una respuesta pensada para el chat en texto apto para TTS. Quita…

### Community 25 - "acceso.py"
Cohesion: 0.14
Nodes (18): acceso_local(), autorizado(), es_local(), firma_proyecto(), firma_valida(), ip_local(), _nombre_de_host(), origen_permitido() (+10 more)

### Community 26 - "Fase 10 — Control del sistema operativo: plan y arnés de seguridad"
Cohesion: 0.06
Nodes (31): 0. Principio rector, 10. Pruebas, 11. Decisiones, 12.1 WhatsApp Web, 12.2 Teclado y ratón genéricos, 12. Fase 10.P — Pendientes de diseño, 13. Fase 10.1 — hecho, 14. Fase 10.2 — hecho (+23 more)

### Community 27 - ".usar"
Cohesion: 0.15
Nodes (3): cancion(), TestHerramientas, uri()

### Community 28 - ".denegada"
Cohesion: 0.10
Nodes (6): ConEspacio, skipUnless, Un espacio de trabajo vacío y propio para cada test., TestResolver, TestUrls, TestVerificar

### Community 29 - "TestAgenteConArnes"
Cohesion: 0.12
Nodes (3): TestAgenteConArnes, TestApps, TestProyectosConArnes

### Community 31 - "test_spotify.py"
Cohesion: 0.13
Nodes (8): Declaraciones JSON de las herramientas de CAIN (Fase 6). Cada entrada sigue el…, BaseConSO, TestSinControlDelSistema, BaseAgenteSpotify, BaseSpotify, Fase 10.4 — Spotify por su API oficial. Primero los ataques, después lo que sí…, TestSinSpotify, TestSugerir

### Community 32 - "test_so.py"
Cohesion: 0.11
Nodes (12): ControlSO, ABC, Interfaz común para observar y actuar sobre el sistema operativo. Cualquier…, Estado del equipo. Claves (las que no se puedan saber, en None): sistema: str —…, Abre el ejecutable `ruta` (una de reglas.apps_permitidas(), exacta) con sus…, Abre una URL http(s) en el navegador de CAIN (su perfil propio)., Tecla multimedia: "reproducir_pausar", "siguiente" o "anterior"., Volumen general: (porcentaje 0-100, silenciado). (+4 more)

### Community 33 - "SimuladoSO"
Cohesion: 0.11
Nodes (4): Ventanas de aplicación abiertas (las que se verían con Alt+Tab), con la activa…, Ventana, SimuladoSO, TestObservar

### Community 34 - "windows.py"
Cohesion: 0.14
Nodes (15): _con_volumen(), _es_de_alt_tab(), _escribir_mute(), _escribir_volumen(), _EstadoEnergia, _EstadoMemoria, _GUID, _leer_volumen() (+7 more)

### Community 35 - ".autorizar"
Cohesion: 0.16
Nodes (4): dict, Lo que hace el navegador: pedir la URL y volver con el state que trae., TestAutorizacion, TestRutas

### Community 37 - "Denegado"
Cohesion: 0.17
Nodes (15): Denegado, Exception, Una acción o ruta que el arnés no permite. El mensaje es el motivo., normalizar_nombre(), Límites de lo que CAIN hace con Spotify (Fase 10.4). El LLM solo da opciones…, Texto para buscar: sin controles, espacios colapsados y con largo máximo., Un URI de Spotify bien formado y de uno de los tipos de la API dados., El id viene de la API (nunca del LLM); igual se comprueba su forma. (+7 more)

### Community 38 - "reglas.py"
Cohesion: 0.16
Nodes (14): apps_permitidas(), argumentos_app(), _entorno(), Reglas del arnés de seguridad (Fase 10). Viven en el código a propósito: CAIN…, Protegidas: no se tocan, salvo las zonas propias de CAIN que caen dentro…, Apps que CAIN puede abrir: nombre → rutas exactas candidatas (se usa la primera…, Argumentos fijos con que se abre cada app. El LLM no añade ninguno., Carpetas de CAIN que son excepción dentro de una zona protegida. (+6 more)

### Community 39 - "agent.py"
Cohesion: 0.20
Nodes (10): _duracion(), _fecha_hora(), _gb(), lunes 27 de octubre de 2026, 14:05' (sin depender del locale del sistema)., config_rol(), crear_llms(), _env(), Un LLM por rol: cada tarea de CAIN puede ir con su propio proveedor y modelo… (+2 more)

### Community 40 - "arnes/__init__.py"
Cohesion: 0.18
Nodes (10): Accion, evaluar(), nivel_de(), proceso_elevado(), Arnés de seguridad de CAIN (Fase 10). El LLM solo PROPONE una herramienta. Lo…, Lo que un handler propone hacer, sin haberlo hecho todavía. ejecutar: callable…, True si CAIN corre como administrador. Se calcula una vez., Nivel de una llamada concreta, o None si la herramienta no está declarada. (+2 more)

### Community 41 - "rutas.py"
Cohesion: 0.22
Nodes (13): dentro_de(), _nombre_prohibido(), _normal(), para_mostrar(), Resolución y verificación de rutas (Fase 10). Toda ruta que viene del LLM pasa…, Ruta relativa a la zona, para enseñársela al usuario., True si `ruta` es `carpeta` o está debajo. Ambas ya resueltas., Lo que se rechaza sin siquiera resolver la ruta. (+5 more)

### Community 43 - "GestorConexiones"
Cohesion: 0.16
Nodes (5): Dispositivo, GestorConexiones, Dispositivos conectados a la vez (Fase 9): PC, móvil, tablet... Todos ven la…, Tira respuestas viejas (p.ej. un clic que llegó tras el timeout)., Envía JSON a un dispositivo. Una conexión caída no tumba el turno.

### Community 45 - "._spotify_sonar"
Cohesion: 0.22
Nodes (3): Tus canciones con Me gusta; con consulta, solo las que coinciden (artista o…, La lista tuya que mejor coincide: nombre exacto, luego todas las palabras,…, Reproduce; si no hay dispositivo activo, busca uno (o abre la app de…

### Community 46 - "revision_codigo.py"
Cohesion: 0.22
Nodes (10): Revisión estática del Python que genera el LLM (Fase 10). NO es una garantía:…, Avisos de todos los .py de un plan {nombre: contenido}., Avisos (lista ordenada) sobre un archivo .py. Lanza Denegado si nombra una ruta…, _revisar_literal(), revisar_proyecto(), revisar_python(), _avisos_confirmados(), corregir_y_reintentar() (+2 more)

### Community 47 - "sistema.py"
Cohesion: 0.20
Nodes (10): es_ejecutable_permitido(), Límites de lo que CAIN hace en el sistema (Fase 10.2): qué apps abre, qué URLs,…, Devuelve (accion, valor) con el valor como entero 0-100, o lanza Denegado., Para so/: la ruta que se va a lanzar es una de la lista blanca, exacta., Devuelve la URL si se puede abrir en el navegador de CAIN; si no, lanza…, Solo sitios de internet: un dominio con TLD de letras o una IP pública., _revisar_host(), validar_multimedia() (+2 more)

### Community 48 - "test_arnes.py"
Cohesion: 0.18
Nodes (3): Fase 10.0 — arnés de seguridad: lo que CAIN NO puede hacer. Casi todos los…, TestEjecucion, TestMultimediaYVolumen

### Community 49 - "test_emocion.py"
Cohesion: 0.27
Nodes (5): TestProsodia, _curva_s(), parametros_prosodia(), Sigmoide normalizada a [0, 1] (como la de OpenSakura): las emociones suaves…, Mezcla la prosodia neutral con la de la emoción según su intensidad.

### Community 50 - "RegistroUso"
Cohesion: 0.24
Nodes (3): Totales por rol y modelo, con costo. dias: lista de fechas "YYYY-MM-DD" a…, RegistroUso, TestRegistroUso

### Community 52 - "TextToSpeech"
Cohesion: 0.24
Nodes (7): ABC, Transcribe audio a texto. Args: audio_bytes: Audio crudo (cualquier contenedor…, Interfaz común para cualquier motor de síntesis de voz. Cualquier motor que…, Sintetiza texto a audio. Args: texto: Texto a convertir en habla. emocion:…, Interfaz común para cualquier motor de reconocimiento de voz. Cualquier motor…, SpeechToText, TextToSpeech

### Community 53 - "APITTS"
Cohesion: 0.20
Nodes (6): APITTS, crear_tts(), PiperTTS, Fábrica del motor de TTS activo, elegido con TTS_PROVIDER en el .env. - "piper"…, Síntesis de voz local con Piper (ONNX). Corre en CPU en tiempo real, sin…, Síntesis de voz vía una API HTTP genérica (p.ej. un servidor Coqui TTS u otro…

### Community 54 - ".chat"
Cohesion: 0.22
Nodes (4): Procesa un mensaje del usuario y retorna la respuesta de CAIN. canal: "texto" o…, Con los argumentos con que el enrutador llamó a la herramienta (los escribió él…, Bloque para el prompt con los últimos turnos vigentes, o "" si no hay. Para el…, Pide confirmación a quien hizo la petición. - Modo web: self._confirmar_fn,…

### Community 55 - "auditoria.py"
Cohesion: 0.25
Nodes (8): Registro de auditoría (Fase 10): cada herramienta que el LLM pide, con su…, resultado: "ejecutado", "denegado", "cancelado" o "error". Nunca lanza: un…, Los últimos n eventos, del más reciente al más antiguo., _recortar(), registrar(), ultimos(), get_auditoria(), Lo último que el arnés dejó (o no) hacer a CAIN.

### Community 56 - "LLMProvider"
Cohesion: 0.28
Nodes (5): LLMProvider, ABC, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…

### Community 57 - "crear_control_so"
Cohesion: 0.28
Nodes (4): crear_control_so(), Control del sistema operativo (Fase 10). Ver FASE10_PLAN.md. Todo lo que pase…, Fábrica del ControlSO activo, elegido con CAIN_SO en el .env. - "off"…, TestFabrica

### Community 58 - "WindowsSO"
Cohesion: 0.28
Nodes (4): WindowsSO, skipUnless, Contra el sistema real: solo lee, no cambia nada., TestWindowsReal

### Community 59 - "mismo_llm_para_todos"
Cohesion: 0.22
Nodes (3): mismo_llm_para_todos(), Sustituto de crear_llms(): una sola instancia de prueba para todos los roles., TestAnimoEnElAgente

### Community 64 - "carpeta_de_proyecto"
Cohesion: 0.29
Nodes (7): carpeta_de_proyecto(), html_principal(), El HTML con el que se abre un proyecto web: index.html si existe., Ruta absoluta de un proyecto, o None si no existe o el nombre intenta salirse…, post, abrir_proyecto(), get_proyectos()

### Community 65 - "_lanzar"
Cohesion: 0.33
Nodes (5): _entorno_app(), _lanzar(), _preparar_perfil_navegador(), Abre el programa sin consola y sin esperarlo. Nunca con shell., La primera vez, crea el perfil de CAIN con preferencias prudentes.

### Community 71 - "archivo_de_proyecto"
Cohesion: 0.40
Nodes (5): archivo_de_proyecto(), Ruta absoluta de un archivo dentro de un proyecto, o None (igual que arriba)., URL estable (la que guardan el chat y la lista): lleva a la versión aislada., servir_proyecto(), servir_proyecto_aislado()

### Community 72 - "registro.py"
Cohesion: 0.40
Nodes (3): costo(), Registro de gasto del LLM: cuántas llamadas y tokens usa cada rol de CAIN…, Costo en USD de esos tokens, o None si el modelo no tiene precio conocido.

## Knowledge Gaps
- **52 isolated node(s):** `_GUID`, `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION`, `faceCurrent` (+47 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 444 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Cain` connect `Cain` to `._conversar`, `._memoria_olvidar`, `agent.py`, `._buscar_dispositivo`, `._multimedia_por_spotify`, `._spotify_sonar`, `._preparar_proyecto`, `RegistroUso`, `app.py`, `.chat`, `._mostrar`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `Denegado` connect `Denegado` to `executor.py`, `test_so.py`, `SimuladoSO`, `windows.py`, `_lanzar`, `TestRevisionCodigo`, `reglas.py`, `arnes/__init__.py`, `rutas.py`, `TestActuar`, `revision_codigo.py`, `sistema.py`, `test_arnes.py`, `TestLimites`, `WindowsSO`, `.denegada`, `TestAgenteConArnes`, `test_spotify.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Denegado` (e.g. with `corregir_y_reintentar()` and `SimuladoSO`) actually correct?**
  _`Denegado` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `SimuladoSO` (e.g. with `Denegado` and `TestActuar`) actually correct?**
  _`SimuladoSO` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `_GUID`, `FACE_PRESETS`, `FACE_EMOCIONES` to the rest of the system?**
  _52 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09788359788359788 - nodes in this community are weakly interconnected._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._