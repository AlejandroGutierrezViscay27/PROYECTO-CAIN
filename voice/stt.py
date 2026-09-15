import io
from faster_whisper import WhisperModel
from voice.base import SpeechToText

MODEL_SIZE    = "small"
DEVICE        = "cpu"
COMPUTE_TYPE  = "int8"


class FasterWhisperSTT(SpeechToText):
    """
    Reconocimiento de voz local con faster-whisper (CTranslate2).
    Corre en CPU a propósito: deja la GPU libre para Ollama (Fase 13).
    """

    def __init__(self, model_size=MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribir(self, audio_bytes: bytes) -> str:
        segmentos, _ = self.model.transcribe(
            io.BytesIO(audio_bytes), language="es", vad_filter=True
        )
        return " ".join(seg.text.strip() for seg in segmentos).strip()
