# Graph Report - PROYECTO-CAIN  (2026-10-29)

## Corpus Check
- 67 files · ~60,938 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1360 nodes · 2364 edges · 94 communities (58 shown, 32 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 68 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91b10443`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- executor.py
- Cain
- CAIN — AI Agent with Personality, Memory and Voice
- test_emocion.py
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
- tts.py
- face.js
- .usar
- ClienteSpotify
- limpiar_para_voz
- acceso.py
- Fase 10 — Control del sistema operativo: plan y arnés de seguridad
- .usar
- .denegada
- TestAgenteConArnes
- .conectar
- BaseConSO
- test_navegador.py
- SimuladoSO
- windows.py
- .autorizar
- TestCambiarDispositivo
- Denegado
- agent.py
- fabrica.py
- NavegadorCAIN
- resolver
- YouTube
- GestorConexiones
- TestContexto
- ._spotify_sonar
- revision_codigo.py
- arnes/youtube.py
- TestEjecucion
- recibir_hasta
- RegistroUso
- navegador.py
- TestLimitesYouTube
- enrutador_103.py
- .chat
- get_auditoria
- TestAccesoHTTP
- NavegadorSimulado
- TestProyectos
- LLMDeRol
- TestEvaluar
- SpotifyFalso
- ._mostrar
- TestLimites
- carpeta_de_proyecto
- TestSpotifyYYouTube
- TestConfigRol
- TestRevisionCodigo
- TestTeclaMultimediaConSpotify
- ._conversar
- ._memoria_olvidar
- archivo_de_proyecto
- corregir_y_reintentar
- ._buscar_dispositivo
- ._spotify_control
- ._youtube_reproducir
- TestFormato
- prompts.py
- _version_estaticos
- ._lista_de_videos
- TestDirectorEnElAgente
- TestRedLocalEnElNavegador
- TestPerfilSinSesionAnterior
- TestDispositivo
- TestSugerir
- ErrorConector
- HiloSincrono
- TestAplicarResultado
- TestPersistencia
- ClienteFalso
- abrir_servidor_web
- preparar_carpeta_proyecto
- registrar
- TestNumerosYNiveles

## God Nodes (most connected - your core abstractions)
1. `Denegado` - 78 edges
2. `Cain` - 70 edges
3. `SimuladoSO` - 32 edges
4. `TestHerramientas` - 29 edges
5. `ClienteSpotify` - 28 edges
6. `NavegadorCAIN` - 26 edges
7. `NavegadorSimulado` - 25 edges
8. `cancion()` - 21 edges
9. `YouTube` - 20 edges
10. `TestCambiarDispositivo` - 19 edges

## Surprising Connections (you probably didn't know these)
- `nuevo()` --uses--> `Cain`  [INFERRED]
  tests/manuales/enrutador_103.py → core/agent.py
- `paso()` --uses--> `Denegado`  [INFERRED]
  tests/manuales/navegador_real_103.py → core/arnes/rutas.py
- `Cain` --uses--> `RegistroUso`  [INFERRED]
  core/agent.py → llm/registro.py
- `Cain` --uses--> `YouTube`  [INFERRED]
  core/agent.py → so/conectores/youtube.py
- `YouTube` --uses--> `Denegado`  [INFERRED]
  so/conectores/youtube.py → core/arnes/rutas.py

## Import Cycles
- None detected.

## Communities (94 total, 32 thin omitted)

### Community 0 - "executor.py"
Cohesion: 0.16
Nodes (14): describir_comando(), detectar_tipo(), ejecutar_proyecto(), guardar_archivo_proyecto(), para_mostrar(), Guarda un archivo dentro de la carpeta del proyecto (o Denegado si se sale)., Genera una descripción legible del comando que se va a ejecutar., Ruta relativa a CAIN (proyectos/...), para los mensajes. (+6 more)

### Community 1 - "Cain"
Cohesion: 0.11
Nodes (4): Cain, Genera el plan (sin escribir nada) y lo devuelve como Accion: el arnés lo…, Agente principal. Orquesta memoria, herramientas, intención y LLM. No conoce a…, modo_terminal()

### Community 2 - "CAIN — AI Agent with Personality, Memory and Voice"
Cohesion: 0.29
Nodes (6): Architecture, CAIN — AI Agent with Personality, Memory and Voice, Features, How to Run, Roadmap, Tech Stack

### Community 3 - "test_emocion.py"
Cohesion: 0.05
Nodes (25): aplicar_resultado(), bloque_para_prompt(), _formatear_conversacion(), _formatear_hechos(), _formatear_perfil(), _lista_de_textos(), llamar_director(), parsear_json() (+17 more)

### Community 4 - "test_llm_roles.py"
Cohesion: 0.13
Nodes (11): LLMProvider, ABC, Envía una lista de mensajes al modelo y retorna la respuesta como string. Args:…, Envía una lista de mensajes junto con declaraciones de herramientas (JSON…, Interfaz común para cualquier proveedor de LLM. Cualquier modelo que CAIN use…, OllamaProvider, LLMProvider para modelos locales con Ollama (https://ollama.com). Ollama expone…, OpenAIProvider (+3 more)

### Community 5 - "memory.py"
Cohesion: 0.11
Nodes (22): agregar_nota(), _cargar_json(), cargar_memoria(), cargar_memoria_larga(), cargar_usuario(), consultar_memoria(), _escribir_atomico(), _guardar_json() (+14 more)

### Community 6 - "intent.py"
Cohesion: 0.18
Nodes (10): detectar_intencion_llm(), detectar_intereses_llm(), detectar_nombre(), detectar_rol(), es_misma_intencion_archivo(), Detecta si el usuario se identifica como creador de CAIN., Extrae intereses del usuario desde el mensaje. Retorna lista de strings, o []…, Valida si la edición solicitada es coherente con el contenido del archivo. (+2 more)

### Community 7 - "tools.py"
Cohesion: 0.14
Nodes (12): evitar_sobrescritura(), generar_nombre_timestamp(), leer_archivo(), mover_a_papelera(), normalizar_nombre_txt(), Nombre de fallback con timestamp si la IA no genera uno., Si el archivo ya existe, agrega sufijo numérico., Agrega la extensión .txt si el nombre no tiene ninguna. (+4 more)

### Community 10 - "test_servicio.py"
Cohesion: 0.11
Nodes (7): CainFalso, Fase 9 — CAIN como servicio: acceso desde la red local, varios dispositivos a…, Lo mínimo que usa web/app.py del agente, sin LLM ni memoria real., TestAcceso, TestAgenteAbreEnElDispositivo, TestEstaticos, TestHistorial

### Community 11 - "CAIN"
Cohesion: 0.25
Nodes (7): CAIN, Comandos, Convenciones, Cómo funciona un turno, Estructura, Pruebas, Stack

### Community 12 - "test_director.py"
Cohesion: 0.12
Nodes (10): construir_prompt(), Arma el prompt de sistema completo combinando: - Info del usuario (nombre, rol,…, mismo_llm_para_todos(), Sustituto de crear_llms(): una sola instancia de prueba para todos los roles., BaseAgente, LLMFalso, LLM de prueba: registra las pasadas del director y responde algo fijo., TestCanalVoz (+2 more)

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

### Community 19 - "tts.py"
Cohesion: 0.07
Nodes (24): TestProsodia, hacer_wav(), TestWavAMuestras, ABC, Transcribe audio a texto. Args: audio_bytes: Audio crudo (cualquier contenedor…, Interfaz común para cualquier motor de síntesis de voz. Cualquier motor que…, Sintetiza texto a audio. Args: texto: Texto a convertir en habla. emocion:…, Interfaz común para cualquier motor de reconocimiento de voz. Cualquier motor… (+16 more)

### Community 21 - "face.js"
Cohesion: 0.22
Nodes (12): ajustarTamanoFace(), animarFace(), crearTexturaGlow(), FACE_EMOCIONES, FACE_ESTADOS_CON_EMOCION, FACE_PRESETS, faceCurrent, faceEmocion (+4 more)

### Community 22 - ".usar"
Cohesion: 0.08
Nodes (8): BaseNavegador, Con navegador, abrir una URL o "el navegador" va por él (un solo dueño del…, El último vídeo de X" y "otro similar de él" (lo que falló en la prueba real)., TestAbrirConElNavegadorDeCAIN, TestControlYouTube, TestPestanas, TestUltimoYParecido, TestYouTube

### Community 23 - "ClienteSpotify"
Cohesion: 0.07
Nodes (24): artistas_de(), ClienteSpotify, crear_cliente_spotify(), describir(), ErrorSpotify, nombre_de(), Spotify por su API oficial (Fase 10.4). Ver FASE10_PLAN.md §6.5. Autorización…, La vuelta desde Spotify. El "state" tiene que ser uno que dio… (+16 more)

### Community 24 - "limpiar_para_voz"
Cohesion: 0.25
Nodes (3): TestLimpiarParaVoz, limpiar_para_voz(), Convierte una respuesta pensada para el chat en texto apto para TTS. Quita…

### Community 25 - "acceso.py"
Cohesion: 0.14
Nodes (18): acceso_local(), autorizado(), es_local(), firma_proyecto(), firma_valida(), ip_local(), _nombre_de_host(), origen_permitido() (+10 more)

### Community 26 - "Fase 10 — Control del sistema operativo: plan y arnés de seguridad"
Cohesion: 0.06
Nodes (34): 0. Principio rector, 10. Pruebas, 11. Decisiones, 12.1 WhatsApp Web, 12.2 Teclado y ratón genéricos, 12.3 YouTube sin cortes (y con sesión), 12. Fase 10.P — Pendientes de diseño, 13. Fase 10.1 — hecho (+26 more)

### Community 27 - ".usar"
Cohesion: 0.15
Nodes (3): cancion(), TestHerramientas, uri()

### Community 28 - ".denegada"
Cohesion: 0.10
Nodes (6): ConEspacio, skipUnless, Un espacio de trabajo vacío y propio para cada test., TestResolver, TestUrls, TestVerificar

### Community 29 - "TestAgenteConArnes"
Cohesion: 0.08
Nodes (10): evaluar(), nivel_de(), proceso_elevado(), True si CAIN corre como administrador. Se calcula una vez., Nivel de una llamada concreta, o None si la herramienta no está declarada., Primera puerta, antes de llamar a ningún handler. origen: "local" (el propio…, Veredicto, TestAgenteConArnes (+2 more)

### Community 31 - "BaseConSO"
Cohesion: 0.20
Nodes (5): BaseConSO, TestSinControlDelSistema, BaseAgenteSpotify, BaseSpotify, TestSinSpotify

### Community 32 - "test_navegador.py"
Cohesion: 0.05
Nodes (30): Registro de auditoría (Fase 10): cada herramienta que el LLM pide, con su…, Declaraciones JSON de las herramientas de CAIN (Fase 6). Cada entrada sigue el…, ControlSO, ErrorNavegador, Navegador, Pestana, ABC, Abre el navegador si no lo está y lo trae al frente. (+22 more)

### Community 33 - "SimuladoSO"
Cohesion: 0.06
Nodes (8): crear_control_so(), Fábrica del ControlSO activo, elegido con CAIN_SO en el .env. - "off"…, SimuladoSO, TestSinNavegador, Fase 10.2: abrir apps y URLs, multimedia y volumen (N1)., TestActuar, TestFabrica, TestObservar

### Community 34 - "windows.py"
Cohesion: 0.07
Nodes (27): entorno_apps(), es_ejecutable_permitido(), Las variables de entorno que heredan las apps que abre CAIN: sin secretos del…, Para so/: la ruta que se va a lanzar es una de la lista blanca, exacta., _con_volumen(), _es_de_alt_tab(), _escribir_mute(), _escribir_volumen() (+19 more)

### Community 35 - ".autorizar"
Cohesion: 0.16
Nodes (4): dict, Lo que hace el navegador: pedir la URL y volver con el state que trae., TestAutorizacion, TestRutas

### Community 37 - "Denegado"
Cohesion: 0.09
Nodes (30): Denegado, Exception, Una acción o ruta que el arnés no permite. El mensaje es el motivo., es_destino_local(), Límites de lo que CAIN hace en el sistema (Fase 10.2): qué apps abre, qué URLs,…, Para el navegador de CAIN (10.3): True si una petición que hace una página va a…, Un número de una lista que vio el usuario (1..cantidad). Lanza Denegado si no., Devuelve (accion, valor) con el valor como entero 0-100, o lanza Denegado. (+22 more)

### Community 38 - "agent.py"
Cohesion: 0.09
Nodes (22): _duracion(), _fecha_hora(), _gb(), lunes 27 de octubre de 2026, 14:05' (sin depender del locale del sistema)., Accion, Arnés de seguridad de CAIN (Fase 10). El LLM solo PROPONE una herramienta. Lo…, Lo que un handler propone hacer, sin haberlo hecho todavía. ejecutar: callable…, apps_permitidas() (+14 more)

### Community 39 - "fabrica.py"
Cohesion: 0.32
Nodes (6): config_rol(), crear_llms(), _env(), Un LLM por rol: cada tarea de CAIN puede ir con su propio proveedor y modelo…, (proveedor, modelo) para un rol, según el .env., Crea un LLMProvider por rol. Todos anotan su gasto en el registro. Returns:…

### Community 40 - "NavegadorCAIN"
Cohesion: 0.09
Nodes (7): _anotar_pestana_nueva(), NavegadorCAIN, El usuario cerró la ventana: la próxima vez se vuelve a abrir., La pestaña del sitio: la visible, si hay una; si no, la última., Depuración: quién abre cada pestaña (las about:blank que se quedan en blanco)., Lo que NavegadorCAIN rechaza antes de abrir el navegador., TestNavegadorCAINSinArrancar

### Community 41 - "resolver"
Cohesion: 0.16
Nodes (14): Protegidas: no se tocan, salvo las zonas propias de CAIN que caen dentro…, Carpetas de CAIN que son excepción dentro de una zona protegida., rutas_protegidas(), zonas_propias(), dentro_de(), _nombre_prohibido(), _normal(), True si `ruta` es `carpeta` o está debajo. Ambas ya resueltas. (+6 more)

### Community 42 - "YouTube"
Cohesion: 0.12
Nodes (14): limpiar_texto(), Título o canal leído de la página, para mostrárselo al usuario (nunca al LLM)., _fecha(), Lo leído de la página → [{url, titulo, canal}] válidos, sin repetir., Abre la búsqueda en la pestaña de YouTube y devuelve los primeros vídeos., {"nombre", "videos"} de la pestaña Vídeos de un canal: del más nuevo al más…, Los últimos vídeos del canal que mejor coincide con `nombre` (el primero de una…, {"url", "canal", "nombre_canal"} del vídeo de la pestaña de YouTube, o None. (+6 more)

### Community 43 - "GestorConexiones"
Cohesion: 0.16
Nodes (5): Dispositivo, GestorConexiones, Dispositivos conectados a la vez (Fase 9): PC, móvil, tablet... Todos ven la…, Tira respuestas viejas (p.ej. un clic que llegó tras el timeout)., Envía JSON a un dispositivo. Una conexión caída no tumba el turno.

### Community 45 - "._spotify_sonar"
Cohesion: 0.22
Nodes (3): Tus canciones con Me gusta; con consulta, solo las que coinciden (artista o…, La lista tuya que mejor coincide: nombre exacto, luego todas las palabras,…, Reproduce; si no hay dispositivo activo, busca uno (o abre la app de…

### Community 46 - "revision_codigo.py"
Cohesion: 0.38
Nodes (6): Revisión estática del Python que genera el LLM (Fase 10). NO es una garantía:…, Avisos de todos los .py de un plan {nombre: contenido}., Avisos (lista ordenada) sobre un archivo .py. Lanza Denegado si nombra una ruta…, _revisar_literal(), revisar_proyecto(), revisar_python()

### Community 47 - "arnes/youtube.py"
Cohesion: 0.15
Nodes (15): host_en(), True si la URL es http(s) y su sitio es uno de `dominios` o un subdominio suyo., Límites de lo que CAIN hace en YouTube (Fase 10.3). El LLM solo da texto para…, Texto para buscar: sin controles, espacios colapsados y con largo máximo., La página de resultados de YouTube; la consulta va como parámetro, codificada., Resultados de YouTube que son canales, para encontrar el de un creador., La pestaña "Vídeos" de un canal (del más nuevo al más viejo) a partir del…, La dirección canónica de un vídeo a partir de un enlace de la página… (+7 more)

### Community 49 - "recibir_hasta"
Cohesion: 0.21
Nodes (4): Mensajes recibidos hasta (e incluido) el primero del tipo dado., recibir_hasta(), TestArnesWeb, TestVariosDispositivos

### Community 50 - "RegistroUso"
Cohesion: 0.20
Nodes (5): costo(), Costo en USD de esos tokens, o None si el modelo no tiene precio conocido., Totales por rol y modelo, con costo. dias: lista de fechas "YYYY-MM-DD" a…, RegistroUso, TestRegistroUso

### Community 51 - "navegador.py"
Cohesion: 0.17
Nodes (7): _filtrar_peticion(), El navegador de CAIN (Fase 10.3): Brave (o Edge) con su perfil propio,…, _vacia(), espia(), H, quitar(), Fase 10.3: el filtro de red local del navegador de CAIN contra Brave real…

### Community 53 - "enrutador_103.py"
Cohesion: 0.24
Nodes (5): coincide(), decidir(), nuevo(), probar(), Fase 10.3: el enrutador real (sin ejecutar nada) con frases sueltas y…

### Community 54 - ".chat"
Cohesion: 0.22
Nodes (4): Procesa un mensaje del usuario y retorna la respuesta de CAIN. canal: "texto" o…, Con los argumentos con que el enrutador llamó a la herramienta (los escribió él…, Bloque para el prompt con los últimos turnos vigentes, o "" si no hay. Para el…, Pide confirmación a quien hizo la petición. - Modo web: self._confirmar_fn,…

### Community 55 - "get_auditoria"
Cohesion: 0.50
Nodes (4): Los últimos n eventos, del más reciente al más antiguo., ultimos(), get_auditoria(), Lo último que el arnés dejó (o no) hacer a CAIN.

### Community 57 - "NavegadorSimulado"
Cohesion: 0.14
Nodes (6): crear_navegador(), Control del sistema operativo (Fase 10). Ver FASE10_PLAN.md. Todo lo que pase…, El navegador de CAIN (Fase 10.3), según CAIN_SO igual que crear_control_so().…, NavegadorSimulado, Navegador que no abre nada. Las pruebas ponen en `respuestas` lo que devolvería…, TestFabricaNavegador

### Community 59 - "LLMDeRol"
Cohesion: 0.22
Nodes (3): LLMDeRol, LLM de prueba que apunta qué rol recibió cada llamada., TestRutasEnElAgente

### Community 64 - "carpeta_de_proyecto"
Cohesion: 0.29
Nodes (7): carpeta_de_proyecto(), html_principal(), El HTML con el que se abre un proyecto web: index.html si existe., Ruta absoluta de un proyecto, o None si no existe o el nombre intenta salirse…, post, abrir_proyecto(), get_proyectos()

### Community 71 - "archivo_de_proyecto"
Cohesion: 0.40
Nodes (5): archivo_de_proyecto(), Ruta absoluta de un archivo dentro de un proyecto, o None (igual que arriba)., URL estable (la que guardan el chat y la lista): lleva a la versión aislada., servir_proyecto(), servir_proyecto_aislado()

### Community 72 - "corregir_y_reintentar"
Cohesion: 0.25
Nodes (8): _avisos_confirmados(), corregir_y_reintentar(), ejecutar_python(), entorno_minimo(), Ejecuta un archivo Python desde su propia carpeta (cwd). Retorna tupla (exito,…, Avisos de revisar_proyecto ("archivo: aviso") que son de ese archivo., Intenta corregir el código automáticamente cuando hay un error. Máximo 2…, Entorno para el código generado: solo lo que Python necesita para correr.…

### Community 74 - "._spotify_control"
Cohesion: 0.25
Nodes (3): La tecla multimedia solo llega a lo que suena en este PC: si Spotify está…, Igual con un vídeo de YouTube que se está viendo en el navegador de CAIN: así…, "Pausa", "sigue" o "la siguiente" que el enrutador mandó a Spotify, pero que…

### Community 77 - "prompts.py"
Cohesion: 0.29
Nodes (6): generar_correccion_codigo(), generar_edicion_archivo(), generar_plan_proyecto(), Pide al LLM el contenido completo actualizado de un archivo existente., Le pide al LLM que genere el plan completo del proyecto: nombre + archivos con…, Le pide al LLM que corrija código Python que falló al ejecutarse.

### Community 85 - "ErrorConector"
Cohesion: 0.40
Nodes (4): ErrorConector, Exception, Conectores de sitio (Fase 10): CAIN habla con un servicio por su API o por su…, Un fallo del servicio que se le explica al usuario tal cual (en español).

### Community 90 - "abrir_servidor_web"
Cohesion: 0.50
Nodes (4): abrir_servidor_web(), encontrar_puerto_libre(), Busca el primer puerto disponible en el rango dado., Inicia un servidor HTTP local en un puerto libre y abre el navegador…

### Community 91 - "preparar_carpeta_proyecto"
Cohesion: 0.50
Nodes (4): nombre_seguro(), preparar_carpeta_proyecto(), Nombre de carpeta a partir del que inventa el LLM: solo [a-z0-9_-]., Crea la carpeta del proyecto con timestamp para evitar colisiones.

### Community 92 - "registrar"
Cohesion: 0.67
Nodes (3): resultado: "ejecutado", "denegado", "cancelado" o "error". Nunca lanza: un…, _recortar(), registrar()

## Knowledge Gaps
- **54 isolated node(s):** `_GUID`, `FACE_PRESETS`, `FACE_EMOCIONES`, `FACE_ESTADOS_CON_EMOCION`, `faceCurrent` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 546 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Denegado` connect `Denegado` to `executor.py`, `.usar`, `.denegada`, `TestAgenteConArnes`, `test_navegador.py`, `SimuladoSO`, `windows.py`, `agent.py`, `NavegadorCAIN`, `resolver`, `YouTube`, `revision_codigo.py`, `arnes/youtube.py`, `TestEjecucion`, `navegador.py`, `TestLimitesYouTube`, `NavegadorSimulado`, `TestLimites`, `TestRevisionCodigo`, `corregir_y_reintentar`, `TestNumerosYNiveles`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `Cain` connect `Cain` to `._conversar`, `agent.py`, `fabrica.py`, `._memoria_olvidar`, `._buscar_dispositivo`, `._spotify_control`, `._youtube_reproducir`, `YouTube`, `._spotify_sonar`, `._lista_de_videos`, `RegistroUso`, `app.py`, `enrutador_103.py`, `.chat`, `._mostrar`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `Denegado` (e.g. with `es_destino_local()` and `corregir_y_reintentar()`) actually correct?**
  _`Denegado` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Cain` (e.g. with `RegistroUso` and `YouTube`) actually correct?**
  _`Cain` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `SimuladoSO` (e.g. with `Denegado` and `BaseNavegador`) actually correct?**
  _`SimuladoSO` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `_GUID`, `FACE_PRESETS`, `FACE_EMOCIONES` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cain` be split into smaller, more focused modules?**
  _Cohesion score 0.11052631578947368 - nodes in this community are weakly interconnected._