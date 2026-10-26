import json
import os
from openai import OpenAI
from llm.base import LLMProvider

MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    """
    Implementación de LLMProvider usando la API de OpenAI.
    Es la única clase en todo el proyecto que conoce a OpenAI.

    Sirve también para cualquier servidor compatible con la API de OpenAI
    (Ollama, LM Studio...) pasándole base_url; ver OllamaProvider.

    al_usar: función opcional (modelo, tokens_entrada, tokens_salida) que se
    llama tras cada respuesta, para el registro de gasto (llm/registro.py).
    """

    proveedor = "openai"

    def __init__(self, model: str = MODEL, base_url: str = None, api_key: str = None,
                 al_usar=None, client=None):
        self.client  = client or OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"), base_url=base_url)
        self.model   = model
        self.al_usar = al_usar

    def _anotar(self, respuesta):
        uso = getattr(respuesta, "usage", None)
        if self.al_usar and uso is not None:
            self.al_usar(self.model, uso.prompt_tokens or 0, uso.completion_tokens or 0)

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """Llama a OpenAI y retorna la respuesta como string."""
        respuesta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        self._anotar(respuesta)
        return respuesta.choices[0].message.content

    def chat_with_tools(self, messages: list, tools: list, temperature: float = 0.3) -> dict:
        """Llama a OpenAI con function calling y retorna texto o una llamada a herramienta."""
        respuesta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature
        )
        self._anotar(respuesta)
        mensaje = respuesta.choices[0].message

        if mensaje.tool_calls:
            llamada = mensaje.tool_calls[0]
            try:
                argumentos = json.loads(llamada.function.arguments)
            except json.JSONDecodeError:
                argumentos = {}
            return {"content": None, "tool_call": {"name": llamada.function.name, "arguments": argumentos}}

        return {"content": mensaje.content, "tool_call": None}
