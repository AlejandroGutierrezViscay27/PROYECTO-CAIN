from abc import ABC, abstractmethod


class SpeechToText(ABC):
    """
    Interfaz común para cualquier motor de reconocimiento de voz.
    Cualquier motor que CAIN use para escuchar debe implementar este contrato.
    """

    @abstractmethod
    def transcribir(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio a texto.

        Args:
            audio_bytes: Audio crudo (cualquier contenedor que ffmpeg pueda
                         decodificar — webm/opus, wav, ogg, etc.).

        Returns:
            Texto transcrito. Cadena vacía si no se detectó habla.
        """
        pass


class TextToSpeech(ABC):
    """
    Interfaz común para cualquier motor de síntesis de voz.
    Cualquier motor que CAIN use para hablar debe implementar este contrato.
    """

    @abstractmethod
    def sintetizar(self, texto: str, emocion: str = "neutral", intensidad: float = 0.0) -> bytes:
        """
        Sintetiza texto a audio.

        Args:
            texto:      Texto a convertir en habla.
            emocion:    Emoción dominante de CAIN (ver core/emocion.py). Cada motor
                        la usa como pueda; uno que no la soporte la ignora.
            intensidad: Intensidad de esa emoción, de 0 a 1.

        Returns:
            Audio en formato WAV (bytes).
        """
        pass
