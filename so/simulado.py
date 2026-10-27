"""
ControlSO que no toca el sistema: devuelve datos fijos y anota lo que se le
pidió. Para las pruebas y para ensayar sin riesgo (CAIN_SO=simulado).
"""
from so.base import ControlSO, Ventana

GB = 1024 ** 3


class SimuladoSO(ControlSO):

    def __init__(self, ventanas=None, info=None):
        self.llamadas = []
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
