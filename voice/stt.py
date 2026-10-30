import io
import os
import wave

# ctranslate2 trae el runtime de Intel (libiomp5md), que en Windows instala su
# propio manejador de Ctrl+C/Ctrl+Break: imprime "forrtl: error (200)", se
# traga la señal e intenta abortar el proceso, que se queda colgado. Tiene que
# estar antes de importar faster_whisper (el runtime la lee al cargarse).
os.environ.setdefault("FOR_DISABLE_CONSOLE_CTRL_HANDLER", "1")

import numpy as np
from faster_whisper import WhisperModel
from voice.base import SpeechToText

MODEL_SIZE    = "small"
DEVICE        = "cpu"
COMPUTE_TYPE  = "int8"
FRECUENCIA    = 16000   # la que espera Whisper


def wav_a_muestras(audio_bytes: bytes):
    """
    Si el audio es WAV PCM 16-bit mono a 16 kHz (lo que manda el navegador),
    lo convierte directo a float32 en [-1, 1] sin pasar por el decodificador.
    Retorna None para cualquier otro formato.
    """
    if audio_bytes[:4] != b"RIFF":
        return None
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (FRECUENCIA, 1, 2):
                return None
            pcm = wav.readframes(wav.getnframes())
    except wave.Error:
        return None
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0


class FasterWhisperSTT(SpeechToText):
    """
    Reconocimiento de voz local con faster-whisper (CTranslate2).
    Corre en CPU a propósito: deja la GPU libre para Ollama (Fase 13).
    """

    def __init__(self, model_size=MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribir(self, audio_bytes: bytes) -> str:
        muestras = wav_a_muestras(audio_bytes)
        entrada  = muestras if muestras is not None else io.BytesIO(audio_bytes)
        segmentos, _ = self.model.transcribe(entrada, language="es", vad_filter=True)
        return " ".join(seg.text.strip() for seg in segmentos).strip()
