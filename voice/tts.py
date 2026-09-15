import io
import os
import wave
from pathlib import Path

import httpx
from piper import PiperVoice
from voice.base import TextToSpeech

VOICE_PATH = Path("data/voices/es_MX-claude-high.onnx")


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

    def sintetizar(self, texto: str) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            self.voice.synthesize_wav(texto, wav_file)
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

    def sintetizar(self, texto: str) -> bytes:
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
