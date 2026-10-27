"""
ControlSO que no toca el sistema: devuelve datos fijos y anota lo que se le
pidió. Para las pruebas y para ensayar sin riesgo (CAIN_SO=simulado).
"""
from core.arnes import sistema
from core.arnes.rutas import Denegado
from so.base import ControlSO, Ventana

GB = 1024 ** 3


class SimuladoSO(ControlSO):

    def __init__(self, ventanas=None, info=None):
        self.llamadas = []
        self._volumen = 50
        self._silenciado = False
        self._ventanas = ventanas if ventanas is not None else [
            Ventana("YouTube - Microsoft Edge", "msedge.exe", True),
            Ventana("Spotify Premium", "Spotify.exe", False),
            Ventana("finanzas.xlsx - Excel", "EXCEL.EXE", False),
        ]
        self._info = info if info is not None else {
            "sistema":       "Windows 11 (simulado)",
            "encendido_seg": 3 * 3600 + 25 * 60,
            "bateria_pct":   None,
            "cargando":      None,
            "ram_total":     32 * GB,
            "ram_libre":     20 * GB,
            "disco_total":   1000 * GB,
            "disco_libre":   400 * GB,
        }

    def ventanas(self):
        self.llamadas.append("ventanas")
        return list(self._ventanas)

    def info_sistema(self):
        self.llamadas.append("info_sistema")
        return dict(self._info)

    # Las acciones comprueban lo mismo que WindowsSO, para que las pruebas
    # cubran también la segunda barrera.

    def abrir_app(self, ruta, argumentos):
        if not sistema.es_ejecutable_permitido(ruta):
            raise Denegado("ese programa no está en la lista de apps permitidas")
        self.llamadas.append(("abrir_app", ruta, list(argumentos)))

    def abrir_url(self, url):
        self.llamadas.append(("abrir_url", sistema.validar_url(url)))

    def multimedia(self, accion):
        self.llamadas.append(("multimedia", sistema.validar_multimedia(accion)))

    def volumen(self):
        return self._volumen, self._silenciado

    def fijar_volumen(self, porcentaje):
        _, porcentaje = sistema.validar_volumen("fijar", porcentaje)
        self.llamadas.append(("fijar_volumen", porcentaje))
        self._volumen, self._silenciado = porcentaje, False

    def silenciar(self, silenciado):
        self.llamadas.append(("silenciar", bool(silenciado)))
        self._silenciado = bool(silenciado)
