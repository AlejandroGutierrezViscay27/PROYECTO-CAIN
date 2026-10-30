"""
El navegador de CAIN (Fase 10.3): Brave (o Edge) con su perfil propio,
controlado con Playwright. Ver FASE10_PLAN.md §6.2.

Playwright corre en un hilo propio, con su event loop: los turnos de CAIN
llegan desde hilos distintos (el pool de web/app.py) y los objetos de
Playwright solo se usan desde el loop que los creó. Además, así el loop
atiende los eventos del navegador (peticiones que filtrar, pestañas que se
cierran) aunque nadie le esté pidiendo nada.

Playwright habla con el navegador por una tubería (--remote-debugging-pipe),
no por un puerto: ningún otro programa del PC puede conectarse a él.
"""
import asyncio
import os
import re
import threading
from urllib.parse import urlsplit

from playwright.async_api import Error as ErrorPlaywright
from playwright.async_api import TimeoutError as TiempoPlaywright
from playwright.async_api import async_playwright

from core.arnes import reglas, sistema
from core.arnes.rutas import Denegado
from so.base import ErrorNavegador, Navegador, Pestana
from so.windows import preparar_perfil_navegador

# Las peticiones de las páginas que pasan por Python: solo las que podrían ir
# a la red local (el resto no se toca y no se frena). Es un filtro amplio, que
# Playwright aplica sin salir del navegador; quien decide es
# sistema.es_destino_local().
POSIBLE_RED_LOCAL = re.compile(
    r"^[a-z][a-z0-9+.-]*://(?:[^/?#@]*@)?"
    r"(?:localhost|\[|[0-9]"                                           # IPs (y dominios que empiezan con cifra)
    r"|[^/?#:.]+\.?(?:[:/?#]|$)"                                       # nombres de una sola etiqueta
    r"|[^/?#:]*\.(?:localhost|local|lan|home|internal|intranet|corp|arpa)\.?(?:[:/?#]|$))",
    re.IGNORECASE)

_ESQUEMAS_PESTANA_VACIA = ("about", "chrome", "brave", "edge")

# El guion de un conector corre dentro de esta función, que antes comprueba
# en la propia página que sigue en uno de sus dominios.
_ENVOLTORIO = """async ([dominios, arg]) => {
  const host = location.hostname;
  if (!dominios.some(d => host === d || host.endsWith('.' + d))) throw new Error('fuera del sitio');
  return await (GUION)(arg);
}"""


async def _filtrar_peticion(ruta):
    if sistema.es_destino_local(ruta.request.url):
        await ruta.abort("blockedbyclient")
    else:
        await ruta.continue_()


def _anotar_pestana_nueva(pagina):
    """Depuración: quién abre cada pestaña (las about:blank que se quedan en blanco)."""
    async def anotar():
        try:
            abridor = await pagina.opener()
        except ErrorPlaywright:
            abridor = None
        origen = urlsplit(abridor.url).netloc if abridor else "CAIN o el usuario"
        print(f"[DEBUG] navegador: pestana nueva ({pagina.url[:60]}) abierta por {origen}"
              .encode("ascii", "replace").decode())
    asyncio.ensure_future(anotar())


def _vacia(pagina):
    url = pagina.url
    return url == "about:blank" or (urlsplit(url).scheme in _ESQUEMAS_PESTANA_VACIA and "newtab" in url.replace("-", ""))


class NavegadorCAIN(Navegador):

    def __init__(self, ejecutable):
        self._ejecutable = ejecutable
        self._lock       = threading.Lock()
        self._loop       = None
        self._playwright = None
        self._contexto   = None

    # ─── Puente entre los turnos y el hilo del navegador ─────────────────────

    def _correr(self, corrutina):
        with self._lock:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                threading.Thread(target=self._loop.run_forever, name="navegador-cain", daemon=True).start()
        futuro = asyncio.run_coroutine_threadsafe(corrutina, self._loop)
        try:
            return futuro.result(timeout=reglas.NAVEGADOR_TIEMPO_MAX)
        except TimeoutError:
            futuro.cancel()
            raise ErrorNavegador("el navegador de CAIN tardó demasiado en responder")
        except ErrorPlaywright as e:
            print(f"[DEBUG] navegador: {type(e).__name__}: {str(e)[:200].encode('ascii', 'replace').decode()}")
            raise ErrorNavegador("el navegador de CAIN no respondió como esperaba")

    async def _abrir_contexto(self):
        if self._contexto is not None:
            return self._contexto
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        preparar_perfil_navegador()
        try:
            contexto = await self._playwright.chromium.launch_persistent_context(
                reglas.CARPETA_NAVEGADOR,
                executable_path=self._ejecutable,
                headless=False,
                args=list(reglas.ARGUMENTOS_NAVEGADOR),
                ignore_default_args=list(reglas.ARGUMENTOS_PLAYWRIGHT_QUITADOS),
                chromium_sandbox=True,     # si no, Playwright lo lanza con --no-sandbox
                no_viewport=True,
                accept_downloads=False,
                service_workers="block",   # si no, sus peticiones no pasarían por el filtro
                env=sistema.entorno_apps(),
            )
        except ErrorPlaywright as e:
            print(f"[DEBUG] navegador no arranco: {str(e)[:200].encode('ascii', 'replace').decode()}")
            raise ErrorNavegador("no pude abrir el navegador de CAIN; si tiene una ventana abierta "
                                 "que no abrí yo, ciérrala y vuelve a pedírmelo")
        await contexto.route(POSIBLE_RED_LOCAL, _filtrar_peticion)
        contexto.on("close", lambda _: self._olvidar(contexto))
        contexto.on("page", _anotar_pestana_nueva)
        self._contexto = contexto
        return contexto

    def _olvidar(self, contexto):
        """El usuario cerró la ventana: la próxima vez se vuelve a abrir."""
        if self._contexto is contexto:
            self._contexto = None

    async def _paginas(self, abrir):
        if self._contexto is None and not abrir:
            return []
        contexto = await self._abrir_contexto()
        return [p for p in contexto.pages if not p.is_closed()]

    async def _nueva(self, paginas):
        vacia = next((p for p in paginas if _vacia(p)), None)
        if vacia:
            return vacia
        if len(paginas) >= reglas.MAX_PESTANAS:
            raise Denegado(f"ya hay {len(paginas)} pestañas abiertas en el navegador de CAIN; cierra alguna")
        return await self._contexto.new_page()

    @staticmethod
    async def _visible(pagina):
        try:
            return await asyncio.wait_for(pagina.evaluate("document.visibilityState === 'visible'"), 2)
        except (ErrorPlaywright, asyncio.TimeoutError):
            return False

    async def _del_sitio(self, paginas, dominios):
        """La pestaña del sitio: la visible, si hay una; si no, la última."""
        del_sitio = [p for p in paginas if sistema.host_en(p.url, dominios)]
        for pagina in del_sitio:
            if await self._visible(pagina):
                return pagina
        return del_sitio[-1] if del_sitio else None

    @staticmethod
    def _pestana(paginas, indice, url_esperada):
        if isinstance(indice, bool) or not isinstance(indice, int) or not 0 <= indice < len(paginas):
            raise Denegado("no hay una pestaña con ese número")
        if paginas[indice].url != url_esperada:
            raise Denegado("las pestañas cambiaron; pídeme la lista otra vez")
        return paginas[indice]

    # ─── Navegador ───────────────────────────────────────────────────────────

    def mostrar(self):
        async def mostrar():
            paginas = await self._paginas(abrir=True)
            pagina = paginas[0] if paginas else await self._contexto.new_page()
            await pagina.bring_to_front()
        self._correr(mostrar())

    def pestanas(self):
        async def pestanas():
            resultado = []
            for pagina in await self._paginas(abrir=False):
                try:
                    titulo = await asyncio.wait_for(pagina.title(), 2)
                except (ErrorPlaywright, asyncio.TimeoutError):
                    titulo = ""
                resultado.append(Pestana(titulo, pagina.url, await self._visible(pagina)))
            return resultado
        return self._correr(pestanas())

    def abrir_url(self, url):
        url = sistema.validar_url(url)

        async def abrir():
            pagina = await self._nueva(await self._paginas(abrir=True))
            await pagina.bring_to_front()
            await pagina.goto(url, wait_until="commit")
        self._correr(abrir())

    def activar(self, indice, url_esperada):
        async def activar():
            await self._pestana(await self._paginas(abrir=False), indice, url_esperada).bring_to_front()
        self._correr(activar())

    def cerrar(self, indice, url_esperada):
        async def cerrar():
            await self._pestana(await self._paginas(abrir=False), indice, url_esperada).close()
        self._correr(cerrar())

    def apagar(self):
        if self._loop is None or self._contexto is None:
            return
        futuro = asyncio.run_coroutine_threadsafe(self._contexto.close(), self._loop)
        try:
            futuro.result(timeout=reglas.NAVEGADOR_TIEMPO_APAGAR)
        except Exception as e:   # al salir, nada debe impedir que CAIN se apague
            print(f"[DEBUG] navegador no se cerro limpio: {type(e).__name__}")

    def recargar(self, indice, url_esperada):
        async def recargar():
            pagina = self._pestana(await self._paginas(abrir=False), indice, url_esperada)
            await pagina.bring_to_front()
            await pagina.reload(wait_until="commit")
        self._correr(recargar())

    def en_sitio(self, dominios, guion, arg=None, ir_a=None, esperar=None):
        dominios = list(dominios)
        if ir_a is not None:
            ir_a = sistema.validar_url(ir_a)
            if not sistema.host_en(ir_a, dominios):
                raise Denegado("esa dirección no es de ese sitio")

        async def en_sitio():
            if ir_a is not None:
                paginas = await self._paginas(abrir=True)
                pagina = await self._del_sitio(paginas, dominios) or await self._nueva(paginas)
                await pagina.bring_to_front()
                await pagina.goto(ir_a, wait_until="domcontentloaded")
            else:
                pagina = await self._del_sitio(await self._paginas(abrir=False), dominios)
                if pagina is None:
                    raise ErrorNavegador("no hay ninguna pestaña de ese sitio abierta en el navegador de CAIN")
            if esperar:
                try:
                    await pagina.wait_for_selector(esperar, timeout=reglas.NAVEGADOR_ESPERA_PAGINA * 1000)
                except TiempoPlaywright:
                    pass   # el guion verá que no está y lo dirá
            if not sistema.host_en(pagina.url, dominios):
                raise Denegado("la pestaña ya no está en ese sitio")
            return await pagina.evaluate(_ENVOLTORIO.replace("GUION", guion), [dominios, arg])
        return self._correr(en_sitio())
