from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Ventana:
    titulo:  str
    proceso: str    # nombre del ejecutable, p. ej. "msedge.exe" ("" si no se pudo saber)
    activa:  bool


class ControlSO(ABC):
    """
    Interfaz común para observar y (en etapas posteriores) actuar sobre el
    sistema operativo. Cualquier implementación que CAIN use debe cumplir
    este contrato.

    Fase 10.1: solo métodos de lectura (N0). No hay ninguno que cambie nada:
    una implementación no puede hacer más de lo que la interfaz declara.
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
