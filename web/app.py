import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from dotenv import load_dotenv
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

from core.agent import Cain
from core import executor
from core.emocion import extraer_animo
from voice.stt import FasterWhisperSTT
from voice.tts import crear_tts
from voice.limpieza import limpiar_para_voz
from web import acceso
from web.conexiones import GestorConexiones

app       = FastAPI()
templates = Jinja2Templates(directory="web/templates")
pool      = ThreadPoolExecutor(max_workers=4)

app.mount("/static", StaticFiles(directory="web/static"), name="static")


def _version_estaticos():
    """
    Cambia cada vez que cambia algún JS/CSS. Va en sus URLs (?v=...) en
    index.html: para el navegador es una URL nueva y no puede usar una copia
    guardada antes del cambio (el móvil se quedó con un main.js viejo aun
    con "no-cache" y la caché borrada).
    """
    ultima = max(
        os.path.getmtime(os.path.join(raiz, archivo))
        for raiz, _, archivos in os.walk("web/static")
        for archivo in archivos
    )
    return str(int(ultima))


templates.env.globals["v"] = _version_estaticos()

cain_agent = Cain()
stt        = FasterWhisperSTT()
tts        = crear_tts()
gestor     = GestorConexiones()

UN_ANIO = 365 * 24 * 3600

PAGINA_SIN_ACCESO = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CAIN</title>
<body style="background:#0b0b10;color:#ddd;font-family:sans-serif;padding:2rem;max-width:32rem;margin:auto">
<h1>🎭 Acceso restringido</h1>
<p>Para entrar desde otro dispositivo abre la dirección con el token que
muestra la consola de CAIN al arrancar (<code>/?token=...</code>).</p>
<p>Si la consola no muestra ninguno, define <code>CAIN_TOKEN</code> en el
<code>.env</code> y reinicia CAIN.</p>
</body>"""


# ─── Acceso desde la red local ───────────────────────────────────────────────

@app.middleware("http")
async def control_de_acceso(request: Request, call_next):
    if not acceso.autorizado(request):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"error": "No autorizado"}, status_code=401)
        return HTMLResponse(PAGINA_SIN_ACCESO, status_code=401)

    token_url = request.query_params.get("token")
    if token_url and acceso.token_valido(token_url, acceso.token_configurado()):
        # Primera visita con ?token=: se guarda en cookie y se quita de la URL
        # (para que no quede en el historial ni en la barra de direcciones).
        respuesta = RedirectResponse(request.url.path)
        respuesta.set_cookie(
            acceso.COOKIE, token_url, max_age=UN_ANIO, httponly=True,
            samesite="strict", secure=request.url.scheme == "https",
        )
        return respuesta

    return await call_next(request)


@app.middleware("http")
async def estaticos_sin_cache_vieja(request: Request, call_next):
    respuesta = await call_next(request)
    # Sin Cache-Control el navegador (sobre todo el del móvil) adivina cuánto
    # guardar el JS/CSS y puede seguir días con la versión vieja junto al HTML
    # nuevo: la página queda a medias. "no-cache" = revalidar siempre (304).
    if request.url.path.startswith("/static/"):
        respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


# ─── API ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/memory")
async def get_memory():
    usuario = cain_agent.usuario_data
    return JSONResponse({
        "nombre":    usuario.get("nombre", None),
        "rol":       usuario.get("rol", None),
        "intereses": usuario.get("intereses", []),
        "notas":     usuario.get("notas", []),
        "resumen":   cain_agent.memoria_larga.get("notas") or None,
        "mensajes":  len(cain_agent.historial)
    })


@app.get("/api/historial")
async def get_historial():
    """La conversación reciente, para que un dispositivo que entra la vea."""
    mensajes = []
    for mensaje in cain_agent.historial:
        if mensaje.get("role") not in ("user", "assistant"):
            continue
        # El historial conserva [[animo: ...]] para el modelo; al usuario no.
        texto, _ = extraer_animo(mensaje.get("content", ""))
        mensajes.append({
            "rol":       "cain" if mensaje["role"] == "assistant" else "user",
            "contenido": texto,
        })
    return JSONResponse({"mensajes": mensajes})


@app.get("/api/uso")
async def get_uso():
    """Gasto del LLM por rol y modelo: hoy y desde que hay registro."""
    registro = cain_agent.registro_uso
    return JSONResponse({
        "modelos": {rol: f"{llm.proveedor}:{llm.model}" for rol, llm in cain_agent.llms.items()},
        "hoy":     registro.resumen_hoy(),
        "total":   registro.resumen(),
    })


@app.get("/api/proyectos")
async def get_proyectos():
    carpeta = executor.CARPETA_PROYECTOS
    if not os.path.exists(carpeta):
        return JSONResponse({"proyectos": []})
    proyectos = []
    for nombre in sorted(os.listdir(carpeta), reverse=True):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)
            tipo = "web" if executor.html_principal(archivos) else "python"
            proyectos.append({"nombre": nombre, "tipo": tipo, "archivos": archivos})
    return JSONResponse({"proyectos": proyectos[:10]})


@app.post("/api/proyectos/{nombre}/abrir")
async def abrir_proyecto(nombre: str):
    ruta = executor.carpeta_de_proyecto(nombre)
    if not ruta:
        return JSONResponse({"error": "Proyecto no encontrado"}, status_code=404)
    archivos = os.listdir(ruta)
    html     = executor.html_principal(archivos)
    if html:
        # Lo sirve el propio CAIN (ver servir_proyecto): una URL relativa
        # funciona igual desde el PC que desde el móvil, sin abrir puertos.
        return JSONResponse({"tipo": "web", "url": f"/proyectos/{nombre}/{html}"})

    py_file = next((a for a in archivos if a.endswith(".py")), None)
    if not py_file:
        return JSONResponse({"error": "No encontré archivo Python"}, status_code=404)
    try:
        with open(os.path.join(ruta, py_file), "r", encoding="utf-8") as f:
            codigo = f.read()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse({"tipo": "python", "archivo": py_file, "codigo": codigo})


@app.get("/proyectos/{nombre}/{ruta:path}")
async def servir_proyecto(nombre: str, ruta: str):
    archivo = executor.archivo_de_proyecto(nombre, ruta)
    if not archivo:
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
    return FileResponse(archivo)


# ─── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # El middleware HTTP no ve los WebSockets: el acceso se revisa aquí.
    if not acceso.autorizado(websocket):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    dispositivo = gestor.conectar(websocket)
    loop        = asyncio.get_running_loop()

    async def enviar_plan_y_esperar(plan):
        dispositivo.vaciar_confirmaciones()
        await gestor.enviar(dispositivo, {
            "tipo":     "confirmacion",
            "archivos": plan["archivos"],
            "comando":  plan["comando"],
            "nombre":   plan["nombre"],
        })
        try:
            return await asyncio.wait_for(dispositivo.confirmaciones.get(), timeout=300)
        except asyncio.TimeoutError:
            return False

    def confirmar_fn(plan):
        # La confirmación la da quien pidió el proyecto, no cualquier dispositivo.
        future = asyncio.run_coroutine_threadsafe(enviar_plan_y_esperar(plan), loop)
        return future.result(timeout=310)

    def estado_fn(estado):
        asyncio.run_coroutine_threadsafe(
            gestor.difundir({"tipo": "estado", "estado": estado}), loop
        )

    async def procesar_mensaje(mensaje, hablar=False):
        # Los demás dispositivos ven lo que se dijo; este ya lo pintó.
        await gestor.difundir({"tipo": "mensaje_usuario", "contenido": mensaje}, excepto=dispositivo)

        canal = "voz" if hablar else "texto"
        # Un turno a la vez: si otro dispositivo está hablando con CAIN, este
        # espera. Los callbacks se inyectan por turno, para quien lo pidió.
        async with gestor.turno:
            await gestor.difundir({"tipo": "estado", "estado": "pensando"})
            cain_agent._confirmar_fn = confirmar_fn
            cain_agent._estado_fn    = estado_fn
            try:
                respuesta = await loop.run_in_executor(pool, cain_agent.chat, mensaje, canal)
            except Exception as e:
                # Al correr en una tarea aparte, una excepción aquí no la ve
                # el try/except del bucle principal — hay que avisar a los
                # clientes explícitamente o se quedan esperando para siempre.
                await gestor.difundir({"tipo": "error", "contenido": str(e)})
                return
            finally:
                cain_agent._confirmar_fn = None
                cain_agent._estado_fn    = None
            emocion, intensidad = cain_agent.emocion.dominante()

        # El chat muestra la respuesta tal cual; a la voz le llega sin
        # emojis, markdown ni código (Piper los leería como basura).
        texto_voz = limpiar_para_voz(respuesta) if hablar else ""

        # "voz" avisa al cliente de que viene audio detrás: así sabe que CAIN
        # va a hablar (umbral de eco del VAD, barge-in) antes de que llegue.
        # Solo suena en el dispositivo que habló. "emocion" tiñe La Cara.
        datos = {
            "tipo": "respuesta", "contenido": respuesta, "estado": "listo",
            "voz": False,
            "emocion": {"nombre": emocion, "intensidad": intensidad},
        }
        await gestor.difundir(datos, excepto=dispositivo)
        await gestor.enviar(dispositivo, {**datos, "voz": bool(texto_voz)})

        if texto_voz:
            try:
                audio = await loop.run_in_executor(
                    pool, tts.sintetizar, texto_voz, emocion, intensidad
                )
                await gestor.enviar_bytes(dispositivo, audio)
            except Exception as e:
                print(f"[DEBUG] Error de sintesis de voz: {e}")
                await gestor.enviar(dispositivo, {"tipo": "sin_audio"})

        usuario = cain_agent.usuario_data
        await gestor.difundir({
            "tipo":      "memoria",
            "nombre":    usuario.get("nombre", None),
            "intereses": usuario.get("intereses", []),
            "notas":     usuario.get("notas", []),
            "mensajes":  len(cain_agent.historial)
        })

    async def procesar_audio(audio_bytes):
        await gestor.enviar(dispositivo, {"tipo": "estado", "estado": "escuchando"})

        try:
            texto = await loop.run_in_executor(pool, stt.transcribir, audio_bytes)
        except Exception as e:
            await gestor.enviar(dispositivo, {
                "tipo": "error", "contenido": f"No pude entender el audio: {e}"
            })
            return

        if not texto:
            await gestor.enviar(dispositivo, {
                "tipo": "respuesta", "contenido": "🎭 Silencio... No escuché nada. Habla cuando quieras."
            })
            return

        await gestor.enviar(dispositivo, {"tipo": "transcripcion", "contenido": texto})
        await procesar_mensaje(texto, hablar=True)

    try:
        while True:
            mensaje_ws = await websocket.receive()
            if mensaje_ws["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(mensaje_ws.get("code", 1000))

            if mensaje_ws.get("bytes") is not None:
                # Audio de voz — se lanza como tarea aparte por la misma
                # razón que los mensajes de texto (ver comentario abajo).
                asyncio.create_task(procesar_audio(mensaje_ws["bytes"]))
                continue

            data = mensaje_ws.get("text")
            if not data:
                continue

            payload  = json.loads(data)
            tipo_msg = payload.get("tipo", "mensaje")

            if tipo_msg == "confirmacion_respuesta":
                confirmado = payload.get("confirmado", False)
                print(f"[DEBUG] Confirmacion del dispositivo {dispositivo.numero}: {confirmado}")
                await dispositivo.confirmaciones.put(confirmado)
                continue

            mensaje = payload.get("mensaje", "").strip()
            if not mensaje:
                continue

            # Se lanza como tarea aparte para que este bucle siga libre
            # y pueda seguir leyendo el WebSocket (p.ej. la respuesta de
            # confirmación) mientras cain_agent.chat() se ejecuta.
            asyncio.create_task(procesar_mensaje(mensaje))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await gestor.enviar(dispositivo, {"tipo": "error", "contenido": str(e)})
    finally:
        gestor.desconectar(dispositivo)
