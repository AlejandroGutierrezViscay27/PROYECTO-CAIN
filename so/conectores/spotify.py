"""
Spotify por su API oficial (Fase 10.4). Ver FASE10_PLAN.md §6.5.

Autorización "Authorization Code con PKCE": no hay secreto de cliente, solo
el Client ID de la app de developer.spotify.com (SPOTIFY_CLIENT_ID en el
.env). El token (el refresh token equivale a acceso a la cuenta) se guarda
en data/spotify_token.json: dentro del repo, que ninguna herramienta puede
leer, y nunca se manda al LLM.

Solo se habla con las URLs de reglas.SPOTIFY_URL_*: las que trae la API en
sus respuestas ("next", "href") no se siguen nunca.
"""
import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from urllib.parse import urlencode

import httpx

from core import memory
from core.arnes import reglas
from so.conectores import ErrorConector

ARCHIVO_TOKEN = "data/spotify_token.json"

# Cuánto vale un "state" pendiente (de /spotify/conectar a /spotify/callback).
VIGENCIA_ESTADO = 600
# Se renueva el token un poco antes de que caduque.
MARGEN_CADUCIDAD = 60
TIEMPO_MAX_PETICION = 10
MAX_PAGINAS_LISTAS = 4     # 4 x 50 listas
MAX_PAGINAS_ME_GUSTA = 20  # 20 x 50 canciones


class ErrorSpotify(ErrorConector):
    pass


class SinDispositivo(ErrorSpotify):
    pass


def redireccion_por_defecto():
    """
    La dirección de vuelta que hay que registrar en developer.spotify.com.
    Spotify no acepta "localhost": exige la IP de loopback.
    """
    explicita = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()
    if explicita:
        return explicita
    esquema = "https" if os.getenv("CAIN_SSL_CERT") and os.getenv("CAIN_SSL_KEY") else "http"
    return f"{esquema}://127.0.0.1:{os.getenv('CAIN_PORT', '8000')}/spotify/callback"


def crear_cliente_spotify():
    """El cliente si hay SPOTIFY_CLIENT_ID en el .env; si no, None (sin herramientas de Spotify)."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    if not client_id:
        return None
    return ClienteSpotify(client_id, redireccion_por_defecto())


class ClienteSpotify:

    def __init__(self, client_id, redireccion, transporte=None, reloj=time.time):
        self.client_id   = client_id
        self.redireccion = redireccion
        self._reloj      = reloj
        self._http       = httpx.Client(transport=transporte, timeout=TIEMPO_MAX_PETICION,
                                        follow_redirects=False)
        self._lock       = threading.Lock()
        self._pendientes = {}   # state -> (code_verifier, creado)

    # ─── Autorización ────────────────────────────────────────────────────────

    def conectado(self):
        return bool(memory._cargar_json(ARCHIVO_TOKEN, {}).get("refresh_token"))

    def url_autorizacion(self):
        """URL de Spotify donde el usuario da permiso. Cada una sirve una sola vez."""
        verificador = secrets.token_urlsafe(64)
        reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).rstrip(b"=").decode()
        estado = secrets.token_urlsafe(24)
        with self._lock:
            self._quitar_caducados()
            self._pendientes[estado] = (verificador, self._reloj())
        return reglas.SPOTIFY_URL_AUTORIZAR + "?" + urlencode({
            "client_id":             self.client_id,
            "response_type":         "code",
            "redirect_uri":          self.redireccion,
            "code_challenge_method": "S256",
            "code_challenge":        reto,
            "state":                 estado,
            "scope":                 " ".join(reglas.SPOTIFY_PERMISOS),
        })

    def completar_autorizacion(self, codigo, estado):
        """
        La vuelta desde Spotify. El "state" tiene que ser uno que dio
        url_autorizacion() hace poco, y se gasta al usarlo: sin él, una web
        cualquiera podría colarle a CAIN un código de OTRA cuenta.
        """
        verificador = self._tomar_pendiente(estado)
        if verificador is None:
            raise ErrorSpotify("ese permiso no es válido o caducó; vuelve a empezar desde /spotify/conectar")
        if not isinstance(codigo, str) or not codigo:
            raise ErrorSpotify("Spotify no devolvió el código de autorización")
        datos = self._pedir_token({
            "grant_type":    "authorization_code",
            "code":          codigo,
            "redirect_uri":  self.redireccion,
            "client_id":     self.client_id,
            "code_verifier": verificador,
        })
        if not datos.get("refresh_token"):
            raise ErrorSpotify("Spotify no devolvió un token que se pueda renovar")
        self._guardar_token(datos, {})

    def desconectar(self):
        try:
            os.remove(ARCHIVO_TOKEN)
        except FileNotFoundError:
            pass

    def _tomar_pendiente(self, estado):
        if not isinstance(estado, str) or not estado:
            return None
        recibido = estado.encode("utf-8", "replace")
        with self._lock:
            self._quitar_caducados()
            for clave in list(self._pendientes):
                if hmac.compare_digest(clave.encode(), recibido):
                    return self._pendientes.pop(clave)[0]
        return None

    def _quitar_caducados(self):
        ahora = self._reloj()
        for clave, (_, creado) in list(self._pendientes.items()):
            if ahora - creado > VIGENCIA_ESTADO:
                del self._pendientes[clave]

    # ─── Token ───────────────────────────────────────────────────────────────

    def _pedir_token(self, formulario):
        try:
            r = self._http.post(reglas.SPOTIFY_URL_TOKEN, data=formulario)
        except httpx.HTTPError:
            raise ErrorSpotify("no pude hablar con Spotify")
        if r.status_code != 200:
            if formulario["grant_type"] == "refresh_token" and r.status_code in (400, 401):
                # Permiso revocado desde la cuenta, o token viejo: hay que reconectar.
                self.desconectar()
                raise ErrorSpotify(self._mensaje_sin_conexion())
            raise ErrorSpotify(f"Spotify rechazó la autorización (código {r.status_code})")
        try:
            datos = r.json()
        except ValueError:
            raise ErrorSpotify("Spotify devolvió una respuesta que no entiendo")
        if not isinstance(datos, dict) or not datos.get("access_token"):
            raise ErrorSpotify("Spotify no devolvió un token")
        return datos

    def _guardar_token(self, datos, anterior):
        memory._guardar_json(ARCHIVO_TOKEN, {
            "access_token":  datos["access_token"],
            # Con PKCE el refresh token puede rotar: si no viene uno nuevo, vale el de antes.
            "refresh_token": datos.get("refresh_token") or anterior.get("refresh_token"),
            "caduca":        self._reloj() + int(datos.get("expires_in", 3600)),
            "permisos":      datos.get("scope", anterior.get("permisos", "")),
        })

    def _token_de_acceso(self, renovar=False):
        with self._lock:
            token = memory._cargar_json(ARCHIVO_TOKEN, {})
            if not token.get("refresh_token"):
                raise ErrorSpotify(self._mensaje_sin_conexion())
            if renovar or not token.get("access_token") or token.get("caduca", 0) - MARGEN_CADUCIDAD < self._reloj():
                datos = self._pedir_token({
                    "grant_type":    "refresh_token",
                    "refresh_token": token["refresh_token"],
                    "client_id":     self.client_id,
                })
                self._guardar_token(datos, token)
                return datos["access_token"]
            return token["access_token"]

    def _mensaje_sin_conexion(self):
        conectar = self.redireccion.rsplit("/", 1)[0] + "/conectar"
        return f"Spotify no está conectado. Ábrelo en el navegador de este PC: {conectar}"

    # ─── Peticiones ──────────────────────────────────────────────────────────

    def _api(self, metodo, ruta, params=None, cuerpo=None, renovado=False):
        """
        Una petición a la API. "ruta" es siempre una constante de este
        archivo: los datos (ids, consultas) van en params o en el cuerpo,
        que httpx codifica; nunca dentro de la ruta.
        """
        try:
            r = self._http.request(
                metodo, reglas.SPOTIFY_URL_API + ruta, params=params, json=cuerpo,
                headers={"Authorization": f"Bearer {self._token_de_acceso()}"},
            )
        except httpx.HTTPError:
            raise ErrorSpotify("no pude hablar con Spotify")

        if r.status_code == 401 and not renovado:
            self._token_de_acceso(renovar=True)
            return self._api(metodo, ruta, params, cuerpo, renovado=True)
        if r.status_code in (200, 201, 202):
            if metodo != "GET":
                # Las órdenes del reproductor responden 200 con un id en texto
                # plano (no JSON). Lo que importa es que se aceptó.
                return None
            try:
                return r.json() if r.content else None
            except ValueError:
                raise ErrorSpotify("Spotify devolvió una respuesta que no entiendo")
        if r.status_code == 204:
            return None
        raise self._error(r)

    @staticmethod
    def _error(r):
        try:
            error = r.json().get("error", {})
            motivo = error.get("reason", "") if isinstance(error, dict) else ""
        except (ValueError, AttributeError):
            motivo = ""
        if motivo == "NO_ACTIVE_DEVICE" or (r.status_code == 404 and "/me/player" in r.url.path):
            return SinDispositivo("no hay ningún dispositivo con Spotify abierto")
        if motivo == "PREMIUM_REQUIRED":
            return ErrorSpotify("eso necesita Spotify Premium")
        if r.status_code == 429:
            return ErrorSpotify("Spotify me pide esperar un momento; prueba en unos segundos")
        if r.status_code == 403:
            return ErrorSpotify("Spotify no me deja hacer eso ahora")
        return ErrorSpotify(f"Spotify respondió con un error ({r.status_code})")

    # ─── Verbos ──────────────────────────────────────────────────────────────

    def estado(self):
        """Lo que suena y dónde, o None si no hay nada."""
        return self._api("GET", "/me/player")

    def dispositivos(self):
        datos = self._api("GET", "/me/player/devices") or {}
        return [d for d in datos.get("devices", []) if isinstance(d, dict) and d.get("id")]

    def reproducir(self, dispositivo=None, contexto=None, pistas=None, desde=None):
        """
        Sin contexto ni pistas, reanuda. "desde": URI de la canción del
        contexto por la que empezar. Los URIs ya vienen validados.
        """
        cuerpo = {}
        if contexto:
            cuerpo["context_uri"] = contexto
            if desde:
                cuerpo["offset"] = {"uri": desde}
        if pistas:
            cuerpo["uris"] = list(pistas)
        params = {"device_id": dispositivo} if dispositivo else None
        self._api("PUT", "/me/player/play", params=params, cuerpo=cuerpo or None)

    def pausar(self):
        self._api("PUT", "/me/player/pause")

    def siguiente(self):
        self._api("POST", "/me/player/next")

    def anterior(self):
        self._api("POST", "/me/player/previous")

    def al_inicio(self):
        """Vuelve al segundo 0 de la canción actual."""
        self._api("PUT", "/me/player/seek", params={"position_ms": 0})

    def aleatorio(self, activo):
        self._api("PUT", "/me/player/shuffle", params={"state": "true" if activo else "false"})

    def buscar(self, consulta, tipo, limite=5):
        """tipo: track, artist, album o playlist. Desde 2026 la API da como mucho 10."""
        datos = self._api("GET", "/search", params={"q": consulta, "type": tipo, "limit": min(limite, 10)}) or {}
        return [x for x in (datos.get(tipo + "s") or {}).get("items", []) if isinstance(x, dict)]

    def mis_listas(self):
        listas = []
        for pagina in range(MAX_PAGINAS_LISTAS):
            datos = self._api("GET", "/me/playlists", params={"limit": 50, "offset": 50 * pagina}) or {}
            items = [x for x in datos.get("items", []) if isinstance(x, dict)]
            listas.extend(items)
            if len(items) < 50:
                break
        return listas

    def me_gusta(self):
        """Tus canciones con Me gusta, de la más reciente a la más vieja (hasta 50 x MAX_PAGINAS_ME_GUSTA)."""
        canciones = []
        for pagina in range(MAX_PAGINAS_ME_GUSTA):
            datos = self._api("GET", "/me/tracks", params={"limit": 50, "offset": 50 * pagina}) or {}
            items = [x for x in datos.get("items", []) if isinstance(x, dict)]
            canciones.extend(x["track"] for x in items if isinstance(x.get("track"), dict))
            if len(items) < 50:
                break
        return canciones

    def mas_escuchados(self, tipo, limite=10):
        """tipo: "artists" o "tracks" (lo que más escuchas en los últimos meses)."""
        if tipo not in ("artists", "tracks"):
            raise ValueError(tipo)
        ruta = "/me/top/artists" if tipo == "artists" else "/me/top/tracks"
        datos = self._api("GET", ruta, params={"limit": limite, "time_range": "medium_term"}) or {}
        return [x for x in datos.get("items", []) if isinstance(x, dict)]


# ─── Para mostrar ────────────────────────────────────────────────────────────

def nombre_de(objeto):
    return str(objeto.get("name") or "sin nombre")[:120]


def artistas_de(objeto):
    return ", ".join(nombre_de(a) for a in objeto.get("artists", [])[:3] if isinstance(a, dict))


def describir(objeto, tipo):
    """'Canción — Artista', 'Álbum — Artista', 'Artista' o 'Lista (de Fulano)'."""
    if tipo in ("track", "album") and artistas_de(objeto):
        return f"{nombre_de(objeto)} — {artistas_de(objeto)}"
    if tipo == "playlist":
        dueno = (objeto.get("owner") or {}).get("display_name")
        return f"{nombre_de(objeto)} (de {str(dueno)[:60]})" if dueno else nombre_de(objeto)
    return nombre_de(objeto)


def total_canciones(lista):
    """Desde 2026 la API llama "items" a lo que antes era "tracks"."""
    for campo in ("items", "tracks"):
        valor = lista.get(campo)
        if isinstance(valor, dict) and isinstance(valor.get("total"), int):
            return valor["total"]
    return None
