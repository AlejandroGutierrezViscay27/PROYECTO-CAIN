from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Interfaz común para cualquier proveedor de LLM.
    Cualquier modelo que CAIN use debe implementar este contrato.
    """

    @abstractmethod
    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """
        Envía una lista de mensajes al modelo y retorna la respuesta como string.

        Args:
            messages:    Lista de dicts con 'role' y 'content'.
            temperature: Creatividad de la respuesta (0 = determinista, 1 = creativo).

        Returns:
            Texto de la respuesta del modelo.
        """
        pass