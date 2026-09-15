import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import json
import asyncio
import threading
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

from core.agent import Cain
from core.executor import encontrar_puerto_libre
from voice.stt import FasterWhisperSTT
from voice.tts import crear_tts

app       = FastAPI()
templates = Jinja2Templates(directory="web/templates")
pool      = ThreadPoolExecutor(max_workers=4)

app.mount("/static", StaticFiles(directory="web/static"), name="static")

cain_agent = Cain()
stt        = FasterWhisperSTT()
tts        = crear_tts()


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
        "resumen":   cain_agent.resumen or None,
        "mensajes":  len(cain_agent.historial)
    })


@app.get("/api/proyectos")
async def get_proyectos():
    carpeta = "proyectos"
    if not os.path.exists(carpeta):
        return JSONResponse({"proyectos": []})
    proyectos = []
    for nombre in sorted(os.listdir(carpeta), reverse=True):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)
            tipo = "web" if any(a.endswith(".html") for a in archivos) else "python"
            proyectos.append({"nombre": nombre, "tipo": tipo, "archivos": archivos})
    return JSONResponse({"proyectos": proyectos[:10]})


@app.post("/api/proyectos/{nombre}/abrir")
async def abrir_proyecto(nombre: str):
    ruta = os.path.join("proyectos", nombre)
    if not os.path.exists(ruta):
        return JSONResponse({"error": "Proyecto no encontrado"}, status_code=404)
    archivos = os.listdir(ruta)
    es_web   = any(a.endswith(".html") for a in archivos)
    if es_web:
        puerto = encontrar_puerto_libre()
        def lanzar():
            subprocess.run(["python", "-m", "http.server", str(puerto)],
                cwd=ruta, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=lanzar, daemon=True).start()
        time.sleep(1)
        return JSONResponse({"tipo": "web", "url": f"http://localhost:{puerto}"})
    else:
        py_file = next((a for a in archivos if a.endswith(".py")), None)
        if not py_file:
            return JSONResponse({"error": "No encontré archivo Python"}, status_code=404)
        try:
            with open(os.path.join(ruta, py_file), "r", encoding="utf-8") as f:
                codigo = f.read()
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({"tipo": "python", "archivo": py_file, "codigo": codigo})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    confirmacion_queue = asyncio.Queue()

    async def enviar_plan_y_esperar(plan):
        await websocket.send_text(json.dumps({
            "tipo":     "confirmacion",
            "archivos": plan["archivos"],
            "comando":  plan["comando"],
            "nombre":   plan["nombre"],
        }))
        try:
            return await asyncio.wait_for(confirmacion_queue.get(), timeout=300)
        except asyncio.TimeoutError:
            return False

    def confirmar_fn(plan):
        future = asyncio.run_coroutine_threadsafe(
            enviar_plan_y_esperar(plan), loop
        )
        return future.result(timeout=310)

    cain_agent._confirmar_fn = confirmar_fn
    loop = asyncio.get_event_loop()

    async def procesar_mensaje(mensaje, hablar=False):
        await websocket.send_text(json.dumps({"tipo": "estado", "estado": "pensando"}))

        try:
            respuesta = await loop.run_in_executor(pool, cain_agent.chat, mensaje)
        except Exception as e:
            # Al correr en una tarea aparte, una excepción aquí no la ve
            # el try/except del bucle principal — hay que avisar al
            # cliente explícitamente o se queda esperando para siempre.
            await websocket.send_text(json.dumps({"tipo": "error", "contenido": str(e)}))
            return

        await websocket.send_text(json.dumps({
            "tipo": "respuesta", "contenido": respuesta, "estado": "listo"
        }))

        if hablar:
            try:
                audio = await loop.run_in_executor(pool, tts.sintetizar, respuesta)
                await websocket.send_bytes(audio)
            except Exception as e:
                print(f"[DEBUG] Error de síntesis de voz: {e}")

        usuario = cain_agent.usuario_data
        await websocket.send_text(json.dumps({
            "tipo":      "memoria",
            "nombre":    usuario.get("nombre", None),
            "intereses": usuario.get("intereses", []),
            "notas":     usuario.get("notas", []),
            "mensajes":  len(cain_agent.historial)
        }))

    async def procesar_audio(audio_bytes):
        await websocket.send_text(json.dumps({"tipo": "estado", "estado": "escuchando"}))

        try:
            texto = await loop.run_in_executor(pool, stt.transcribir, audio_bytes)
        except Exception as e:
            await websocket.send_text(json.dumps({
                "tipo": "error", "contenido": f"No pude entender el audio: {e}"
            }))
            return

        if not texto:
            await websocket.send_text(json.dumps({
                "tipo": "error", "contenido": "No detecté ninguna voz en el audio."
            }))
            return

        await websocket.send_text(json.dumps({"tipo": "transcripcion", "contenido": texto}))
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
                print(f"[DEBUG] Confirmación del usuario: {confirmado}")
                await confirmacion_queue.put(confirmado)
                continue

            mensaje = payload.get("mensaje", "").strip()
            if not mensaje:
                continue

            # Se lanza como tarea aparte para que este bucle siga libre
            # y pueda seguir leyendo el WebSocket (p.ej. la respuesta de
            # confirmación) mientras cain_agent.chat() se ejecuta.
            asyncio.create_task(procesar_mensaje(mensaje))

    except WebSocketDisconnect:
        cain_agent._confirmar_fn = None
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"tipo": "error", "contenido": str(e)}))
        except Exception:
            pass
        cain_agent._confirmar_fn = None