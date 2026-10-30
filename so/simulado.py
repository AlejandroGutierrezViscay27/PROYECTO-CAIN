"""
ControlSO que no toca el sistema: devuelve datos fijos y anota lo que se le
pidió. Para las pruebas y para ensayar sin riesgo (CAIN_SO=simulado).
"""
from core.arnes import reglas, sistema
from core.arnes.rutas import Denegado
from so.base import ControlSO, ErrorNavegador, Navegador, Pestana, Ventana

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


class NavegadorSimulado(Navegador):
    """
    Navegador que no abre nada. Las pruebas ponen en `respuestas` lo que
    devolvería cada guion (un valor o una función del argumento).
    """

    def __init__(self, pestanas=None):
        self.llamadas   = []
        self.respuestas = {}
        self._pestanas  = list(pestanas or [])

    def _abrir(self, url):
        self._pestanas = [Pestana(p.titulo, p.url, False) for p in self._pestanas]
        self._pestanas.append(Pestana(url, url, True))

    def _pestana(self, indice, url_esperada):
        if isinstance(indice, bool) or not isinstance(indice, int) or not 0 <= indice < len(self._pestanas):
            raise Denegado("no hay una pestaña con ese número")
        if self._pestanas[indice].url != url_esperada:
            raise Denegado("las pestañas cambiaron; pídeme la lista otra vez")

    def mostrar(self):
        self.llamadas.append(("mostrar",))

    def pestanas(self):
        return list(self._pestanas)

    def abrir_url(self, url):
        url = sistema.validar_url(url)
        if len(self._pestanas) >= reglas.MAX_PESTANAS:
            raise Denegado("ya hay demasiadas pestañas abiertas en el navegador de CAIN; cierra alguna")
        self.llamadas.append(("abrir_url", url))
        self._abrir(url)

    def activar(self, indice, url_esperada):
        self._pestana(indice, url_esperada)
        self.llamadas.append(("activar", indice))
        self._pestanas = [Pestana(p.titulo, p.url, i == indice) for i, p in enumerate(self._pestanas)]

    def cerrar(self, indice, url_esperada):
        self._pestana(indice, url_esperada)
        self.llamadas.append(("cerrar", indice))
        del self._pestanas[indice]

    def recargar(self, indice, url_esperada):
        self._pestana(indice, url_esperada)
        self.llamadas.append(("recargar", indice))

    def en_sitio(self, dominios, guion, arg=None, ir_a=None, esperar=None):
        if ir_a is not None:
            ir_a = sistema.validar_url(ir_a)
            if not sistema.host_en(ir_a, dominios):
                raise Denegado("esa dirección no es de ese sitio")
            self.llamadas.append(("ir_a", ir_a))
            del_sitio = [i for i, p in enumerate(self._pestanas) if sistema.host_en(p.url, dominios)]
            if del_sitio:
                self._pestanas[del_sitio[-1]] = Pestana(ir_a, ir_a, True)
            else:
                self._abrir(ir_a)
        elif not any(sistema.host_en(p.url, dominios) for p in self._pestanas):
            raise ErrorNavegador("no hay ninguna pestaña de ese sitio abierta en el navegador de CAIN")
        self.llamadas.append(("guion", guion, arg))
        respuesta = self.respuestas.get(guion)
        return respuesta(arg) if callable(respuesta) else respuesta
