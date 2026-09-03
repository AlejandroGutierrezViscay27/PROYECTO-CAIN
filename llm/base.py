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

    @abstractmethod
    def chat_with_tools(self, messages: list, tools: list, temperature: float = 0.3) -> dict:
        """
        Envía una lista de mensajes junto con declaraciones de herramientas
        (JSON schema estilo "function calling") y deja que el modelo decida
        si responde en texto o pide invocar una herramienta.

        Args:
            messages:    Lista de dicts con 'role' y 'content'.
            tools:       Lista de declaraciones de herramientas disponibles.
            temperature: Creatividad de la respuesta (0 = determinista, 1 = creativo).

        Returns:
            Dict con la forma:
            {"content": str | None, "tool_call": {"name": str, "arguments": dict} | None}
            Exactamente uno de los dos campos viene poblado.
        """
        pass