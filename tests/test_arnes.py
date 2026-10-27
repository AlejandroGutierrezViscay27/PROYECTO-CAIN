"""
Fase 10.0 — arnés de seguridad: lo que CAIN NO puede hacer.

Casi todos los casos son ataques: rutas que intentan salirse del espacio de
trabajo, tocar el sistema o el propio código de CAIN, y planes del LLM que
intentan escribir fuera de su carpeta. Cada uno debe fallar y quedar
registrado en la auditoría.
"""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from core import arnes, executor, tools
from core.arnes import auditoria, reglas, revision_codigo, rutas
from core.arnes.rutas import Denegado
from core.tool_schemas import TOOLS
from tests.test_director import BaseAgente

PERFIL      = os.path.expanduser("~")
SYSTEM32    = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")


class ConEspacio(unittest.TestCase):
    """Un espacio de trabajo vacío y propio para cada test."""

    def setUp(self):
        self.espacio = tempfile.mkdtemp(prefix="cain_espacio_")
        parche = mock.patch.object(reglas, "CARPETA_ESPACIO", self.espacio)
        parche.start()
        self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.espacio, ignore_errors=True)

    def denegada(self, texto, escritura=False):
        with self.assertRaises(Denegado, msg=texto):
            rutas.resolver(texto, self.espacio, escritura)


# ─── Rutas ───────────────────────────────────────────────────────────────────

class TestResolver(ConEspacio):

    def test_rutas_validas_quedan_dentro_del_espacio(self):
        for texto in ("notas.txt", "ideas/plan.md", os.path.join(self.espacio, "a.txt")):
            ruta = rutas.resolver(texto, self.espacio, escritura=True)
            self.assertTrue(rutas.dentro_de(ruta, self.espacio), texto)

    def test_no_se_sale_del_espacio(self):
        for texto in (r"..\..\Windows\System32\x.txt", "../fuera.txt", "ideas/../../fuera.txt",
                      r"C:/WINDOWS/system32/x.txt", r"c:\windows\SYSTEM32\x.txt",
                      os.path.join(reglas.RAIZ_CAIN, "core", "agent.py"),
                      os.path.join(PERFIL, "Desktop", "x.txt"), ".", "ideas/.."):
            self.denegada(texto)

    def test_formas_raras_de_escribir_una_ruta(self):
        for texto in (r"\\?\C:\Windows\x.txt", r"\\.\PhysicalDrive0", r"\\localhost\c$\Windows",
                      "//servidor/compartido/x.txt", r"%WINDIR%\x.txt", r"~\.ssh\id_rsa",
                      "$HOME/x.txt", "nota.txt:oculto", "a*b.txt", "a?.txt", "a\x00.txt",
                      "", "   ", "x" * 300):
            self.denegada(texto)

    def test_nombres_reservados_y_finales_engañosos(self):
        # Windows ignora el punto y el espacio finales: "agent.py." ES agent.py.
        for texto in ("CON", "nul.txt", "Aux", "com1.txt", "LPT9", "agent.py.", "nota.txt ", "carpeta./x.txt"):
            self.denegada(texto)

    def test_archivos_de_credenciales(self):
        for texto in (".env", "produccion.env", ".env.local", "llave.pem", "servidor.key",
                      "id_rsa", "id_ed25519.pub", "mis_credentials.txt", "claves.kdbx", ".git/config"):
            self.denegada(texto)

    def test_solo_se_escriben_extensiones_de_texto(self):
        for texto in ("x.bat", "x.exe", "x.ps1", "x.cmd", "x.lnk", "x.reg", "x.vbs", "x.dll", "sin_extension"):
            self.denegada(texto, escritura=True)
        # Leer sí (es solo leer).
        rutas.resolver("x.bat", self.espacio)

    @unittest.skipUnless(os.name == "nt" and os.path.isdir(SYSTEM32), "solo Windows")
    def test_junction_dentro_del_espacio_hacia_el_sistema(self):
        import _winapi
        for nombre, destino in (("atajo", SYSTEM32), ("repo", reglas.RAIZ_CAIN)):
            enlace = os.path.join(self.espacio, nombre)
            _winapi.CreateJunction(destino, enlace)
            self.addCleanup(os.rmdir, enlace)
            self.denegada(f"{nombre}/drivers/etc/hosts")
            self.denegada(f"{nombre}/nuevo.txt", escritura=True)


class TestVerificar(unittest.TestCase):

    def test_el_codigo_de_cain_esta_protegido(self):
        for partes in (("core", "agent.py"), (".env",), (".git", "config"), ("data", "memoria.json"),
                       ("tests", "__init__.py"), ("core", "arnes", "reglas.py"), ("CLAUDE.md",)):
            with self.assertRaises(Denegado, msg=partes):
                rutas.verificar(os.path.join(reglas.RAIZ_CAIN, *partes))

    def test_las_zonas_propias_si_se_pueden_usar(self):
        with mock.patch.object(reglas, "CARPETA_ESPACIO", os.path.join(reglas.RAIZ_CAIN, "espacio")), \
             mock.patch.object(reglas, "CARPETA_PROYECTOS", os.path.join(reglas.RAIZ_CAIN, "proyectos")):
            rutas.verificar(os.path.join(reglas.RAIZ_CAIN, "espacio", "notas.txt"))
            rutas.verificar(os.path.join(reglas.RAIZ_CAIN, "proyectos", "cubo_1", "index.html"))
            # Pero ni siquiera ahí un .env.
            with self.assertRaises(Denegado):
                rutas.verificar(os.path.join(reglas.RAIZ_CAIN, "espacio", ".env"))

    def test_sistema_y_carpetas_sensibles(self):
        for ruta in (os.path.join(SYSTEM32, "drivers", "etc", "hosts"), r"C:\Program Files\x",
                     r"C:\ProgramData\x", os.path.join(PERFIL, "AppData", "Local", "x"),
                     os.path.join(PERFIL, ".ssh", "id_rsa"), os.path.join(PERFIL, ".aws", "credentials")):
            with self.assertRaises(Denegado, msg=ruta):
                rutas.verificar(ruta)

    @unittest.skipUnless(os.path.isdir(r"C:\PROGRA~1"), "sin nombres cortos 8.3")
    def test_nombre_corto_8_3(self):
        with self.assertRaises(Denegado):
            rutas.verificar(r"C:\PROGRA~1\x.txt")

    def test_ninguna_ruta_del_sistema_cubre_el_perfil_del_usuario(self):
        # Pasó: "C:\Documents and Settings" es una junction a C:\Users y,
        # resuelta, prohibía todo. Las carpetas del usuario NO son del sistema.
        for nunca in reglas.rutas_nunca():
            self.assertFalse(rutas.dentro_de(PERFIL, nunca), nunca)
        rutas.verificar(os.path.join(PERFIL, "Documents", "x.txt"))

    def test_una_zona_en_el_sistema_se_rechaza_aunque_lo_diga_reglas(self):
        with self.assertRaises(Denegado):
            rutas.resolver("x.txt", SYSTEM32)


# ─── Evaluación de herramientas ──────────────────────────────────────────────

class TestEvaluar(unittest.TestCase):

    def test_toda_herramienta_declarada_tiene_nivel(self):
        nombres = {t["function"]["name"] for t in TOOLS}
        self.assertLessEqual(nombres, set(reglas.NIVEL_HERRAMIENTA))

    def test_herramienta_sin_nivel_se_rechaza(self):
        veredicto = arnes.evaluar("formatear_disco", {})
        self.assertFalse(veredicto.permitido)

    def test_argumentos_que_no_son_un_diccionario(self):
        self.assertFalse(arnes.evaluar("leer_archivo", "../.env").permitido)

    def test_niveles_y_confirmacion(self):
        self.assertFalse(arnes.evaluar("leer_archivo", {}).confirmar)
        self.assertTrue(arnes.evaluar("ejecutar_proyecto", {}).confirmar)
        self.assertTrue(arnes.evaluar("borrar_archivo", {}).confirmar)
        self.assertFalse(arnes.evaluar("memoria_olvidar", {"objetivo": "nombre"}).confirmar)
        self.assertEqual(arnes.evaluar("memoria_olvidar", {"objetivo": "todo"}).nivel, reglas.N3)

    def test_solo_local(self):
        with mock.patch.object(reglas, "SOLO_LOCAL", frozenset({"leer_archivo"})):
            self.assertTrue(arnes.evaluar("leer_archivo", {}, "local").permitido)
            self.assertFalse(arnes.evaluar("leer_archivo", {}, "remoto").permitido)
            # Cualquier origen que no sea exactamente "local" cuenta como remoto.
            self.assertFalse(arnes.evaluar("leer_archivo", {}, "LOCAL").permitido)

    def test_desde_el_movil_solo_hasta_n1(self):
        # Decisión del usuario: nada que envíe, borre o ejecute código desde fuera.
        for herramienta, args in (("leer_archivo", {}), ("crear_archivo", {}),
                                  ("editar_archivo", {}), ("memoria_olvidar", {"objetivo": "nombre"})):
            self.assertTrue(arnes.evaluar(herramienta, args, "remoto").permitido, herramienta)
        for herramienta, args in (("ejecutar_proyecto", {}), ("borrar_archivo", {}),
                                  ("memoria_olvidar", {"objetivo": "todo"})):
            self.assertFalse(arnes.evaluar(herramienta, args, "remoto").permitido, herramienta)
            self.assertTrue(arnes.evaluar(herramienta, args, "local").permitido, herramienta)

    def test_nivel_maximo_remoto(self):
        with mock.patch.object(reglas, "NIVEL_MAX_REMOTO", reglas.N1):
            self.assertTrue(arnes.evaluar("crear_archivo", {}, "remoto").permitido)
            self.assertFalse(arnes.evaluar("borrar_archivo", {}, "remoto").permitido)
            self.assertTrue(arnes.evaluar("borrar_archivo", {}, "local").permitido)

    def test_como_administrador_nada_por_encima_de_n1(self):
        with mock.patch.object(arnes, "_elevado", True):
            self.assertTrue(arnes.evaluar("crear_archivo", {}).permitido)
            self.assertFalse(arnes.evaluar("ejecutar_proyecto", {}).permitido)
            self.assertFalse(arnes.evaluar("borrar_archivo", {}).permitido)


# ─── El agente pasando por el arnés ──────────────────────────────────────────

class TestAgenteConArnes(BaseAgente):

    def setUp(self):
        super().setUp()
        self.espacio = tempfile.mkdtemp(prefix="cain_espacio_")
        self.auditoria = os.path.join(self.espacio, "..", os.path.basename(self.espacio) + ".jsonl")
        for parche in (mock.patch.object(reglas, "CARPETA_ESPACIO", self.espacio),
                       mock.patch.object(auditoria, "ARCHIVO_AUDITORIA", self.auditoria),
                       mock.patch.object(tools, "send2trash", side_effect=os.remove)):
            parche.start()
            self.addCleanup(parche.stop)
        self.addCleanup(shutil.rmtree, self.espacio, ignore_errors=True)
        self.addCleanup(lambda: os.path.exists(self.auditoria) and os.remove(self.auditoria))
        self.planes = []
        self.respuesta_confirmacion = True

        def confirmar(plan):
            self.planes.append(plan)
            return self.respuesta_confirmacion
        self.cain._confirmar_fn = confirmar

    def usar(self, herramienta, **argumentos):
        return self.cain._usar_herramienta(herramienta, argumentos)

    def escribir(self, nombre, texto="hola"):
        with open(os.path.join(self.espacio, nombre), "w", encoding="utf-8") as f:
            f.write(texto)

    def test_no_lee_el_env_ni_su_codigo(self):
        for nombre in (".env", "../.env", os.path.join(reglas.RAIZ_CAIN, ".env"),
                       os.path.join(reglas.RAIZ_CAIN, "core", "agent.py")):
            respuesta = self.usar("leer_archivo", nombre_archivo=nombre)
            self.assertTrue(respuesta.startswith("🛡️"), nombre)
            self.assertNotIn("OPENAI", respuesta)

    def test_no_se_borra_ni_se_edita_a_si_mismo(self):
        agente = os.path.join(reglas.RAIZ_CAIN, "core", "agent.py")
        for herramienta, args in (("borrar_archivo", {"nombre_archivo": agente}),
                                  ("borrar_archivo", {"nombre_archivo": "../core/agent.py"}),
                                  ("editar_archivo", {"nombre_archivo": agente, "instruccion": "x"}),
                                  ("crear_archivo", {"nombre_archivo": "../../main", "contenido": "x"})):
            self.assertTrue(self.usar(herramienta, **args).startswith("🛡️"), (herramienta, args))
        self.assertTrue(os.path.isfile(agente))
        self.assertEqual(self.planes, [])   # ni siquiera llegó a pedir confirmación

    def test_crear_queda_en_el_espacio_y_no_sobrescribe(self):
        self.usar("crear_archivo", nombre_archivo="notas", contenido="uno")
        self.usar("crear_archivo", nombre_archivo="notas", contenido="dos")
        self.assertEqual(sorted(os.listdir(self.espacio)), ["notas.txt", "notas_1.txt"])

    def test_crear_un_ejecutable_se_rechaza(self):
        self.assertTrue(self.usar("crear_archivo", nombre_archivo="virus.bat", contenido="x").startswith("🛡️"))
        self.assertEqual(os.listdir(self.espacio), [])

    def test_borrar_pide_confirmacion_y_va_a_la_papelera(self):
        self.escribir("viejo.txt")
        self.respuesta_confirmacion = False
        self.usar("borrar_archivo", nombre_archivo="viejo")
        self.assertTrue(os.path.exists(os.path.join(self.espacio, "viejo.txt")))
        self.assertEqual(self.planes[-1]["clase"], "accion")
        self.assertEqual(self.planes[-1]["nivel"], "N3")

        self.respuesta_confirmacion = True
        respuesta = self.usar("borrar_archivo", nombre_archivo="viejo")
        self.assertIn("Papelera", respuesta)
        self.assertFalse(os.path.exists(os.path.join(self.espacio, "viejo.txt")))
        tools.send2trash.assert_called_once()

    def test_solo_un_true_confirma(self):
        self.escribir("viejo.txt")
        for respuesta in ("si", 1, "true", [True], None):
            self.respuesta_confirmacion = respuesta
            self.usar("borrar_archivo", nombre_archivo="viejo")
            self.assertTrue(os.path.exists(os.path.join(self.espacio, "viejo.txt")), respuesta)

    def test_editar_guarda_la_version_anterior(self):
        self.escribir("plan.txt", "versión uno")
        with mock.patch.object(self.cain_mod().intent, "es_misma_intencion_archivo", return_value=True), \
             mock.patch.object(self.cain_mod().prompts, "generar_edicion_archivo", return_value="versión dos"):
            self.usar("editar_archivo", nombre_archivo="plan", instruccion="cámbialo")
        with open(os.path.join(self.espacio, "plan.txt"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "versión dos")
        respaldos = os.listdir(os.path.join(self.espacio, reglas.CARPETA_RESPALDOS))
        self.assertEqual(len(respaldos), 1)
        with open(os.path.join(self.espacio, reglas.CARPETA_RESPALDOS, respaldos[0]), encoding="utf-8") as f:
            self.assertEqual(f.read(), "versión uno")

    def test_olvidar_todo_se_confirma(self):
        self.cain.usuario_data = {"nombre": "Ana"}
        self.respuesta_confirmacion = False
        self.usar("memoria_olvidar", objetivo="todo")
        self.assertEqual(self.cain.usuario_data, {"nombre": "Ana"})
        self.respuesta_confirmacion = True
        self.usar("memoria_olvidar", objetivo="todo")
        self.assertEqual(self.cain.usuario_data, {})

    def test_todo_queda_en_la_auditoria(self):
        self.usar("leer_archivo", nombre_archivo=".env")
        self.usar("crear_archivo", nombre_archivo="ok", contenido="x")
        eventos = auditoria.ultimos()
        self.assertEqual([e["resultado"] for e in eventos], ["ejecutado", "denegado"])
        self.assertIn("credenciales", eventos[1]["motivo"])

    def cain_mod(self):
        from core import agent
        return agent


class TestProyectosConArnes(TestAgenteConArnes):

    def proyecto(self, archivos):
        from core import agent
        plan = {"nombre": "demo", "archivos": archivos}
        with mock.patch.object(agent.prompts, "generar_plan_proyecto", return_value=plan), \
             mock.patch.object(agent.executor, "ejecutar_proyecto", return_value=("ok", None, None)) as ejecutar:
            respuesta = self.usar("ejecutar_proyecto", descripcion="x", tipo="python")
        return respuesta, ejecutar

    def test_un_archivo_que_se_sale_de_su_carpeta_frena_todo(self):
        for nombre in ("../../core/agent.py", r"..\..\main.py", r"C:\Windows\x.py", "run.bat", ".env"):
            respuesta, ejecutar = self.proyecto({"main.py": "print(1)", nombre: "x"})
            self.assertTrue(respuesta.startswith("🛡️"), nombre)
            ejecutar.assert_not_called()
        self.assertEqual(self.planes, [])

    def test_codigo_que_nombra_una_ruta_prohibida_se_rechaza(self):
        hosts = os.path.join(SYSTEM32, "drivers", "etc", "hosts")
        respuesta, ejecutar = self.proyecto({"main.py": f"open(r'{hosts}', 'w')"})
        self.assertTrue(respuesta.startswith("🛡️"))
        ejecutar.assert_not_called()

    def test_la_confirmacion_avisa_de_lo_que_hace_el_codigo(self):
        self.proyecto({"main.py": "import os, subprocess\nos.remove('x')\n"})
        avisos = self.planes[-1]["advertencias"]
        self.assertIn("main.py: borra archivos", avisos)
        self.assertIn("main.py: lanza otros programas", avisos)


# ─── Revisión del código generado ────────────────────────────────────────────

class TestRevisionCodigo(unittest.TestCase):

    def avisos(self, codigo):
        return revision_codigo.revisar_python(codigo)

    def test_codigo_inocente_sin_avisos(self):
        self.assertEqual(self.avisos(
            "import os, math\nxs = [1, 2]\nxs.remove(1)\ns = 'a'.replace('a', 'b')\n"
            "print(os.path.join('a', 'b'))\n"), [])

    def test_avisos(self):
        self.assertIn("borra archivos", self.avisos("import os\nos.remove('x')"))
        self.assertIn("borra carpetas enteras", self.avisos("from shutil import rmtree"))
        self.assertIn("borra archivos", self.avisos("from pathlib import Path\nPath('x').unlink()"))
        self.assertIn("lanza otros programas", self.avisos("import subprocess"))
        self.assertIn("toca el registro de Windows", self.avisos("import winreg"))
        self.assertIn("ejecuta código construido en tiempo de ejecución", self.avisos("eval('1')"))
        self.assertIn("ejecuta comandos de consola", self.avisos("import os\nos.system('dir')"))

    def test_rutas_prohibidas_en_el_codigo(self):
        for literal in (os.path.join(reglas.RAIZ_CAIN, "core", "agent.py"), SYSTEM32 + "\\x",
                        os.path.join(PERFIL, ".ssh", "id_rsa")):
            with self.assertRaises(Denegado, msg=literal):
                revision_codigo.revisar_python(f"ruta = r'{literal}'")

    def test_ruta_de_red_avisa_sin_resolverla(self):
        self.assertIn("usa rutas de red", self.avisos(r"x = '\\\\servidor\\c$'"))


# ─── Ejecución del código generado ───────────────────────────────────────────

class TestEjecucion(unittest.TestCase):

    def test_el_codigo_generado_no_hereda_secretos(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-x", "CAIN_TOKEN": "t", "GITHUB_TOKEN": "g"}):
            entorno = executor.entorno_minimo()
        self.assertFalse({"OPENAI_API_KEY", "CAIN_TOKEN", "GITHUB_TOKEN"} & set(entorno))
        self.assertEqual(entorno["PYTHONIOENCODING"], "utf-8")
        self.assertIn("PATH", {k.upper() for k in entorno})

    def test_el_nombre_del_proyecto_no_se_sale(self):
        self.assertEqual(executor.nombre_seguro("../../core"), "core")
        self.assertEqual(executor.nombre_seguro(r"C:\Windows"), "c_windows")
        self.assertEqual(executor.nombre_seguro("..."), "proyecto_cain")

    def test_guardar_fuera_de_la_carpeta_del_proyecto(self):
        carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, carpeta, ignore_errors=True)
        with mock.patch.object(reglas, "CARPETA_PROYECTOS", os.path.dirname(carpeta)):
            executor.guardar_archivo_proyecto(carpeta, "css/estilo.css", "h1 {}")
            for nombre in ("../fuera.py", "x.exe", "con.py"):
                with self.assertRaises(Denegado, msg=nombre):
                    executor.guardar_archivo_proyecto(carpeta, nombre, "x")

    def test_la_correccion_automatica_no_puede_hacer_mas_de_lo_confirmado(self):
        carpeta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, carpeta, ignore_errors=True)
        ruta = os.path.join(carpeta, "main.py")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("print(1/0)")

        casos = (
            ("import subprocess\nsubprocess.run('dir')", [], "no confirmaste"),
            (f"open(r'{SYSTEM32}\\x', 'w')", [], "No ejecuté"),
        )
        for corregido, confirmadas, esperado in casos:
            with mock.patch.object(executor.prompts, "generar_correccion_codigo", return_value=corregido), \
                 mock.patch.object(executor, "ejecutar_python") as ejecutar:
                mensaje = executor.corregir_y_reintentar(None, ruta, "error", "original",
                                                         advertencias_confirmadas=confirmadas)
            ejecutar.assert_not_called()
            self.assertIn(esperado, mensaje)

        # Si el usuario ya confirmó ese aviso, la corrección sí corre.
        with mock.patch.object(executor.prompts, "generar_correccion_codigo",
                               return_value="import subprocess\nprint(1)"), \
             mock.patch.object(executor, "ejecutar_python", return_value=(True, "ok", None)) as ejecutar:
            executor.corregir_y_reintentar(None, ruta, "error", "original",
                                           advertencias_confirmadas=["main.py: lanza otros programas"])
        ejecutar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
