"""Fase 10.3: el filtro de red local del navegador de CAIN contra Brave real (headless, perfil temporal), con control."""
import os, sys, tempfile, threading, http.server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from core.arnes import reglas, sistema
from so import navegador as modulo
visitas, decisiones = [], []
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        visitas.append(self.path); self.send_response(200); self.end_headers(); self.wfile.write(b"hola")
    def log_message(self, *a): pass
threading.Thread(target=http.server.HTTPServer(("127.0.0.1", 8765), H).serve_forever, daemon=True).start()
original = modulo._filtrar_peticion
async def espia(ruta):
    decisiones.append((ruta.request.url, sistema.es_destino_local(ruta.request.url)))
    await original(ruta)
modulo._filtrar_peticion = espia
reglas.CARPETA_NAVEGADOR = tempfile.mkdtemp(prefix="cain_nav_prueba_")
reglas.ARGUMENTOS_NAVEGADOR = (*reglas.ARGUMENTOS_NAVEGADOR, "--headless=new")
nav = modulo.NavegadorCAIN(sistema.resolver_app("navegador")[0])
nav.abrir_url("https://www.youtube.com/")
async def ir(url):
    pagina = nav._contexto.pages[0]
    try:
        await pagina.goto(url, wait_until="commit"); return "cargo"
    except Exception as e:
        return str(e).splitlines()[0][:90]
print("con filtro:", nav._correr(ir("http://127.0.0.1:8765/con-filtro")), "| visitas:", visitas)
async def quitar():
    await nav._contexto.unroute(modulo.POSIBLE_RED_LOCAL, espia)
nav._correr(quitar())
print("sin filtro (control):", nav._correr(ir("http://127.0.0.1:8765/sin-filtro")), "| visitas:", visitas)
print("decisiones del filtro:", decisiones[:5], "... total", len(decisiones))
