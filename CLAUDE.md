# CAIN

Agente conversacional en español con memoria persistente, estado de ánimo,
ejecución de proyectos generados por LLM y voz (STT/TTS, manos libres).
Backend FastAPI + WebSocket, frontend vanilla JS.

## Stack

- Python 3.14, FastAPI + Uvicorn (servidor y WebSocket), Jinja2 (templates).
- LLM: `llm/base.py` define la interfaz `LLMProvider`. Implementaciones:
  `llm/openai_provider.py` (OpenAI y APIs compatibles) y
  `llm/ollama_provider.py` (Ollama, sobre su API compatible con OpenAI).
  - Un LLM por rol (`llm/fabrica.py`): `conversacion`, `enrutador`,
    `intencion`, `director`, `codigo`. El agente usa `self.llms[rol]`;
    `self.llm` es el de conversación.
  - Todo uso de tokens se anota en `llm/registro.py` → `data/uso_llm.json`
    (por día, rol y modelo; costo con la tabla `PRECIOS`). `GET /api/uso`.
- Voz: `voice/base.py` define las interfaces `SpeechToText` y `TextToSpeech`.
  - STT: `faster-whisper` small, CPU int8 (`voice/stt.py`). Acepta WAV
    16 kHz mono del navegador directo como array (sin ffmpeg).
  - TTS: Piper local por defecto, o una API HTTP genérica — elegido en
    runtime con `TTS_PROVIDER` (ver `voice/tts.py`). Piper ajusta la
    prosodia según la emoción (`PROSODIA_POR_EMOCION`).
  - `voice/limpieza.py`: `limpiar_para_voz()` quita emojis, markdown,
    código y URLs antes de sintetizar.
- Frontend: JS vanilla sin build step, en `web/static/js/` (chat, websocket,
  state, modal, voz con VAD/barge-in, proyectos, `face.js` = La Cara en
  Three.js).
- Hardware objetivo: AMD RX 7600 (sin CUDA): STT y TTS en CPU, GPU libre
  para Ollama.

## Comandos

```bash
pip install -r requirements.txt
python -m uvicorn web.app:app --reload   # servidor web con recarga (usa web/app.py)
python main.py                           # servidor web en http://localhost:8000
python main.py terminal                  # modo terminal
.venv\Scripts\python -m unittest discover -s tests -t .   # pruebas
```

Variables de entorno en `.env` (ver `.env` para el listado completo):

- `OPENAI_API_KEY`
- `LLM_PROVIDER` (`openai` | `ollama`), `LLM_MODEL` — generales.
- `LLM_PROVIDER_<ROL>`, `LLM_MODEL_<ROL>` — por rol (`CONVERSACION`,
  `ENRUTADOR`, `INTENCION`, `DIRECTOR`, `CODIGO`). Un rol sin variables
  propias usa las generales; si cambia de proveedor, no hereda `LLM_MODEL`.
  Sin nada configurado, todo va con `openai:gpt-4o-mini`.
- `OLLAMA_URL` (default `http://localhost:11434/v1`).
- `TTS_PROVIDER` (`piper` | `api`), `TTS_API_URL`, `TTS_VOICE_ID`,
  `TTS_API_KEY`, `TTS_API_TIMEOUT`.
- Red local (Fase 9): `CAIN_TOKEN` (sin él solo entra localhost),
  `CAIN_HOST`, `CAIN_PORT`, `CAIN_SSL_CERT`/`CAIN_SSL_KEY` (HTTPS: el
  micrófono desde otro dispositivo lo exige).

## Estructura

- `core/` — el agente (`agent.py`), persistencia de memoria (`memory.py`),
  director de memoria a largo plazo (`director.py`), estado de ánimo
  (`emocion.py`), detección de intención (`intent.py`), ejecución de
  proyectos generados (`executor.py`), herramientas (`tools.py`,
  `tool_schemas.py`) y prompts (`prompts.py`).
- `llm/` — interfaz `LLMProvider`, proveedores, fábrica por rol y registro
  de gasto.
- `voice/` — interfaces `SpeechToText`/`TextToSpeech`, proveedores
  concretos y limpieza de texto para voz.
- `web/` — app FastAPI (`app.py`), templates y estáticos (`static/js`,
  `static/style.css`). `acceso.py`: token para la red local (middleware HTTP
  y chequeo en `/ws`). `conexiones.py`: `GestorConexiones` — varios
  dispositivos ven la misma conversación; un turno a la vez (`turno`); la
  confirmación y el audio van solo al dispositivo que pidió. Los proyectos
  web los sirve el propio FastAPI en `/proyectos/<nombre>/` (rutas validadas
  con `executor.archivo_de_proyecto`). Al crear uno en modo web,
  `ejecutar_proyecto(..., abrir_en_pc=False)` no abre nada en el PC: el url
  llega por `cain._abrir_fn` y va en la respuesta (`proyecto`, `abrir`).
- `data/` — memoria persistida y voces de Piper (`data/voices/`). No está
  en git. Archivos: `memoria.json` (historial), `memoria_usuario.json`
  (perfil), `memoria_larga.json` (director), `uso_llm.json` (gasto);
  `memoria_resumen.txt` es formato viejo, solo se lee para migrar.
- `proyectos/` — proyectos generados y ejecutados por CAIN.
- `tests/` — pruebas con `unittest`.
- `graphify-out/` — grafo de arquitectura generado por Graphify
  (`GRAPH_REPORT.md`, `graph.json`) — útil para orientarse rápido en el
  código antes de tocarlo.

## Cómo funciona un turno

1. El rol `enrutador` decide (function calling) si el mensaje pide una
   herramienta; si no, va a conversación.
2. `intencion` clasifica (historia/reto/técnico/conversación) y extrae
   intereses.
3. `conversacion` responde con un prompt que incluye perfil, bloque del
   director, sufijo de canal (`canal="voz"` → corto y sin formato) y el
   ánimo actual. La respuesta termina en `[[animo: ...]]`:
   `emocion.extraer_animo()` la quita para usuario, voz y director, pero el
   historial la conserva (si no, el modelo deja de emitirla).
4. Cada 10 mensajes, el `director` corre en un hilo aparte y actualiza
   `memoria_larga` bajo `_lock_memoria`. Los hechos solo se añaden o se
   marcan obsoletos por número — el modelo nunca reescribe la lista.

## Convenciones

- Nombres de funciones, variables y docstrings en español; el código sigue
  el patrón interfaz abstracta (`base.py`) + implementaciones concretas para
  cada subsistema intercambiable (LLM, STT, TTS).
- Selección de proveedor por variable de entorno cuando hay más de una
  implementación disponible en runtime (ver `voice/tts.py:crear_tts()` y
  `llm/fabrica.py:crear_llms()`).
- Escritura de JSON siempre con `memory._guardar_json` (atómica: temporal +
  `os.replace`); lectura con `memory._cargar_json` (tolera JSON corrupto).
- Todo JS/CSS nuevo en `index.html` se enlaza con `?v={{ v }}` (versión
  que calcula `web/app.py` al arrancar): sin eso el móvil sigue usando la
  copia vieja aunque se borre la caché.
- Los `print` de depuración solo con ASCII (`->`, no `→`): la consola de
  Windows (cp1252) lanza `UnicodeEncodeError` y tumba el turno.
- Commits en español, directo sobre `main`.

## Pruebas

- `tests/__init__.py` redirige todas las rutas de `data/` (memoria y
  `registro.ARCHIVO_USO`) a una carpeta temporal: **ningún test puede tocar
  la memoria real del usuario**. Una ruta nueva en `data/` debe redirigirse
  ahí también.
- Para construir un `Cain` sin red: parchear `agent_mod.crear_llms` (ver
  `tests.mismo_llm_para_todos`) y `threading.Thread` con `HiloSincrono`
  (`tests/test_director.py`) para que el director corra en el momento.
- El JS no tiene runner (no hay Node): se prueba con Edge headless
  (`msedge --headless=new --dump-dom` sobre un HTML de prueba).
