"""
Fase 9 — CAIN como servicio: acceso desde la red local, varios dispositivos
a la vez y proyectos servidos por el propio FastAPI.
"""
import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient

from core import executor
from web import acceso

TOKEN = "token-de-prueba"
LOCAL = ("127.0.0.1", 50000)


class CainFalso:
    """Lo mínimo que usa web/app.py del agente, sin LLM ni memoria real."""

    def __init__(self):
        self.historial = [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "¡Bienvenido! [[animo: alegria +0.3]]"},
        ]
        self.usuario_data  = {"nombre": "Ana"}
        self.memoria_larga = {}
        self.emocion       = SimpleNamespace(dominante=lambda: ("alegria", 0.3))
        self._confirmar_fn = None
        self._estado_fn    = None

    def chat(self, mensaje, canal="texto"):
        if mensaje == "haz un proyecto":
            confirmado = self._confirmar_fn({"archivos": ["main.py"], "comando": "python main.py", "nombre": "demo"})
            return f"confirmado: {confirmado}"
        return f"eco: {mensaje}"


def importar_app():
    # web/app.py crea el agente, el STT y el TTS al importarse: se sustituyen
    # para no cargar Whisper ni Piper ni llamar a ningún LLM.
    with mock.patch("core.agent.Cain", CainFalso), \
         mock.patch("voice.stt.FasterWhisperSTT", mock.MagicMock), \
         mock.patch("voice.tts.crear_tts", mock.MagicMock):
        from web import app as app_mod
    return app_mod


app_mod = importar_app()


def recibir_hasta(ws, tipo):
    """Mensajes recibidos hasta (e incluido) el primero del tipo dado."""
    recibidos = []
    while True:
        datos = ws.receive_json()
        recibidos.append(datos)
        if datos["tipo"] == tipo:
            return recibidos


# ─── Acceso ──────────────────────────────────────────────────────────────────

class TestAcceso(unittest.TestCase):

    def test_token_valido(self):
        self.assertTrue(acceso.token_valido("abc", "abc"))
        self.assertFalse(acceso.token_valido("abd", "abc"))
        self.assertFalse(acceso.token_valido("", "abc"))
        # Sin token configurado, nadie de fuera entra (ni con token vacío).
        self.assertFalse(acceso.token_valido("", ""))
        self.assertFalse(acceso.token_valido("abc", ""))

    def test_token_de_query_cookie_o_cabecera(self):
        def conexion(query=None, cookies=None, headers=None):
            return SimpleNamespace(query_params=query or {}, cookies=cookies or {}, headers=headers or {})

        self.assertEqual(acceso.token_de(conexion(query={"token": "q"}, cookies={acceso.COOKIE: "c"})), "q")
        self.assertEqual(acceso.token_de(conexion(cookies={acceso.COOKIE: "c"})), "c")
        self.assertEqual(acceso.token_de(conexion(headers={"authorization": "Bearer b"})), "b")
        self.assertEqual(acceso.token_de(conexion()), "")


@mock.patch.dict(os.environ, {"CAIN_TOKEN": TOKEN})
class TestAccesoHTTP(unittest.TestCase):

    def test_localhost_entra_sin_token(self):
        cliente = TestClient(app_mod.app, client=LOCAL)
        self.assertEqual(cliente.get("/api/memory").status_code, 200)

    def test_remoto_sin_token_no_entra(self):
        cliente = TestClient(app_mod.app)
        self.assertEqual(cliente.get("/api/memory").status_code, 401)
        self.assertEqual(cliente.get("/").status_code, 401)

    def test_remoto_sin_token_configurado_no_entra(self):
        with mock.patch.dict(os.environ, {"CAIN_TOKEN": ""}):
            cliente = TestClient(app_mod.app)
            self.assertEqual(cliente.get("/api/memory", params={"token": ""}).status_code, 401)

    def test_token_en_url_queda_en_cookie_y_se_quita_de_la_url(self):
        cliente   = TestClient(app_mod.app, follow_redirects=False)
        respuesta = cliente.get("/", params={"token": TOKEN})
        self.assertEqual(respuesta.status_code, 307)
        self.assertEqual(respuesta.headers["location"], "/")
        self.assertIn("httponly", respuesta.headers["set-cookie"].lower())
        # La cookie ya basta para las siguientes peticiones.
        self.assertEqual(cliente.get("/api/memory").status_code, 200)

    def test_token_incorrecto_no_entra(self):
        cliente = TestClient(app_mod.app)
        self.assertEqual(cliente.get("/api/memory", params={"token": "otro"}).status_code, 401)

    def test_websocket_remoto_sin_token_se_rechaza(self):
        from starlette.websockets import WebSocketDisconnect
        with TestClient(app_mod.app) as cliente:
            with self.assertRaises(WebSocketDisconnect):
                with cliente.websocket_connect("/ws"):
                    pass

    def test_websocket_remoto_con_token_entra(self):
        with TestClient(app_mod.app, headers={"authorization": f"Bearer {TOKEN}"}) as cliente:
            with cliente.websocket_connect("/ws") as ws:
                ws.send_json({"mensaje": "hola"})
                self.assertEqual(recibir_hasta(ws, "respuesta")[-1]["contenido"], "eco: hola")


class TestEstaticos(unittest.TestCase):

    def test_js_y_css_se_revalidan_siempre(self):
        # Si el navegador se queda con el JS viejo, el HTML nuevo queda a medias
        # (pasó con el botón del panel en el móvil).
        cliente = TestClient(app_mod.app, client=LOCAL)
        for ruta in ("/static/style.css", "/static/js/main.js"):
            self.assertEqual(cliente.get(ruta).headers["cache-control"], "no-cache")

    def test_index_pide_js_y_css_con_version(self):
        # Una URL nueva por versión: ninguna caché puede servir el JS viejo.
        cliente = TestClient(app_mod.app, client=LOCAL)
        html    = cliente.get("/").text
        version = app_mod.templates.env.globals["v"]
        self.assertIn(f'/static/js/main.js?v={version}"', html)
        self.assertIn(f'/static/style.css?v={version}"', html)
        self.assertNotIn('.js"', html.replace("three.min.js\"", ""))
        self.assertEqual(cliente.get(f"/static/js/main.js?v={version}").status_code, 200)


# ─── Historial ───────────────────────────────────────────────────────────────

class TestHistorial(unittest.TestCase):

    def test_historial_sin_etiqueta_de_animo(self):
        cliente  = TestClient(app_mod.app, client=LOCAL)
        mensajes = cliente.get("/api/historial").json()["mensajes"]
        self.assertEqual(mensajes, [
            {"rol": "user", "contenido": "hola"},
            {"rol": "cain", "contenido": "¡Bienvenido!"},
        ])


# ─── Varios dispositivos ─────────────────────────────────────────────────────

class TestVariosDispositivos(unittest.TestCase):

    def test_la_respuesta_llega_a_todos_los_dispositivos(self):
        with TestClient(app_mod.app, client=LOCAL) as cliente:
            with cliente.websocket_connect("/ws") as pc, cliente.websocket_connect("/ws") as movil:
                pc.send_json({"mensaje": "hola"})

                del_pc = recibir_hasta(pc, "memoria")
                self.assertEqual([d["tipo"] for d in del_pc], ["estado", "respuesta", "memoria"])

                del_movil = recibir_hasta(movil, "memoria")
                self.assertEqual(del_movil[0], {"tipo": "mensaje_usuario", "contenido": "hola"})
                respuesta = next(d for d in del_movil if d["tipo"] == "respuesta")
                self.assertEqual(respuesta["contenido"], "eco: hola")
                self.assertFalse(respuesta["voz"])

    def test_la_confirmacion_va_solo_a_quien_pidio_el_proyecto(self):
        with TestClient(app_mod.app, client=LOCAL) as cliente:
            with cliente.websocket_connect("/ws") as pc, cliente.websocket_connect("/ws") as movil:
                movil.send_json({"mensaje": "haz un proyecto"})
                self.assertEqual(recibir_hasta(movil, "confirmacion")[-1]["nombre"], "demo")

                movil.send_json({"tipo": "confirmacion_respuesta", "confirmado": True})
                self.assertEqual(recibir_hasta(movil, "respuesta")[-1]["contenido"], "confirmado: True")

                del_pc = recibir_hasta(pc, "respuesta")
                self.assertNotIn("confirmacion", [d["tipo"] for d in del_pc])
                self.assertEqual(del_pc[-1]["contenido"], "confirmado: True")

    def test_si_quien_confirma_se_desconecta_el_turno_se_cancela(self):
        with TestClient(app_mod.app, client=LOCAL) as cliente:
            with cliente.websocket_connect("/ws") as pc:
                with cliente.websocket_connect("/ws") as movil:
                    movil.send_json({"mensaje": "haz un proyecto"})
                    recibir_hasta(movil, "confirmacion")
                # El móvil se fue sin responder: no hay que esperar 5 minutos.
                self.assertEqual(recibir_hasta(pc, "respuesta")[-1]["contenido"], "confirmado: False")


# ─── Proyectos ───────────────────────────────────────────────────────────────

class TestProyectos(unittest.TestCase):

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="cain_proyectos_")
        os.makedirs(os.path.join(self.base, "web_1234", "css"))
        with open(os.path.join(self.base, "web_1234", "index.html"), "w", encoding="utf-8") as f:
            f.write("<h1>hola</h1>")
        with open(os.path.join(self.base, "web_1234", "css", "estilo.css"), "w", encoding="utf-8") as f:
            f.write("h1 {}")
        with open(os.path.join(self.base, "secreto.txt"), "w", encoding="utf-8") as f:
            f.write("no")
        parche = mock.patch.object(executor, "CARPETA_PROYECTOS", self.base)
        parche.start()
        self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.base)

    def test_rutas_dentro_del_proyecto(self):
        self.assertTrue(executor.carpeta_de_proyecto("web_1234"))
        self.assertTrue(executor.archivo_de_proyecto("web_1234", ""))
        self.assertTrue(executor.archivo_de_proyecto("web_1234", "css/estilo.css"))

    def test_no_se_puede_salir_de_la_carpeta(self):
        self.assertIsNone(executor.carpeta_de_proyecto(".."))
        self.assertIsNone(executor.carpeta_de_proyecto("no_existe"))
        self.assertIsNone(executor.archivo_de_proyecto("web_1234", "../secreto.txt"))
        self.assertIsNone(executor.archivo_de_proyecto("web_1234", "../../tests/__init__.py"))

    def test_html_principal(self):
        self.assertEqual(executor.html_principal(["app.js", "b.html", "index.html"]), "index.html")
        self.assertEqual(executor.html_principal(["juego.html", "app.js"]), "juego.html")
        self.assertIsNone(executor.html_principal(["main.py"]))

    def test_abrir_devuelve_url_relativa_servida_por_cain(self):
        cliente = TestClient(app_mod.app, client=LOCAL)
        datos   = cliente.post("/api/proyectos/web_1234/abrir").json()
        self.assertEqual(datos, {"tipo": "web", "url": "/proyectos/web_1234/index.html"})
        self.assertEqual(cliente.get(datos["url"]).text, "<h1>hola</h1>")
        self.assertEqual(cliente.get("/proyectos/web_1234/css/estilo.css").text, "h1 {}")
        self.assertEqual(cliente.get("/proyectos/web_1234/..%2Fsecreto.txt").status_code, 404)


if __name__ == "__main__":
    unittest.main()
