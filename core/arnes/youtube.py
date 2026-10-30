"""
Límites de lo que CAIN hace en YouTube (Fase 10.3).

El LLM solo da texto para buscar, el número de un resultado que vio el
usuario o una acción cerrada. Nunca la dirección de un vídeo: la que se abre
sale de un enlace de una página de YouTube, y aquí se reconstruye desde el id
(https://www.youtube.com/watch?v=<11 caracteres>), así que nada más de ese
enlace llega al navegador.
"""
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from core.arnes import reglas
from core.arnes.rutas import Denegado
from core.arnes.sistema import host_en

ACCIONES_CONTROL = ("pausar", "reanudar", "siguiente")
# "parecido_de_otros": uno de los que YouTube muestra junto al vídeo abierto;
# "del_mismo_creador": otro del canal del vídeo abierto, del más nuevo al más viejo.
MODOS_REPRODUCIR = ("recomendado", "parecido_de_otros", "del_mismo_creador")

LARGO_MAX_CONSULTA = 100
LARGO_MAX_TITULO   = 100
LARGO_MAX_CANAL    = 60
LARGO_MAX_FECHA    = 30
MAX_RESULTADOS     = 5

# Filtro "Tipo: Canal" de la búsqueda de YouTube.
FILTRO_CANALES = "EgIQAg=="

_ID_VIDEO  = re.compile(r"^[A-Za-z0-9_-]{11}$")
# Un canal, como lo enlaza la página: /@nombre (3-30 caracteres) o /channel/UC...
_CANAL     = re.compile(r"^/(?:@[A-Za-z0-9._-]{3,30}|channel/UC[A-Za-z0-9_-]{22})$")
_CONTROLES = re.compile(r"[\x00-\x1f\x7f]")


def validar_consulta(texto):
    """Texto para buscar: sin controles, espacios colapsados y con largo máximo."""
    if not isinstance(texto, str):
        raise Denegado("falta qué buscar")
    texto = " ".join(_CONTROLES.sub(" ", texto).split())
    if not texto:
        raise Denegado("falta qué buscar")
    return texto[:LARGO_MAX_CONSULTA]


def validar_control(accion):
    if accion not in ACCIONES_CONTROL:
        raise Denegado("esa acción de YouTube no existe")
    return accion


def validar_modo(modo):
    if modo not in MODOS_REPRODUCIR:
        raise Denegado("esa forma de elegir un vídeo de YouTube no existe")
    return modo


def url_busqueda(consulta):
    """La página de resultados de YouTube; la consulta va como parámetro, codificada."""
    return f"{reglas.YOUTUBE_URL}/results?" + urlencode({"search_query": validar_consulta(consulta)})


def url_busqueda_canales(nombre):
    """Resultados de YouTube que son canales, para encontrar el de un creador."""
    return f"{reglas.YOUTUBE_URL}/results?" + urlencode({"search_query": validar_consulta(nombre),
                                                         "sp": FILTRO_CANALES})


def url_videos_de_canal(enlace):
    """
    La pestaña "Vídeos" de un canal (del más nuevo al más viejo) a partir del
    enlace que trae la página ("/@nombre" o "/channel/UC..."). Lanza Denegado
    si el enlace no es de un canal.
    """
    if not isinstance(enlace, str) or not _CANAL.fullmatch(enlace):
        raise Denegado("eso no es un canal de YouTube")
    return f"{reglas.YOUTUBE_URL}{enlace}/videos"


def url_video(enlace):
    """
    La dirección canónica de un vídeo a partir de un enlace de la página
    ("/watch?v=ID&list=..." o "https://www.youtube.com/watch?v=ID"). Lanza
    Denegado si el enlace no es de un vídeo de YouTube.
    """
    if not isinstance(enlace, str) or len(enlace) > reglas.LARGO_MAX_URL:
        raise Denegado("eso no es un vídeo de YouTube")
    if enlace.startswith("/") and not enlace.startswith("//"):
        enlace = reglas.YOUTUBE_URL + enlace
    if not host_en(enlace, reglas.YOUTUBE_DOMINIOS):
        raise Denegado("eso no es un vídeo de YouTube")
    partes = urlsplit(enlace)
    ids = parse_qs(partes.query).get("v", [])
    if partes.path != "/watch" or len(ids) != 1 or not _ID_VIDEO.fullmatch(ids[0]):
        raise Denegado("eso no es un vídeo de YouTube")
    return f"{reglas.YOUTUBE_URL}/watch?v={ids[0]}"


def limpiar_texto(texto, largo):
    """Título o canal leído de la página, para mostrárselo al usuario (nunca al LLM)."""
    if not isinstance(texto, str):
        return ""
    texto = " ".join(_CONTROLES.sub(" ", texto).split())
    return texto if len(texto) <= largo else texto[:largo] + "…"
