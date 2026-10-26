"""
Estado emocional de CAIN (inspirado en el de OpenSakura, reducido a lo que
le pega a un maestro de ceremonias).

El modelo no responde en JSON: cierra cada respuesta con una etiqueta
[[animo: entusiasmo +0.3, curiosidad +0.1]] que extraer_animo() lee y quita.
Las emociones decaen solas con el tiempo; las negativas, más rápido, para
que CAIN no se quede de mal humor.
"""
import re
import time

EMOCIONES = (
    "entusiasmo", "alegria", "curiosidad", "orgullo", "picardia",
    "calma", "sorpresa", "preocupacion", "frustracion", "tristeza",
)
NEGATIVAS = {"preocupacion", "frustracion", "tristeza"}

DECAIMIENTO_POR_MINUTO = 0.04   # una emoción a 0.6 tarda ~15 min en apagarse
FACTOR_NEGATIVAS       = 3.0    # ... y una negativa, ~5 min
MAX_DELTA              = 0.4
UMBRAL_DOMINANTE       = 0.1    # por debajo, CAIN está neutral
# Además del tiempo, cada respuesta desvanece lo que no reforzó: el modelo
# casi nunca manda deltas negativos, y sin esto la frustración de hace cinco
# mensajes seguiría ahí aunque el problema ya se resolvió.
FACTOR_POR_TURNO       = 0.85

_ETIQUETA = re.compile(r"\[\[\s*[aá]nimo\s*:(.*?)\]\]", re.I | re.S)
_PAR      = re.compile(r"([a-záéíóúñ]+)\s*[:=]?\s*([+-]?\d*\.?\d+)", re.I)
_SIN_TILDES = str.maketrans("áéíóú", "aeiou")


def extraer_animo(texto):
    """
    Separa la respuesta de la etiqueta de ánimo.

    Returns:
        (texto_limpio, deltas) — deltas es {emocion: float}, solo con
        emociones válidas. Sin etiqueta, deltas es {}.
    """
    coincidencias = _ETIQUETA.findall(texto or "")
    limpio = _ETIQUETA.sub("", texto or "").strip()
    deltas = {}
    if coincidencias:
        for nombre, valor in _PAR.findall(coincidencias[-1]):
            nombre = nombre.lower().translate(_SIN_TILDES)
            if nombre in EMOCIONES:
                try:
                    deltas[nombre] = float(valor)
                except ValueError:
                    continue
    return limpio, deltas


class EstadoEmocional:

    def __init__(self, reloj=time.time):
        self._reloj  = reloj
        self._ultimo = reloj()
        self.valores = {e: 0.0 for e in EMOCIONES}

    def _decaer(self):
        ahora   = self._reloj()
        minutos = max(0.0, ahora - self._ultimo) / 60.0
        self._ultimo = ahora
        if minutos <= 0:
            return
        for e, v in self.valores.items():
            if v > 0:
                tasa = DECAIMIENTO_POR_MINUTO * (FACTOR_NEGATIVAS if e in NEGATIVAS else 1.0)
                self.valores[e] = max(0.0, v - tasa * minutos)

    def aplicar(self, deltas):
        """
        Un turno de conversación: desvanece las emociones que no aparecen en
        deltas, suma los deltas (acotados a ±MAX_DELTA) y retorna los aplicados.
        """
        self._decaer()
        deltas = {e: d for e, d in (deltas or {}).items() if e in self.valores}
        for e in self.valores:
            if e not in deltas:
                self.valores[e] *= FACTOR_POR_TURNO
        aplicados = {}
        for e, d in deltas.items():
            d = max(-MAX_DELTA, min(MAX_DELTA, float(d)))
            nuevo = max(0.0, min(1.0, self.valores[e] + d))
            if nuevo != self.valores[e]:
                aplicados[e] = round(nuevo - self.valores[e], 3)
                self.valores[e] = nuevo
        return aplicados

    def dominante(self):
        """(emocion, intensidad) de la emoción más fuerte, o ("neutral", 0.0)."""
        self._decaer()
        nombre, valor = max(self.valores.items(), key=lambda kv: kv[1])
        if valor < UMBRAL_DOMINANTE:
            return "neutral", 0.0
        return nombre, round(valor, 3)

    def describir(self):
        """Texto corto del ánimo actual para el prompt de sistema."""
        self._decaer()
        activas = sorted(((e, v) for e, v in self.valores.items() if v >= 0.05),
                         key=lambda kv: kv[1], reverse=True)
        if not activas:
            return "neutral, en calma"
        return ", ".join(f"{e} {v:.2f}" for e, v in activas[:4])

    def reiniciar(self):
        self.valores = {e: 0.0 for e in EMOCIONES}
        self._ultimo = self._reloj()
