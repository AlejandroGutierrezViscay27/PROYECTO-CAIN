from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Ventana:
    titulo:  str
    proceso: str    # nombre del ejecutable, p. ej. "msedge.exe" ("" si no se pudo saber)
    activa:  bool


class ControlSO(ABC):
    """
    Interfaz común para observar y actuar sobre el sistema operativo.
    Cualquier implementación que CAIN use debe cumplir este contrato, y no
    puede hacer más de lo que la interfaz declara.

    Fase 10.1: lectura (N0). Fase 10.2: abrir apps de la lista blanca y URLs,
    multimedia y volumen (N1). Cada método que actúa vuelve a comprobar sus
    argumentos con core.arnes.sistema, aunque el agente ya lo haya hecho.
    """

    @abstractmethod
    def ventanas(self) -> list[Ventana]:
        """
        Ventanas de aplicación abiertas (las que se verían con Alt+Tab),
        con la activa marcada. Sin ventanas ocultas, de herramientas ni sin título.
        """
        pass

    @abstractmethod
    def info_sistema(self) -> dict:
        """
        Estado del equipo. Claves (las que no se puedan saber, en None):
            sistema:        str  — "Windows 11 (10.0.26200)"
            encendido_seg:  int  — tiempo desde el arranque
            bateria_pct:    int | None — None si no hay batería
            cargando:       bool | None
            ram_total:      int  — bytes
            ram_libre:      int  — bytes
            disco_total:    int  — bytes, unidad del sistema
            disco_libre:    int  — bytes, unidad del sistema
        """
        pass

    # ─── Fase 10.2: acciones N1 ──────────────────────────────────────────────

    @abstractmethod
    def abrir_app(self, ruta, argumentos):
        """
        Abre el ejecutable `ruta` (una de reglas.apps_permitidas(), exacta) con
        sus argumentos fijos (reglas.argumentos_app). Lanza Denegado si no.
        """
        pass

    @abstractmethod
    def abrir_url(self, url):
        """Abre una URL http(s) en el navegador de CAIN (su perfil propio)."""
        pass

    @abstractmethod
    def multimedia(self, accion):
        """Tecla multimedia: "reproducir_pausar", "siguiente" o "anterior"."""
        pass

    @abstractmethod
    def volumen(self):
        """Volumen general: (porcentaje 0-100, silenciado)."""
        pass

    @abstractmethod
    def fijar_volumen(self, porcentaje):
        """Pone el volumen general en `porcentaje` (0-100) y quita el silencio."""
        pass

    @abstractmethod
    def silenciar(self, silenciado):
        """Silencia (True) o quita el silencio (False)."""
        pass
