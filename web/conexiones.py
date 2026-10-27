"""
Dispositivos conectados a la vez (Fase 9): PC, móvil, tablet...

Todos ven la misma conversación — CAIN es uno solo, con una sola memoria.
Los turnos van de uno en uno (self.turno): el agente no es seguro para dos
chat() simultáneos. La confirmación de un proyecto y el audio de la voz van
solo al dispositivo que hizo la petición; lo demás se difunde a todos.
"""
import asyncio
import itertools
import json


class Dispositivo:

    def __init__(self, websocket, numero, es_local=False):
        self.websocket      = websocket
        self.numero         = numero
        # El propio PC o un dispositivo de la red: el arnés limita lo remoto.
        self.es_local       = es_local
        self.confirmaciones = asyncio.Queue()

    def vaciar_confirmaciones(self):
        """Tira respuestas viejas (p.ej. un clic que llegó tras el timeout)."""
        while not self.confirmaciones.empty():
            self.confirmaciones.get_nowait()


class GestorConexiones:

    def __init__(self):
        self.dispositivos = []
        self.turno        = asyncio.Lock()
        self._contador    = itertools.count(1)

    def conectar(self, websocket, es_local=False):
        dispositivo = Dispositivo(websocket, next(self._contador), es_local)
        self.dispositivos.append(dispositivo)
        print(f"[DEBUG] Dispositivo {dispositivo.numero} conectado ({len(self.dispositivos)} en total)")
        return dispositivo

    def desconectar(self, dispositivo):
        if dispositivo in self.dispositivos:
            self.dispositivos.remove(dispositivo)
        # Si se fue con una confirmación pendiente, el turno no puede quedarse
        # esperando 5 minutos con todos los demás bloqueados: se cancela.
        dispositivo.confirmaciones.put_nowait(False)
        print(f"[DEBUG] Dispositivo {dispositivo.numero} desconectado ({len(self.dispositivos)} en total)")

    async def enviar(self, dispositivo, datos):
        """Envía JSON a un dispositivo. Una conexión caída no tumba el turno."""
        try:
            await dispositivo.websocket.send_text(json.dumps(datos))
        except Exception:
            pass

    async def enviar_bytes(self, dispositivo, datos):
        try:
            await dispositivo.websocket.send_bytes(datos)
        except Exception:
            pass

    async def difundir(self, datos, excepto=None):
        for dispositivo in list(self.dispositivos):
            if dispositivo is not excepto:
                await self.enviar(dispositivo, datos)
