from llm.base import LLMProvider

# TODO: Fase futura — migración a modelo local con Ollama
#
# Instalación cuando llegue el momento:
#   pip install ollama
#
# Uso esperado:
#   import ollama
#
# Esta clase ya tiene la estructura correcta.
# Solo hay que implementar el método chat() cuando estés listo.


class OllamaProvider(LLMProvider):
    """
    Implementación de LLMProvider usando Ollama (modelo local).
    Para activarla, cambia una línea en core/agent.py.
    """

    def __init__(self, model: str = "llama3"):
        self.model = model

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        raise NotImplementedError(
            "OllamaProvider aún no está implementado. "
            "Instala Ollama y completa este método cuando estés listo."
        )