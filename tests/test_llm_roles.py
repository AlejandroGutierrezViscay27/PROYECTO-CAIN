import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from core import agent as agent_mod
from core import memory
from llm import fabrica, registro
from llm.ollama_provider import OllamaProvider
from llm.openai_provider import OpenAIProvider
from llm.registro import RegistroUso
from tests.test_director import HiloSincrono, RESPUESTA_DIRECTOR

SIN_LLM_ENV = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
SIN_LLM_ENV["OPENAI_API_KEY"] = "sk-prueba"   # el cliente la exige; no se llama a la red


class ClienteFalso:
    """Imita client.chat.completions.create() con un uso de tokens fijo."""

    def __init__(self, texto="hola", entrada=100, salida=20):
        self.texto, self.entrada, self.salida = texto, entrada, salida
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))
        self.llamadas = []

    def _crear(self, **kwargs):
        self.llamadas.append(kwargs)
        mensaje = SimpleNamespace(content=self.texto, tool_calls=None)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=mensaje)],
            usage=SimpleNamespace(prompt_tokens=self.entrada, completion_tokens=self.salida),
        )


class TestConfigRol(unittest.TestCase):

    def entorno(self, **extra):
        return mock.patch.dict(os.environ, {**SIN_LLM_ENV, **extra}, clear=True)

    def test_sin_configurar_todo_es_como_antes(self):
        with self.entorno():
            for rol in fabrica.ROLES:
                self.assertEqual(fabrica.config_rol(rol), ("openai", "gpt-4o-mini"))

    def test_el_rol_sobreescribe_al_general(self):
        with self.entorno(LLM_MODEL="gpt-4.1-mini", LLM_MODEL_CODIGO="gpt-4.1"):
            self.assertEqual(fabrica.config_rol("codigo"), ("openai", "gpt-4.1"))
            self.assertEqual(fabrica.config_rol("director"), ("openai", "gpt-4.1-mini"))

    def test_cambiar_de_proveedor_no_hereda_el_modelo_general(self):
        with self.entorno(LLM_MODEL="gpt-4o-mini", LLM_PROVIDER_DIRECTOR="Ollama"):
            self.assertEqual(fabrica.config_rol("director"), ("ollama", "llama3.1"))
        with self.entorno(LLM_PROVIDER_DIRECTOR="ollama", LLM_MODEL_DIRECTOR="qwen2.5:7b"):
            self.assertEqual(fabrica.config_rol("director"), ("ollama", "qwen2.5:7b"))

    def test_proveedor_desconocido_falla_al_arrancar(self):
        with self.entorno(LLM_PROVIDER_INTENCION="gemini"):
            with self.assertRaises(ValueError):
                fabrica.config_rol("intencion")

    def test_crear_llms_un_proveedor_por_rol_con_cliente_compartido(self):
        with self.entorno(LLM_PROVIDER_DIRECTOR="ollama", LLM_MODEL_CODIGO="gpt-4.1"):
            llms = fabrica.crear_llms(RegistroUso(ruta=os.path.join(tempfile.mkdtemp(), "uso.json")))
        self.assertEqual(set(llms), set(fabrica.ROLES))
        self.assertIsInstance(llms["director"], OllamaProvider)
        self.assertEqual(llms["codigo"].model, "gpt-4.1")
        self.assertIs(llms["conversacion"].client, llms["codigo"].client)
        self.assertIsNot(llms["conversacion"].client, llms["director"].client)
        self.assertIn("11434", str(llms["director"].client.base_url))


class TestRegistroUso(unittest.TestCase):

    def setUp(self):
        self.ruta = os.path.join(tempfile.mkdtemp(), "uso.json")
        self.registro = RegistroUso(ruta=self.ruta, reloj=lambda: 1_790_000_000)

    def test_el_proveedor_anota_cada_llamada_con_su_rol(self):
        cliente = ClienteFalso(entrada=1000, salida=200)
        llm = OpenAIProvider(model="gpt-4o-mini", client=cliente,
                             al_usar=lambda m, e, s: self.registro.anotar("director", "openai", m, e, s))
        llm.chat([{"role": "user", "content": "x"}])
        llm.chat_with_tools([{"role": "user", "content": "x"}], tools=[])
        fila = self.registro.resumen()["roles"]["director"]["openai:gpt-4o-mini"]
        self.assertEqual((fila["llamadas"], fila["entrada"], fila["salida"]), (2, 2000, 400))

    def test_costos(self):
        self.registro.anotar("conversacion", "openai", "gpt-4o-mini", 1_000_000, 1_000_000)
        self.registro.anotar("director", "ollama", "qwen2.5:7b", 5000, 500)
        resumen = self.registro.resumen()
        self.assertAlmostEqual(resumen["costo_usd"], 0.75)
        self.assertEqual(resumen["roles"]["director"]["ollama:qwen2.5:7b"]["costo_usd"], 0.0)
        self.assertFalse(resumen["costo_incompleto"])

        self.registro.anotar("codigo", "openai", "modelo-del-futuro", 10, 10)
        resumen = self.registro.resumen()
        self.assertIsNone(resumen["roles"]["codigo"]["openai:modelo-del-futuro"]["costo_usd"])
        self.assertTrue(resumen["costo_incompleto"])

    def test_se_agrega_por_dia(self):
        self.registro.anotar("intencion", "openai", "gpt-4o-mini", 10, 1)
        self.registro._reloj = lambda: 1_790_000_000 + 86_400
        self.registro.anotar("intencion", "openai", "gpt-4o-mini", 10, 1)
        with open(self.ruta, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["dias"]), 2)
        self.assertEqual(self.registro.resumen_hoy()["roles"]["intencion"]["openai:gpt-4o-mini"]["llamadas"], 1)
        self.assertEqual(self.registro.resumen()["roles"]["intencion"]["openai:gpt-4o-mini"]["llamadas"], 2)

    def test_un_archivo_corrupto_no_tumba_el_turno(self):
        with open(self.ruta, "w") as f:
            f.write("{no es json")
        self.registro.anotar("conversacion", "openai", "gpt-4o-mini", 1, 1)
        self.assertEqual(self.registro.resumen()["roles"]["conversacion"]["openai:gpt-4o-mini"]["llamadas"], 1)


class LLMDeRol:
    """LLM de prueba que apunta qué rol recibió cada llamada."""

    def __init__(self, rol, llamadas):
        self.rol, self.llamadas = rol, llamadas

    def chat(self, messages, temperature=0.7):
        self.llamadas.append(self.rol)
        if "director de memoria" in messages[-1]["content"]:
            return json.dumps(RESPUESTA_DIRECTOR)
        if self.rol == "intencion":
            return "ninguno" if "intereses" in messages[0]["content"] else "conversacion"
        return "respuesta\n[[animo: -]]"

    def chat_with_tools(self, messages, tools, temperature=0.7):
        self.llamadas.append(self.rol)
        return {"content": None, "tool_call": None}


class TestRutasEnElAgente(unittest.TestCase):

    def setUp(self):
        self.llamadas = []
        llms = {rol: LLMDeRol(rol, self.llamadas) for rol in fabrica.ROLES}
        parches = [
            mock.patch.object(agent_mod, "crear_llms", lambda registro=None: llms),
            mock.patch.object(agent_mod.threading, "Thread", HiloSincrono),
            mock.patch.object(memory, "cargar_memoria", return_value=[]),
            mock.patch.object(memory, "cargar_usuario", return_value={}),
            mock.patch.object(memory, "cargar_memoria_larga", side_effect=memory.memoria_larga_vacia),
            mock.patch.object(memory, "guardar_memoria"),
            mock.patch.object(memory, "guardar_usuario"),
            mock.patch.object(memory, "guardar_memoria_larga"),
        ]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)
        self.cain = agent_mod.Cain()

    def test_cada_tarea_va_a_su_rol(self):
        self.cain.chat("hola")
        self.assertEqual(self.llamadas[0], "enrutador")
        self.assertIn("intencion", self.llamadas)
        self.assertEqual(self.llamadas[-1], "conversacion")
        self.assertNotIn("director", self.llamadas)

        for _ in range(agent_mod.INTERVALO_DIRECTOR // 2 - 1):
            self.cain.chat("otra")
        self.assertEqual(self.llamadas[-1], "director")
        self.assertNotIn("codigo", self.llamadas)

    def test_el_agente_usa_el_registro_redirigido_en_pruebas(self):
        self.assertEqual(self.cain.registro_uso.ruta, registro.ARCHIVO_USO)
        self.assertNotIn("data", os.path.relpath(registro.ARCHIVO_USO).split(os.sep)[:1])


if __name__ == "__main__":
    unittest.main()
