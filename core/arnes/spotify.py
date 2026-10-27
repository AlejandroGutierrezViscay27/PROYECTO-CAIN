"""
Límites de lo que CAIN hace con Spotify (Fase 10.4).

El LLM solo da opciones cerradas (tipo, acción) y texto para buscar. Nunca
un URI ni un id: lo que suena sale siempre de una respuesta de la API, y
además se comprueba aquí que tenga la forma de un URI de Spotify.
"""
import re
import unicodedata

from core.arnes.rutas import Denegado

# Lo que el LLM puede pedir buscar → tipo de la API.
TIPOS_BUSQUEDA = {"cancion": "track", "artista": "artist", "album": "album", "lista": "playlist"}
# Para reproducir, además, una lista tuya por su nombre y tus Me gusta.
TIPOS_REPRODUCIR = (*TIPOS_BUSQUEDA, "mi_lista", "me_gusta")

# Cuántas canciones de tus Me gusta se mandan a sonar de una vez.
MAX_PISTAS = 100

ACCIONES_CONTROL = ("pausar", "reanudar", "siguiente", "anterior", "aleatorio_si", "aleatorio_no")

LARGO_MAX_CONSULTA = 100
MAX_SUGERENCIAS    = 5

_URI = re.compile(r"^spotify:(track|album|artist|playlist):[A-Za-z0-9]{22}$")
_CONTROLES = re.compile(r"[\x00-\x1f\x7f]")


def validar_tipo(tipo, permitidos):
    if tipo not in permitidos:
        raise Denegado("no sé buscar eso en Spotify")
    return tipo


def validar_control(accion):
    if accion not in ACCIONES_CONTROL:
        raise Denegado("esa acción de Spotify no existe")
    return accion


def validar_consulta(texto):
    """Texto para buscar: sin controles, espacios colapsados y con largo máximo."""
    if not isinstance(texto, str):
        raise Denegado("falta qué buscar")
    texto = " ".join(_CONTROLES.sub(" ", texto).split())
    if not texto:
        raise Denegado("falta qué buscar")
    return texto[:LARGO_MAX_CONSULTA]


def validar_uri(uri, tipos):
    """Un URI de Spotify bien formado y de uno de los tipos de la API dados."""
    coincide = _URI.match(uri) if isinstance(uri, str) else None
    if not coincide or coincide.group(1) not in tipos:
        raise Denegado("Spotify devolvió algo que no reconozco")
    return uri


def normalizar_nombre(texto):
    """Para comparar nombres de listas: sin mayúsculas, tildes ni signos."""
    texto = unicodedata.normalize("NFKD", str(texto)).casefold()
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w]+", " ", texto).split())
