import io
import math
import os
import wave
from pathlib import Path

import httpx
from piper import PiperVoice, SynthesisConfig
from voice.base import TextToSpeech

VOICE_PATH = Path("data/voices/es_MX-claude-high.onnx")

# ─── Prosodia por emoción (Piper) ────────────────────────────────────────────
# Piper no tiene etiquetas de emoción como GPT-SoVITS, pero sí cuatro perillas:
#   length_scale  → duración (<1 más rápido, >1 más lento)
#   noise_scale   → variación de entonación (más alto = más expresivo)
#   noise_w_scale → variación del ritmo
#   volume        → volumen
# Valores a intensidad máxima; NEUTRAL son los de la voz es_MX-claude-high.

PROSODIA_NEUTRAL = {"length_scale": 1.0, "noise_scale": 0.667, "noise_w_scale": 0.8, "volume": 1.0}

PROSODIA_POR_EMOCION = {
    "entusiasmo":   {"length_scale": 0.88, "noise_scale": 0.80, "noise_w_scale": 0.90, "volume": 1.0},
    "alegria":      {"length_scale": 0.94, "noise_scale": 0.75, "noise_w_scale": 0.85, "volume": 1.0},
    "curiosidad":   {"length_scale": 0.97, "noise_scale": 0.72, "noise_w_scale": 0.85, "volume": 1.0},
    "orgullo":      {"length_scale": 1.04, "noise_scale": 0.70, "noise_w_scale": 0.80, "volume": 1.0},
    "picardia":     {"length_scale": 0.93, "noise_scale": 0.80, "noise_w_scale": 0.95, "volume": 1.0},
    "calma":        {"length_scale": 1.10, "noise_scale": 0.55, "noise_w_scale": 0.70, "volume": 0.90},
    "sorpresa":     {"length_scale": 0.90, "noise_scale": 0.85, "noise_w_scale": 0.95, "volume": 1.0},
    "preocupacion": {"length_scale": 1.05, "noise_scale": 0.60, "noise_w_scale": 0.75, "volume": 0.90},
    "frustracion":  {"length_scale": 0.92, "noise_scale": 0.75, "noise_w_scale": 0.90, "volume": 1.0},
    "tristeza":     {"length_scale": 1.18, "noise_scale": 0.50, "noise_w_scale": 0.65, "volume": 0.80},
}


def _curva_s(x, pendiente=8.0, centro=0.6):
    """
    Sigmoide normalizada a [0, 1] (como la de OpenSakura): las emociones
    suaves casi no tocan la voz y solo una emoción fuerte llega al extremo.
    0.3 → ~0.08, 0.6 → ~0.52, 0.9 → ~0.95.
    """
    x = max(0.0, min(1.0, x))
    s = lambda v: 1.0 / (1.0 + math.exp(-pendiente * (v - centro)))
    return (s(x) - s(0.0)) / (s(1.0) - s(0.0))


def parametros_prosodia(emocion, intensidad):
    """Mezcla la prosodia neutral con la de la emoción según su intensidad."""
    objetivo = PROSODIA_POR_EMOCION.get(emocion)
    if not objetivo:
        return dict(PROSODIA_NEUTRAL)
    k = _curva_s(intensidad)
    return {p: round(PROSODIA_NEUTRAL[p] + (objetivo[p] - PROSODIA_NEUTRAL[p]) * k, 4)
            for p in PROSODIA_NEUTRAL}


class PiperTTS(TextToSpeech):
    """
    Síntesis de voz local con Piper (ONNX). Corre en CPU en tiempo real,
    sin necesitar GPU — coherente con dejar la GPU libre para Ollama.
    """

    def __init__(self, voz_path=VOICE_PATH):
        if not voz_path.exists():
            raise FileNotFoundError(
                f"No encontré la voz de Piper en '{voz_path}'. "
                f"Descárgala con: python -m piper.download_voices "
                f"--download-dir data/voices es_MX-claude-high"
            )
        self.voice = PiperVoice.load(str(voz_path))

    def sintetizar(self, texto: str, emocion: str = "neutral", intensidad: float = 0.0) -> bytes:
        config = SynthesisConfig(**parametros_prosodia(emocion, intensidad))
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            self.voice.synthesize_wav(texto, wav_file, syn_config=config)
        return buffer.getvalue()


class APITTS(TextToSpeech):
    """
    Síntesis de voz vía una API HTTP genérica (p.ej. un servidor Coqui TTS
    u otro motor expuesto por HTTP). Permite cambiar de motor de voz sin
    tocar código: basta con apuntar TTS_API_URL a un endpoint compatible
    que reciba {"text": ...} por POST y responda con el audio en bytes.

    Variables de entorno (.env):
        TTS_API_URL   — endpoint de síntesis (obligatorio).
        TTS_VOICE_ID  — id/nombre de voz a pedir al servidor (opcional).
        TTS_API_KEY   — token Bearer si el endpoint lo requiere (opcional).
        TTS_API_TIMEOUT — timeout en segundos (opcional, default 30).
    """

    def __init__(self, api_url=None, voice_id=None, api_key=None, timeout=None):
        self.api_url = api_url or os.getenv("TTS_API_URL")
        if not self.api_url:
            raise ValueError(
                "Falta TTS_API_URL en el .env — la URL del endpoint de síntesis "
                "para TTS_PROVIDER='api'."
            )
        self.voice_id = voice_id or os.getenv("TTS_VOICE_ID")
        self.api_key = api_key or os.getenv("TTS_API_KEY")
        self.timeout = timeout or float(os.getenv("TTS_API_TIMEOUT", "30"))

    def sintetizar(self, texto: str, emocion: str = "neutral", intensidad: float = 0.0) -> bytes:
        # La emoción no se manda: el contrato del endpoint es solo {"text", "voice_id"}
        # y un servidor estricto podría rechazar campos de más.
        payload = {"text": texto}
        if self.voice_id:
            payload["voice_id"] = self.voice_id

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=self.timeout) as client:
            respuesta = client.post(self.api_url, json=payload, headers=headers)
            respuesta.raise_for_status()
            return respuesta.content


def crear_tts() -> TextToSpeech:
    """
    Fábrica del motor de TTS activo, elegido con TTS_PROVIDER en el .env.

    - "piper" (default): síntesis local con Piper (sin red, corre en CPU).
    - "api": síntesis vía API HTTP genérica (ver APITTS).
    """
    proveedor = os.getenv("TTS_PROVIDER", "piper").strip().lower()
    if proveedor == "piper":
        return PiperTTS()
    if proveedor == "api":
        return APITTS()
    raise ValueError(
        f"TTS_PROVIDER='{proveedor}' no reconocido. Usa 'piper' o 'api'."
    )
