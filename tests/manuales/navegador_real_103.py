"""NavegadorCAIN contra Brave real, perfil temporal y headless. Sin reproducir nada."""
import os, sys, tempfile, threading
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from core.arnes import reglas, sistema
from core.arnes.rutas import Denegado
from so.base import ErrorNavegador
from so.conectores.youtube import YouTube
from so import navegador as modulo

reglas.CARPETA_NAVEGADOR = tempfile.mkdtemp(prefix="cain_nav_prueba_")
reglas.ARGUMENTOS_NAVEGADOR = (*reglas.ARGUMENTOS_NAVEGADOR, "--headless=new")

ruta, _ = sistema.resolver_app("navegador")
nav = modulo.NavegadorCAIN(ruta)
yt = YouTube(nav)

def paso(nombre, f):
    try:
        print(f"[OK]  {nombre}: {f()}")
    except (Denegado, ErrorNavegador) as e:
        print(f"[NO]  {nombre}: {type(e).__name__}: {e}")

print("pestanas antes de abrir (no debe arrancar):", nav.pestanas(), nav._contexto)

# Desde otro hilo distinto, como el pool de web/app.py
r = {}
t = threading.Thread(target=lambda: r.setdefault("v", yt.buscar("documental agujeros negros")))
t.start(); t.join()
for v in r["v"]:
    print("   ", v)

paso("estado sin video (pagina de resultados)", yt.estado)
paso("control sin video", lambda: yt.control("pausar"))

paso("abrir example.com", lambda: nav.abrir_url("https://example.com/"))
paso("pestanas", lambda: [(p.titulo, p.url, p.activa) for p in nav.pestanas()])

FETCH = """async (url) => { try { await fetch(url, {mode: 'no-cors'}); return 'LLEGO'; } catch (e) { return 'bloqueado: ' + e.message; } }"""
for destino in ("http://127.0.0.1:8000/api/auditoria", "http://192.168.1.1/", "http://localhost:8000/",
                "http://router/", "https://www.youtube.com/"):
    paso(f"fetch desde example.com -> {destino}",
         lambda d=destino: nav.en_sitio(("example.com",), FETCH, d))

# El guion dentro de la pagina: en example.com con dominios de YouTube debe negarse.
async def guion_fuera():
    pagina = next(p for p in nav._contexto.pages if "example.com" in p.url)
    try:
        await pagina.evaluate(modulo._ENVOLTORIO.replace("GUION", "() => 'CORRIO'"), [["youtube.com"], None])
        return "CORRIO (mal)"
    except Exception as e:
        return "negado: " + str(e).splitlines()[0][:80]
paso("guion de YouTube en example.com", lambda: nav._correr(guion_fuera()))

paso("navegar por JS a la red local", lambda: nav.en_sitio(("example.com",),
     "async () => { location.href = 'http://192.168.1.1/'; await new Promise(r => setTimeout(r, 1500)); return location.href; }"))
paso("pestanas tras intento", lambda: [(p.titulo[:40], p.url) for p in nav.pestanas()])

ps = nav.pestanas()
paso("cerrar con url equivocada", lambda: nav.cerrar(0, "https://otra.com/"))
paso("cerrar la ultima", lambda: nav.cerrar(len(ps) - 1, ps[-1].url))
paso("pestanas final", lambda: [p.url for p in nav.pestanas()])
