import unittest
from unittest import mock

from core import agent as agent_mod
from tests import mismo_llm_para_todos
from core import emocion, memory
from core.emocion import EstadoEmocional, extraer_animo
from voice.tts import PROSODIA_NEUTRAL, PROSODIA_POR_EMOCION, parametros_prosodia


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class TestExtraerAnimo(unittest.TestCase):

    def test_quita_la_etiqueta_y_lee_los_deltas(self):
        texto, deltas = extraer_animo("¡Gran idea!\n[[animo: entusiasmo +0.3, curiosidad 0.1]]")
        self.assertEqual(texto, "¡Gran idea!")
        self.assertEqual(deltas, {"entusiasmo": 0.3, "curiosidad": 0.1})

    def test_tolera_tildes_mayusculas_y_signos(self):
        _, deltas = extraer_animo("ok [[Ánimo: alegría=+0.2, tristeza: -0.1, inventada +0.5]]")
        self.assertEqual(deltas, {"alegria": 0.2, "tristeza": -0.1})

    def test_sin_etiqueta_o_vacia(self):
        self.assertEqual(extraer_animo("hola"), ("hola", {}))
        self.assertEqual(extraer_animo("hola\n[[animo: -]]"), ("hola", {}))

    def test_varias_etiquetas_usa_la_ultima_y_quita_todas(self):
        texto, deltas = extraer_animo("a [[animo: calma +0.1]] b\n[[animo: orgullo +0.2]]")
        self.assertEqual(texto, "a  b")
        self.assertEqual(deltas, {"orgullo": 0.2})


class TestEstadoEmocional(unittest.TestCase):

    def setUp(self):
        self.reloj = Reloj()
        self.estado = EstadoEmocional(reloj=self.reloj)

    def test_aplica_con_tope_y_acotado(self):
        aplicados = self.estado.aplicar({"entusiasmo": 0.9, "calma": -0.3, "inventada": 1})
        self.assertEqual(aplicados, {"entusiasmo": emocion.MAX_DELTA})   # calma ya estaba en 0
        self.estado.aplicar({"entusiasmo": 0.4})
        self.estado.aplicar({"entusiasmo": 0.4})
        self.assertEqual(self.estado.valores["entusiasmo"], 1.0)

    def test_lo_no_reforzado_se_desvanece_por_turno(self):
        self.estado.aplicar({"frustracion": 0.3, "entusiasmo": 0.2})
        self.estado.aplicar({"entusiasmo": 0.1})
        self.assertAlmostEqual(self.estado.valores["frustracion"], 0.3 * emocion.FACTOR_POR_TURNO)
        self.assertAlmostEqual(self.estado.valores["entusiasmo"], 0.3)   # reforzado: no se desvanece
        for _ in range(10):
            self.estado.aplicar({})
        self.assertEqual(self.estado.dominante(), ("neutral", 0.0))

    def test_dominante_y_neutral(self):
        self.assertEqual(self.estado.dominante(), ("neutral", 0.0))
        self.estado.aplicar({"curiosidad": 0.3, "alegria": 0.2})
        self.assertEqual(self.estado.dominante(), ("curiosidad", 0.3))

    def test_negativas_decaen_mas_rapido(self):
        self.estado.aplicar({"alegria": 0.4, "tristeza": 0.4})
        self.reloj.t += 120   # 2 minutos
        self.assertAlmostEqual(self.estado.valores["alegria"], 0.4, places=6)   # decae al leer
        self.estado.describir()
        self.assertAlmostEqual(self.estado.valores["alegria"], 0.4 - 0.04 * 2, places=6)
        self.assertAlmostEqual(self.estado.valores["tristeza"], 0.4 - 0.12 * 2, places=6)

    def test_describir(self):
        self.assertEqual(self.estado.describir(), "neutral, en calma")
        self.estado.aplicar({"picardia": 0.25})
        self.assertEqual(self.estado.describir(), "picardia 0.25")


class TestProsodia(unittest.TestCase):

    def test_neutral_y_desconocida_no_tocan_la_voz(self):
        self.assertEqual(parametros_prosodia("neutral", 1.0), PROSODIA_NEUTRAL)
        self.assertEqual(parametros_prosodia("inventada", 1.0), PROSODIA_NEUTRAL)

    def test_intensidad_maxima_llega_al_objetivo(self):
        self.assertEqual(parametros_prosodia("tristeza", 1.0), PROSODIA_POR_EMOCION["tristeza"])

    def test_emocion_suave_casi_no_se_nota(self):
        suave = parametros_prosodia("entusiasmo", 0.2)
        self.assertLess(abs(suave["length_scale"] - 1.0), 0.01)

    def test_todas_las_emociones_tienen_prosodia(self):
        self.assertEqual(set(PROSODIA_POR_EMOCION), set(emocion.EMOCIONES))


class LLMConAnimo:
    def chat(self, messages, temperature=0.7):
        return "¡Qué buena idea!\n[[animo: entusiasmo +0.3]]"

    def chat_with_tools(self, messages, tools, temperature=0.7):
        return {"tool_call": None}


class TestAnimoEnElAgente(unittest.TestCase):

    def setUp(self):
        parches = [
            mock.patch.object(agent_mod, "crear_llms", mismo_llm_para_todos(LLMConAnimo)),
            mock.patch.object(memory, "cargar_memoria", return_value=[]),
            mock.patch.object(memory, "cargar_usuario", return_value={}),
            mock.patch.object(memory, "cargar_memoria_larga", side_effect=memory.memoria_larga_vacia),
            mock.patch.object(memory, "guardar_memoria"),
            mock.patch.object(memory, "guardar_usuario"),
            mock.patch.object(agent_mod.intent, "detectar_intencion_llm", return_value="conversacion"),
            mock.patch.object(agent_mod.intent, "detectar_intereses_llm", return_value=[]),
        ]
        for p in parches:
            p.start()
            self.addCleanup(p.stop)
        self.cain = agent_mod.Cain()

    def test_la_etiqueta_no_llega_al_usuario(self):
        respuesta = self.cain.chat("hagamos un juego en 3D")
        self.assertEqual(respuesta, "¡Qué buena idea!")
        self.assertEqual(self.cain.emocion.dominante(), ("entusiasmo", 0.3))

    def test_el_historial_la_conserva_pero_el_director_no_la_ve(self):
        from core import director
        self.cain.chat("hola")
        self.assertIn("[[animo:", self.cain.historial[-1]["content"])
        texto = director._formatear_conversacion(self.cain.historial)
        self.assertEqual(texto, "Usuario: hola\nCAIN: ¡Qué buena idea!")

    def test_el_recordatorio_va_al_final(self):
        from core.prompts import RECORDATORIO_ANIMO
        with mock.patch.object(self.cain.llm, "chat", wraps=self.cain.llm.chat) as chat:
            self.cain.chat("hola")
        self.assertEqual(chat.call_args.args[0][-1], {"role": "system", "content": RECORDATORIO_ANIMO})

    def test_el_animo_entra_al_prompt(self):
        self.cain.chat("hola")
        with mock.patch.object(self.cain.llm, "chat", wraps=self.cain.llm.chat) as chat:
            self.cain.chat("otra")
        sistema = chat.call_args.args[0][0]["content"]
        self.assertIn("TU ESTADO DE ÁNIMO AHORA: entusiasmo 0.30", sistema)
        self.assertIn("[[animo:", sistema)


if __name__ == "__main__":
    unittest.main()
