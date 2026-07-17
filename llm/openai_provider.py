import os
from openai import OpenAI
from llm.base import LLMProvider

MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    """
    Implementación de LLMProvider usando la API de OpenAI.
    Es la única clase en todo el proyecto que conoce a OpenAI.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model  = MODEL

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """Llama a OpenAI y retorna la respuesta como string."""
        respuesta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return respuesta.choices[0].message.content