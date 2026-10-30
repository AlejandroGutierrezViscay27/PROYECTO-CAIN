"""
Arnés de seguridad de CAIN (Fase 10).

El LLM solo PROPONE una herramienta. Lo que se ejecuta lo decide este
paquete, con reglas fijas en el código (reglas.py), no el prompt.

Flujo (ver Cain._usar_herramienta):
1. evaluar(): ¿la herramienta tiene nivel declarado? ¿lo permite el origen
   (PC o dispositivo remoto) y el proceso (no administrador)?
2. El handler resuelve rutas con rutas.resolver() — lanza Denegado si no.
   Si el nivel exige confirmación, el handler NO actúa: devuelve una Accion
   con lo que se va a hacer, exactamente.
3. Se confirma en el dispositivo que lo pidió, se ejecuta y se audita.
"""
import os

from core.arnes import reglas
from core.arnes.rutas import Denegado

__all__ = ["Accion", "Denegado", "Veredicto", "evaluar", "nivel_de", "proceso_elevado"]


class Veredicto:

    def __init__(self, permitido, nivel, motivo=""):
        self.permitido = permitido
        self.nivel     = nivel
        self.motivo    = motivo

    @property
    def confirmar(self):
        return self.nivel is not None and self.nivel >= reglas.NIVEL_CONFIRMACION

    @property
    def nombre_nivel(self):
        return reglas.NOMBRE_NIVEL.get(self.nivel, "?")


class Accion:
    """
    Lo que un handler propone hacer, sin haberlo hecho todavía.

    ejecutar:     callable sin argumentos que hace la acción y devuelve el texto
                  de respuesta. Solo se llama si el usuario confirmó.
    confirmacion: dict que ve el usuario. "clase": "proyecto" (nombre, archivos,
                  comando) o "accion" (titulo, detalle). Ambos con "advertencias".
    al_cancelar:  texto de respuesta si el usuario dice que no.
    """

    def __init__(self, ejecutar, confirmacion, al_cancelar="🎭 Entendido, cancelado."):
        self.ejecutar     = ejecutar
        self.confirmacion = confirmacion
        self.al_cancelar  = al_cancelar


_elevado = None


def proceso_elevado():
    """True si CAIN corre como administrador. Se calcula una vez."""
    global _elevado
    if _elevado is None:
        try:
            if os.name == "nt":
                import ctypes
                _elevado = bool(ctypes.windll.shell32.IsUserAnAdmin())
            else:
                _elevado = os.geteuid() == 0
        except Exception:
            _elevado = True   # si no se puede saber, se asume lo peor
    return _elevado


def nivel_de(herramienta, argumentos):
    """Nivel de una llamada concreta, o None si la herramienta no está declarada."""
    nivel = reglas.NIVEL_HERRAMIENTA.get(herramienta)
    if herramienta == "memoria_olvidar" and argumentos.get("objetivo") in ("todo", "historial"):
        nivel = reglas.N3
    if herramienta == "navegador_pestanas" and argumentos.get("accion") == "listar":
        nivel = reglas.N0
    if herramienta == "youtube_canal" and argumentos.get("poner") is not True:
        nivel = reglas.N0
    return nivel


def evaluar(herramienta, argumentos, origen="local"):
    """
    Primera puerta, antes de llamar a ningún handler.
    origen: "local" (el propio PC) o "remoto" (otro dispositivo de la red).
    """
    if not isinstance(argumentos, dict):
        return Veredicto(False, None, "los argumentos de la herramienta no son válidos")

    nivel = nivel_de(herramienta, argumentos)
    if nivel is None:
        return Veredicto(False, None, f"la herramienta '{herramienta}' no está autorizada")

    if origen != "local":
        if herramienta in reglas.SOLO_LOCAL:
            return Veredicto(False, nivel, "eso solo se puede pedir desde el propio PC")
        if nivel > reglas.NIVEL_MAX_REMOTO:
            return Veredicto(False, nivel, "eso no se puede pedir desde otro dispositivo")

    if nivel > reglas.NIVEL_MAX_ELEVADO and proceso_elevado():
        return Veredicto(False, nivel, "estoy corriendo como administrador; reiníciame como usuario normal")

    return Veredicto(True, nivel)
