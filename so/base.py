from abc import ABC, abstractmethod
from dataclasses import dataclass

from so.conectores import ErrorConector


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


# ─── Fase 10.3: el navegador de CAIN ─────────────────────────────────────────

class ErrorNavegador(ErrorConector):
    pass


@dataclass(frozen=True)
class Pestana:
    titulo: str
    url:    str
    activa: bool    # la visible en su ventana


class Navegador(ABC):
    """
    El navegador de CAIN: su propio perfil, nunca el navegador del usuario.

    Abre páginas http(s) cualesquiera (validadas con core.arnes.sistema), pero
    dentro de una página solo actúa con en_sitio(), y solo en los dominios que
    le pasa un conector (p. ej. YouTube). Los índices de pestaña empiezan en 0;
    cada método que actúa sobre una pestaña recibe también su URL tal como se
    vio, y no hace nada si la pestaña ya no es esa.
    """

    @abstractmethod
    def mostrar(self):
        """Abre el navegador si no lo está y lo trae al frente."""
        pass

    @abstractmethod
    def pestanas(self) -> list[Pestana]:
        """Pestañas abiertas. [] si el navegador no está abierto (no lo abre)."""
        pass

    @abstractmethod
    def abrir_url(self, url):
        """Abre una URL http(s) en una pestaña (la vacía, si hay una; si no, una nueva)."""
        pass

    @abstractmethod
    def activar(self, indice, url_esperada):
        """Trae al frente la pestaña `indice`."""
        pass

    @abstractmethod
    def cerrar(self, indice, url_esperada):
        """Cierra la pestaña `indice`."""
        pass

    def apagar(self):
        """Al apagar CAIN: cierra el navegador limpio (si se mata, se cree caído)."""
        pass

    @abstractmethod
    def recargar(self, indice, url_esperada):
        """Recarga la pestaña `indice` (lo que haría el usuario con F5)."""
        pass

    @abstractmethod
    def en_sitio(self, dominios, guion, arg=None, ir_a=None, esperar=None):
        """
        Corre `guion` (JavaScript fijo de un conector, nunca del LLM) en la
        pestaña de ese sitio y devuelve su resultado. Con `ir_a` (una URL del
        sitio), antes navega a ella en la pestaña del sitio o en una nueva;
        sin `ir_a`, si no hay pestaña del sitio, lanza ErrorNavegador.
        `esperar`: selector CSS que se espera (un rato) antes de correr el guion.
        El guion no corre si la pestaña ya no está en uno de los `dominios`.
        """
        pass
