import json
import os
import tempfile
import threading
import unittest
from unittest import mock

from core import agent as agent_mod
from core import director, memory

RESPUESTA_DIRECTOR = {
    "notas": "Está construyendo CAIN y prefiere código comentado.",
    "eventos_cerrados": ["Arreglamos juntos el bug del resumen."],
    "temas_abiertos": ["probar el VAD con su micrófono"],
    "guia": {"lectura_usuario": "creador enfocado", "temas_proactivos": ["la Fase 9"]},
}


class LLMFalso:
    """LLM de prueba: registra las pasadas del director y responde algo fijo."""

    def __init__(self, respuesta_director=None):
        self.prompts_director = []
        self.respuesta_director = respuesta_director or json.dumps(RESPUESTA_DIRECTOR)

    def chat(self, messages, temperature=0.7):
        contenido = messages[-1]["content"]
        if "director de memoria" in contenido:
            self.prompts_director.append(contenido)
            return self.respuesta_director
        return "respuesta"

    def chat_with_tools(self, messages, tools, temperature=0.7):
        return {"tool_call": None}


class HiloSincrono:
    """Sustituto de threading.Thread que corre el target en el momento."""

    def __init__(self, target, args=(), daemon=None):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)

    def is_alive(self):
        return False


class BaseAgente(unittest.TestCase):
    hilo = HiloSincrono

    def setUp(self):
        # Nada de disco ni de red.
        self.guardar_larga = mock.MagicMock()
        parches = [
            mock.patch.object(agent_mod, "OpenAIProvider", LLMFalso),
            mock.patch.object(memory, "cargar_memoria", return_value=[]),
            mock.patch.object(memory, "cargar_usuario", return_value={}),
            mock.patch.object(memory, "cargar_memoria_larga", side_effect=memory.memoria_larga_vacia),
            mock.patch.object(memory, "guardar_memoria"),
            mock.patch.object(memory, "guardar_usuario"),
            mock.patch.object(memory, "guardar_memoria_larga", self.guardar_larga),
            mock.patch.object(memory, "limpiar_historial_completo"),
            mock.patch.object(agent_mod.intent, "detectar_intencion_llm", return_value="conversacion"),
            mock.patch.object(agent_mod.intent, "detectar_intereses_llm", return_value=[]),
        ]
        if self.hilo:
            parches.append(mock.patch.object(agent_mod.threading, "Thread", self.hilo))
        for p in parches:
            p.start()
            self.addCleanup(p.stop)
        self.cain = agent_mod.Cain()


class TestDirectorEnElAgente(BaseAgente):

    def test_pasa_cada_intervalo_aunque_el_historial_este_lleno(self):
        # 40 turnos = 80 mensajes; el historial se llena (30) a los 15 turnos.
        for i in range(40):
            self.cain.chat(f"mensaje {i}")
        self.assertEqual(len(self.cain.historial), memory.MAX_HISTORIAL)
        # Pasa al terminar los turnos 5, 10, ..., 40 → 8 veces.
        self.assertEqual(len(self.cain.llm.prompts_director), 8)

    def test_solo_ve_mensajes_nuevos_etiquetados(self):
        for i in range(10):
            self.cain.chat(f"mensaje {i}")
        segundo = self.cain.llm.prompts_director[1]
        self.assertNotIn("mensaje 4\n", segundo)   # ya lo vio la primera pasada
        self.assertIn("Usuario: mensaje 5", segundo)
        self.assertIn("CAIN: respuesta", segundo)

    def test_la_memoria_entra_al_prompt_de_cain(self):
        for i in range(5):
            self.cain.chat(f"mensaje {i}")
        self.guardar_larga.assert_called()
        with mock.patch.object(self.cain.llm, "chat", wraps=self.cain.llm.chat) as chat:
            self.cain.chat("otro")
        sistema = chat.call_args_list[-1].args[0][0]["content"]
        self.assertIn("prefiere código comentado", sistema)
        self.assertIn("probar el VAD", sistema)
        self.assertNotIn("la Fase 9", sistema)   # temas_proactivos no se inyecta

    def test_si_el_director_falla_los_mensajes_vuelven_a_la_cola(self):
        self.cain.llm.respuesta_director = "no es json"
        for i in range(5):
            self.cain.chat(f"mensaje {i}")
        self.assertEqual(len(self.cain.llm.prompts_director), 2)   # intento + reintento
        self.assertEqual(self.cain.mensajes_sin_resumir, 10)
        self.assertEqual(self.cain.memoria_larga["notas"], "")
        self.guardar_larga.assert_not_called()

    def test_olvidar_historial_reinicia_todo(self):
        for i in range(5):
            self.cain.chat(f"mensaje {i}")
        self.cain._memoria_olvidar({"objetivo": "historial"})
        self.assertEqual(self.cain.mensajes_sin_resumir, 0)
        self.assertEqual(self.cain.memoria_larga, memory.memoria_larga_vacia())


class TestDirectorEnSegundoPlano(BaseAgente):
    hilo = None   # hilos reales

    def test_resultado_tardio_tras_olvidar_se_descarta(self):
        liberar = threading.Event()
        original = self.cain.llm.chat

        def chat_lento(messages, temperature=0.7):
            if "director de memoria" in messages[-1]["content"]:
                liberar.wait(5)
            return original(messages, temperature)

        self.cain.llm.chat = chat_lento
        for i in range(5):
            self.cain.chat(f"mensaje {i}")      # el director queda bloqueado
        self.assertTrue(self.cain._director_en_curso())

        self.cain._memoria_olvidar({"objetivo": "historial"})
        liberar.set()
        self.cain._hilo_director.join(5)

        self.assertEqual(self.cain.memoria_larga["notas"], "")
        self.guardar_larga.assert_not_called()


class TestAplicarResultado(unittest.TestCase):

    def test_versiona_notas_y_archiva_eventos(self):
        mem = memory.memoria_larga_vacia()
        mem["notas"] = "notas viejas"
        director.aplicar_resultado(mem, RESPUESTA_DIRECTOR)
        self.assertEqual(mem["notas"], RESPUESTA_DIRECTOR["notas"])
        self.assertEqual(mem["historial_notas"][0]["notas"], "notas viejas")
        self.assertEqual(mem["eventos_archivados"][0]["evento"], "Arreglamos juntos el bug del resumen.")
        self.assertEqual(mem["temas_abiertos"], ["probar el VAD con su micrófono"])

    def test_hechos_solo_se_anaden_o_se_quitan_por_numero(self):
        mem = memory.memoria_larga_vacia()
        mem["hechos"] = ["Tiene una perrita.", "Usa Windows.", "Programa en Java."]
        director.aplicar_resultado(mem, {
            "hechos_nuevos": ["Programa en Python.", "tiene una perrita."],  # el 2º ya estaba
            "hechos_obsoletos": [3, 99, "1"],                                  # 99 y "1" se ignoran
        })
        self.assertEqual(mem["hechos"], ["Tiene una perrita.", "Usa Windows.", "Programa en Python."])

    def test_sin_hechos_en_la_respuesta_no_se_pierde_ninguno(self):
        mem = memory.memoria_larga_vacia()
        mem["hechos"] = ["Tiene una perrita."]
        director.aplicar_resultado(mem, {"notas": "otra cosa"})
        self.assertEqual(mem["hechos"], ["Tiene una perrita."])

    def test_campos_invalidos_no_borran_lo_que_habia(self):
        mem = memory.memoria_larga_vacia()
        mem.update(notas="se queda", temas_abiertos=["sigue"], guia={"riesgos": "x"})
        director.aplicar_resultado(mem, {"notas": "", "temas_abiertos": "no es lista",
                                         "guia": None, "eventos_cerrados": [3, " ", "ok"]})
        self.assertEqual(mem["notas"], "se queda")
        self.assertEqual(mem["temas_abiertos"], ["sigue"])
        self.assertEqual(mem["guia"], {"riesgos": "x"})
        self.assertEqual([e["evento"] for e in mem["eventos_archivados"]], ["ok"])


class TestParsearJson(unittest.TestCase):

    def test_tolera_envolturas_tipicas(self):
        self.assertEqual(director.parsear_json('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(director.parsear_json('Claro: {"a": [1, 2,],}'), {"a": [1, 2]})
        self.assertIsNone(director.parsear_json("nada"))
        self.assertIsNone(director.parsear_json("[1, 2]"))


class TestPersistencia(unittest.TestCase):

    def setUp(self):
        carpeta = tempfile.mkdtemp()
        self.rutas = {n: os.path.join(carpeta, n) for n in ("larga.json", "resumen.txt")}
        for nombre, ruta in (("ARCHIVO_LARGA", "larga.json"), ("ARCHIVO_RESUMEN", "resumen.txt")):
            p = mock.patch.object(memory, nombre, self.rutas[ruta])
            p.start()
            self.addCleanup(p.stop)

    def test_migra_el_resumen_viejo(self):
        with open(self.rutas["resumen.txt"], "w", encoding="utf-8") as f:
            f.write("Le gusta la ciencia ficción.\n")
        self.assertEqual(memory.cargar_memoria_larga()["hechos"],
                         ["De conversaciones anteriores: Le gusta la ciencia ficción."])

    def test_guardar_y_cargar(self):
        mem = memory.memoria_larga_vacia()
        mem["notas"] = "ñandú"
        mem["historial_notas"] = [{"ts": i, "notas": str(i)} for i in range(30)]
        memory.guardar_memoria_larga(mem)
        cargada = memory.cargar_memoria_larga()
        self.assertEqual(cargada["notas"], "ñandú")
        self.assertEqual(len(cargada["historial_notas"]), memory.MAX_VERSIONES_NOTAS)
        # sin temporales sueltos
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.rutas["larga.json"]))), ["larga.json"])

    def test_json_corrupto_no_tumba_la_carga(self):
        with open(self.rutas["larga.json"], "w", encoding="utf-8") as f:
            f.write('{"notas": "cortado')
        self.assertEqual(memory.cargar_memoria_larga(), memory.memoria_larga_vacia())


class TestCanalVoz(unittest.TestCase):

    def test_prompt_de_voz_solo_en_canal_voz(self):
        from core.prompts import construir_prompt, SUFIJO_VOZ
        self.assertIn(SUFIJO_VOZ, construir_prompt("conversacion", {}, "", canal="voz"))
        self.assertNotIn(SUFIJO_VOZ, construir_prompt("conversacion", {}, ""))


if __name__ == "__main__":
    unittest.main()
