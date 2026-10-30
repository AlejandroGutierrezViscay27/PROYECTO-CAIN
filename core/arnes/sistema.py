"""
Límites de lo que CAIN hace en el sistema (Fase 10.2): qué apps abre, qué
URLs, qué teclas multimedia y qué volumen.

Todo lo que propone el LLM pasa por aquí antes de llegar a so/, y so/ lo
vuelve a comprobar antes de actuar.
"""
import ipaddress
import os
import re
from urllib.parse import urlsplit

from core.arnes import reglas
from core.arnes.rutas import Denegado

ACCIONES_MULTIMEDIA = ("reproducir_pausar", "siguiente", "anterior")
ACCIONES_VOLUMEN    = ("subir", "bajar", "fijar", "silenciar", "activar_sonido")

# Espacios, controles, comillas y barras invertidas: nada de eso va en una URL
# bien formada, y en una línea de comandos podría partirla en dos argumentos.
_CARACTERES_PROHIBIDOS = re.compile(r'[\s\x00-\x1f\x7f"\\<>`^{}|]')
_ETIQUETA_TLD = re.compile(r"^(?:[a-z]{2,63}|xn--[a-z0-9-]{1,59})$")


def resolver_app(nombre):
    """
    Ruta exacta del ejecutable de una app de la lista blanca y sus argumentos
    fijos. Lanza Denegado si no está en la lista o no está instalada.
    """
    if not isinstance(nombre, str):
        raise Denegado("no sé qué app abrir")
    nombre = nombre.strip().lower()
    candidatas = reglas.apps_permitidas().get(nombre)
    if candidatas is None:
        disponibles = ", ".join(sorted(reglas.apps_permitidas()))
        raise Denegado(f"solo puedo abrir estas apps: {disponibles}")
    for ruta in candidatas:
        if os.path.exists(ruta):
            return ruta, reglas.argumentos_app(nombre)
    raise Denegado(f"no encuentro {nombre} instalado en este PC")


def es_ejecutable_permitido(ruta):
    """Para so/: la ruta que se va a lanzar es una de la lista blanca, exacta."""
    if not isinstance(ruta, str):
        return False
    normal = os.path.normcase(os.path.normpath(ruta))
    return any(normal == os.path.normcase(os.path.normpath(candidata))
               for candidatas in reglas.apps_permitidas().values() for candidata in candidatas)


def validar_url(texto):
    """
    Devuelve la URL si se puede abrir en el navegador de CAIN; si no, lanza
    Denegado. Solo http(s) hacia internet: ni otros esquemas (file:,
    javascript:, ms-settings:...), ni la red local, ni usuario@ en la URL.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise Denegado("falta la dirección")
    url = texto.strip()
    if len(url) > reglas.LARGO_MAX_URL:
        raise Denegado("la dirección es demasiado larga")
    if _CARACTERES_PROHIBIDOS.search(url):
        raise Denegado("la dirección tiene caracteres que no van en una URL")

    try:
        partes = urlsplit(url)
        host = partes.hostname
        partes.port   # lanza ValueError si el puerto no es un número válido
    except ValueError:
        raise Denegado("la dirección no es válida")
    if partes.scheme.lower() not in reglas.ESQUEMAS_URL:
        raise Denegado("solo abro direcciones http o https")
    if not host:
        raise Denegado("la dirección no tiene sitio")
    if "@" in partes.netloc:
        raise Denegado("la dirección esconde el sitio real tras un usuario@")

    _revisar_host(host.rstrip("."))
    return url


def _revisar_host(host):
    """Solo sitios de internet: un dominio con TLD de letras o una IP pública."""
    if host == "localhost" or host.endswith(reglas.SUFIJOS_LOCALES):
        raise Denegado("no abro direcciones de la red local")
    ultima = host.rsplit(".", 1)[-1]
    if "." in host and _ETIQUETA_TLD.match(ultima):
        return
    # Sin TLD de letras: tiene que ser una IP pública escrita normal. Las formas
    # raras ("2130706433", "0x7f.1") el navegador las lee como 127.0.0.1.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        raise Denegado("no reconozco el sitio de esa dirección")
    if not ip.is_global:
        raise Denegado("no abro direcciones de la red local")


def es_destino_local(url):
    """
    Para el navegador de CAIN (10.3): True si una petición que hace una
    página va a la red local (el router, otro equipo, el propio CAIN). Se
    mira solo el sitio: las páginas piden URLs largas o con caracteres que
    validar_url() no admite y que aquí no importan.
    """
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return True
    if not host:
        return False
    try:
        _revisar_host(host.rstrip("."))
    except Denegado:
        return True
    return False


def host_en(url, dominios):
    """True si la URL es http(s) y su sitio es uno de `dominios` o un subdominio suyo."""
    try:
        partes = urlsplit(url)
        host = (partes.hostname or "").rstrip(".")
    except ValueError:
        return False
    if partes.scheme.lower() not in reglas.ESQUEMAS_URL or not host:
        return False
    return any(host == d or host.endswith("." + d) for d in dominios)


def entorno_apps():
    """Las variables de entorno que heredan las apps que abre CAIN: sin secretos del .env."""
    return {k: v for k, v in os.environ.items() if k.upper() in reglas.ENTORNO_APPS}


ACCIONES_PESTANAS = ("listar", "cambiar", "cerrar", "recargar")


def validar_accion_pestanas(accion):
    if accion not in ACCIONES_PESTANAS:
        raise Denegado("esa acción de pestañas no existe")
    return accion


def validar_numero(valor, cantidad):
    """Un número de una lista que vio el usuario (1..cantidad). Lanza Denegado si no."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise Denegado("falta el número")
    if not 1 <= valor <= cantidad:
        raise Denegado(f"no hay un número {valor} en la lista (hay {cantidad})")
    return valor


def validar_multimedia(accion):
    if accion not in ACCIONES_MULTIMEDIA:
        raise Denegado("esa acción multimedia no existe")
    return accion


def validar_volumen(accion, valor):
    """Devuelve (accion, valor) con el valor como entero 0-100, o lanza Denegado."""
    if accion not in ACCIONES_VOLUMEN:
        raise Denegado("esa acción de volumen no existe")
    if accion in ("silenciar", "activar_sonido"):
        return accion, None
    if valor is None and accion in ("subir", "bajar"):
        valor = 10
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise Denegado("falta cuánto volumen")
    valor = int(round(valor))
    if not 0 <= valor <= 100:
        raise Denegado("el volumen va de 0 a 100")
    return accion, valor
