import json
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

    def chat_with_tools(self, messages: list, tools: list, temperature: float = 0.3) -> dict:
        """Llama a OpenAI con function calling y retorna texto o una llamada a herramienta."""
        respuesta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature
        )
        mensaje = respuesta.choices[0].message

        if mensaje.tool_calls:
            llamada = mensaje.tool_calls[0]
            try:
                argumentos = json.loads(llamada.function.arguments)
            except json.JSONDecodeError:
                argumentos = {}
            return {"content": None, "tool_call": {"name": llamada.function.name, "arguments": argumentos}}

        return {"content": mensaje.content, "tool_call": None}