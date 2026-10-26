import os

from llm.openai_provider import OpenAIProvider

OLLAMA_URL = "http://localhost:11434/v1"


class OllamaProvider(OpenAIProvider):
    """
    LLMProvider para modelos locales con Ollama (https://ollama.com).

    Ollama expone una API compatible con la de OpenAI en /v1, así que basta
    con apuntar el cliente de OpenAI ahí. La URL se cambia con OLLAMA_URL.
    Para usar herramientas (rol "enrutador") el modelo debe soportar
    function calling (p.ej. llama3.1, qwen2.5).

        ollama pull qwen2.5:7b
        LLM_PROVIDER_DIRECTOR=ollama
        LLM_MODEL_DIRECTOR=qwen2.5:7b
    """

    proveedor = "ollama"

    def __init__(self, model: str = "llama3.1", base_url: str = None, al_usar=None, client=None):
        super().__init__(
            model=model,
            base_url=base_url or os.getenv("OLLAMA_URL", OLLAMA_URL),
            api_key="ollama",   # Ollama no la valida, pero el cliente exige una
            al_usar=al_usar,
            client=client,
        )
