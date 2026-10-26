"""
Un LLM por rol: cada tarea de CAIN puede ir con su propio proveedor y modelo
(inspirado en OpenSakura, que separa actor y director).

Se elige en el .env. Un rol sin variables propias usa las generales, así
que sin configurar nada todo va con openai:gpt-4o-mini como antes:

    LLM_PROVIDER=openai              # general: "openai" | "ollama"
    LLM_MODEL=gpt-4o-mini
    LLM_PROVIDER_DIRECTOR=ollama     # por rol: LLM_PROVIDER_<ROL> / LLM_MODEL_<ROL>
    LLM_MODEL_DIRECTOR=qwen2.5:7b
    LLM_MODEL_CODIGO=gpt-4.1
"""
import os

from llm.ollama_provider import OllamaProvider
from llm.openai_provider import OpenAIProvider
from llm.registro import RegistroUso

ROLES = {
    "conversacion": "la respuesta que ve el usuario (personalidad, ánimo)",
    "enrutador":    "decide si el mensaje pide una herramienta (necesita function calling)",
    "intencion":    "clasificaciones cortas: intención, intereses, coherencia de ediciones",
    "director":     "director de memoria, en segundo plano cada 10 mensajes",
    "codigo":       "genera proyectos y archivos, edita archivos y corrige código",
}

PROVEEDORES = {"openai": OpenAIProvider, "ollama": OllamaProvider}
MODELO_POR_DEFECTO = {"openai": "gpt-4o-mini", "ollama": "llama3.1"}


def _env(nombre):
    valor = os.getenv(nombre, "").strip()
    return valor or None


def config_rol(rol):
    """(proveedor, modelo) para un rol, según el .env."""
    general = (_env("LLM_PROVIDER") or "openai").lower()
    proveedor = (_env(f"LLM_PROVIDER_{rol.upper()}") or general).lower()
    if proveedor not in PROVEEDORES:
        raise ValueError(
            f"Proveedor de LLM '{proveedor}' no reconocido (rol {rol}). "
            f"Usa uno de: {', '.join(PROVEEDORES)}."
        )
    modelo = _env(f"LLM_MODEL_{rol.upper()}")
    if modelo is None:
        # LLM_MODEL es del proveedor general: no sirve si el rol cambió de
        # proveedor (gpt-4o-mini no existe en Ollama).
        modelo = (_env("LLM_MODEL") if proveedor == general else None) or MODELO_POR_DEFECTO[proveedor]
    return proveedor, modelo


def crear_llms(registro=None):
    """
    Crea un LLMProvider por rol. Todos anotan su gasto en el registro.

    Returns:
        {rol: LLMProvider}
    """
    registro = registro or RegistroUso()
    clientes = {}   # un cliente HTTP por proveedor, compartido entre roles
    llms = {}
    for rol in ROLES:
        proveedor, modelo = config_rol(rol)

        def al_usar(m, entrada, salida, rol=rol, proveedor=proveedor):
            registro.anotar(rol, proveedor, m, entrada, salida)

        llm = PROVEEDORES[proveedor](model=modelo, al_usar=al_usar, client=clientes.get(proveedor))
        clientes.setdefault(proveedor, llm.client)
        llms[rol] = llm
    print("[LLM] " + ", ".join(f"{rol}={config_rol(rol)[0]}:{llms[rol].model}" for rol in llms))
    return llms
