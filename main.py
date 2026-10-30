import os
import sys
from dotenv import load_dotenv

load_dotenv()

SEGUNDOS_PARA_APAGARSE = 3

def modo_terminal():
    from core.agent import Cain
    agent = Cain()
    print("🎪 CAIN ha iniciado — Modo Terminal")
    print("Escribe 'salir' para terminar.\n")
    while True:
        usuario = input("TÚ: ")
        if usuario.lower() == "salir":
            print("🎪 CAIN: El espectáculo termina... por ahora.")
            break
        print(f"\nCAIN: {agent.chat(usuario)}\n")

def modo_web():
    import uvicorn
    from web import acceso

    host   = os.getenv("CAIN_HOST", "0.0.0.0")
    puerto = int(os.getenv("CAIN_PORT", "8000"))
    # HTTPS es necesario para usar el micrófono desde otro dispositivo:
    # el navegador solo lo permite en localhost o en un origen seguro.
    cert   = os.getenv("CAIN_SSL_CERT") or None
    clave  = os.getenv("CAIN_SSL_KEY") or None
    esquema = "https" if cert and clave else "http"

    print("🎪 CAIN ha iniciado — Modo Web")
    print(f"Abre {esquema}://localhost:{puerto} en tu navegador")

    if host not in ("127.0.0.1", "localhost"):
        token = acceso.token_configurado()
        if token:
            print(f"Desde otro dispositivo de la red: {esquema}://{acceso.ip_local()}:{puerto}/?token={token}")
        else:
            print("[AVISO] Sin CAIN_TOKEN en el .env solo se entra desde esta maquina.")
            print(f"        Para abrirlo a la red local agrega, por ejemplo: CAIN_TOKEN={acceso.generar_token()}")
        if esquema == "http":
            print("        (Sin HTTPS el microfono solo funciona en esta maquina: ver CAIN_SSL_CERT en el .env)")
    print()

    # lifespan="off": CAIN no usa eventos de arranque/apagado (todo se crea al
    # importar web/app.py), y con lifespan activo Ctrl+C deja un traceback de
    # CancelledError que no significa nada. Si algún día hace falta código
    # de apagado (p.ej. cerrar servidores de proyectos), quitar esto.
    # timeout_graceful_shutdown: tras Ctrl+C, uvicorn espera a que se cierren
    # las conexiones y tareas abiertas; sin límite, una que no termina (un
    # dispositivo que no contesta, un turno a medias) deja a CAIN sin apagarse.
    uvicorn.run("web.app:app", host=host, port=puerto, reload=False, lifespan="off",
                timeout_graceful_shutdown=SEGUNDOS_PARA_APAGARSE,
                ssl_certfile=cert if esquema == "https" else None,
                ssl_keyfile=clave if esquema == "https" else None)

    # Uvicorn ya cerró lo suyo. Un turno a medias en el pool de web/app.py (p.ej.
    # esperando una confirmación, hasta 310 s) haría que Python lo esperara al
    # salir: se sale ya. La memoria se escribe de forma atómica, así que cortar
    # a mitad de una escritura no deja un JSON roto. El navegador de CAIN se
    # cierra antes: matado con el proceso, se cree caído y al volver a abrirse
    # restaura sus pestañas.
    from web.app import cain_agent
    if cain_agent.navegador:
        cain_agent.navegador.apagar()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        modo_terminal()
    else:
        modo_web()