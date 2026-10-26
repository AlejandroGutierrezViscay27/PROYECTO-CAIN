import unittest
from unittest import mock

from core import agent as agent_mod
from core import memory


class LLMFalso:
    """LLM de prueba: cuenta las llamadas de resumen y responde algo fijo."""

    def __init__(self):
        self.resumenes = []

    def chat(self, messages, temperature=0.7):
        contenido = messages[-1]["content"]
        if "sistema de memoria a largo plazo" in contenido:
            self.resumenes.append(contenido)
            return "resumen"
        return "respuesta"

    def chat_with_tools(self, messages, tools, temperature=0.7):
        return {"tool_call": None}


class TestResumen(unittest.TestCase):

    def setUp(self):
        # Nada de disco ni de red: memoria vacía y escrituras ignoradas.
        parches = [
            mock.patch.object(agent_mod, "OpenAIProvider", LLMFalso),
            mock.patch.object(memory, "cargar_memoria", return_value=[]),
            mock.patch.object(memory, "cargar_usuario", return_value={}),
            mock.patch.object(memory, "cargar_resumen", return_value=""),
            mock.patch.object(memory, "guardar_memoria"),
            mock.patch.object(memory, "guardar_usuario"),
            mock.patch.object(memory, "guardar_resumen"),
            mock.patch.object(agent_mod.intent, "detectar_intencion_llm", return_value="conversacion"),
            mock.patch.object(agent_mod.intent, "detectar_intereses_llm", return_value=[]),
        ]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)
        self.cain = agent_mod.Cain()

    def test_resumen_cada_intervalo_aunque_el_historial_este_lleno(self):
        # 40 turnos = 80 mensajes: el historial se llena (30) a los 15 turnos.
        # Antes, desde ahí se resumía en CADA turno (30 % 10 == 0).
        for i in range(40):
            self.cain.chat(f"mensaje {i}")

        self.assertEqual(len(self.cain.historial), memory.MAX_HISTORIAL)
        # Se resume al empezar los turnos 6, 11, 16, ... 36 → 7 veces.
        self.assertEqual(len(self.cain.llm.resumenes), 7)

    def test_resumen_solo_ve_mensajes_nuevos(self):
        for i in range(11):
            self.cain.chat(f"mensaje {i}")
        for i in range(11, 16):
            self.cain.chat(f"mensaje {i}")

        segundo = self.cain.llm.resumenes[1]
        self.assertNotIn("mensaje 4\n", segundo)   # ya estaba en el primer resumen
        self.assertIn("Usuario: mensaje 5", segundo)
        self.assertIn("CAIN: respuesta", segundo)

    def test_olvidar_historial_reinicia_el_contador(self):
        for i in range(4):
            self.cain.chat(f"mensaje {i}")
        self.cain._memoria_olvidar({"objetivo": "historial"})
        self.assertEqual(self.cain.mensajes_sin_resumir, 0)


class TestCanalVoz(unittest.TestCase):

    def test_prompt_de_voz_solo_en_canal_voz(self):
        from core.prompts import construir_prompt, SUFIJO_VOZ
        self.assertIn(SUFIJO_VOZ, construir_prompt("conversacion", {}, "", canal="voz"))
        self.assertNotIn(SUFIJO_VOZ, construir_prompt("conversacion", {}, ""))


if __name__ == "__main__":
    unittest.main()
