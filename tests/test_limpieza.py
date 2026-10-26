import unittest

from voice.limpieza import limpiar_para_voz, AVISO_CODIGO


class TestLimpiarParaVoz(unittest.TestCase):

    def test_quita_emojis(self):
        self.assertEqual(limpiar_para_voz("🎭 ¡El espectáculo está en vivo!"),
                         "¡El espectáculo está en vivo!")

    def test_reemplaza_bloque_de_codigo(self):
        texto = "Aquí tienes:\n```python\nprint('hola')\n```\nPruébalo."
        resultado = limpiar_para_voz(texto)
        self.assertNotIn("print", resultado)
        self.assertIn(AVISO_CODIGO.strip(), resultado)
        self.assertTrue(resultado.endswith("Pruébalo."))

    def test_bloque_de_codigo_sin_cerrar(self):
        resultado = limpiar_para_voz("Mira:\n```js\nconst x = 1;")
        self.assertNotIn("const", resultado)

    def test_quita_markdown(self):
        texto = "## Título\n**negrita** y *cursiva* con `codigo`"
        self.assertEqual(limpiar_para_voz(texto),
                         "Título. negrita y cursiva con codigo.")

    def test_listas_se_vuelven_frases(self):
        texto = "Opciones:\n- primera\n- segunda\n1. tercera"
        self.assertEqual(limpiar_para_voz(texto),
                         "Opciones: primera. segunda. tercera.")

    def test_enlaces_y_urls(self):
        self.assertEqual(limpiar_para_voz("Ver [la guía](http://x.com)"), "Ver la guía.")
        self.assertEqual(limpiar_para_voz("Abierto en http://localhost:8001"),
                         "Abierto en el enlace del chat.")

    def test_respeta_puntos_suspensivos(self):
        self.assertEqual(limpiar_para_voz("He creado algo para este espectáculo..."),
                         "He creado algo para este espectáculo...")

    def test_guiones_bajos_de_nombres(self):
        self.assertEqual(limpiar_para_voz("Proyecto numeros_fibonacci listo."),
                         "Proyecto numeros fibonacci listo.")

    def test_solo_emojis_queda_vacio(self):
        self.assertEqual(limpiar_para_voz("🎭✨"), "")
        self.assertEqual(limpiar_para_voz(""), "")


if __name__ == "__main__":
    unittest.main()
