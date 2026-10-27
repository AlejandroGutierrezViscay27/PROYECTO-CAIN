"""
Conectores de sitio (Fase 10): CAIN habla con un servicio por su API o por
su navegador propio, con verbos estrechos, en vez de con teclado y ratón.
Ver FASE10_PLAN.md §6.
"""


class ErrorConector(Exception):
    """Un fallo del servicio que se le explica al usuario tal cual (en español)."""
