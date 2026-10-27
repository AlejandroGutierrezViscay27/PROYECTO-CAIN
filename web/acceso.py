"""
Acceso a CAIN desde la red local (Fase 9).

Desde la propia máquina (localhost) se entra sin más. Desde otro dispositivo
hace falta el token de CAIN_TOKEN: se pasa una vez como /?token=... y queda
guardado en una cookie. Sin CAIN_TOKEN configurado solo entra localhost —
CAIN ejecuta código y toca archivos, no puede quedar abierto a toda la red.
"""
import hashlib
import hmac
import os
import secrets
import socket
from urllib.parse import urlsplit

COOKIE        = "cain_token"
HOSTS_LOCALES = {"127.0.0.1", "::1", "localhost"}


def token_configurado():
    return os.getenv("CAIN_TOKEN", "").strip()


def generar_token():
    return secrets.token_urlsafe(24)


def es_local(host):
    return host in HOSTS_LOCALES


def token_valido(recibido, esperado):
    """Compara en tiempo constante. Sin token esperado, nada es válido."""
    if not esperado or not recibido:
        return False
    return hmac.compare_digest(recibido.encode("utf-8"), esperado.encode("utf-8"))


def token_de(conexion):
    """
    Token que trae una petición HTTP o un WebSocket (ambos de Starlette):
    query ?token=, cookie o cabecera Authorization: Bearer.
    """
    token = conexion.query_params.get("token") or conexion.cookies.get(COOKIE)
    if token:
        return token
    autorizacion = conexion.headers.get("authorization", "")
    if autorizacion.lower().startswith("bearer "):
        return autorizacion[7:].strip()
    return ""


def _nombre_de_host(cabecera):
    """'localhost:8000' -> 'localhost', '[::1]:8000' -> '::1'."""
    cabecera = cabecera.strip().lower()
    if cabecera.startswith("["):
        return cabecera[1:].split("]")[0]
    return cabecera.rsplit(":", 1)[0] if cabecera.count(":") == 1 else cabecera


def acceso_local(conexion):
    """
    La propia máquina, pidiendo por un nombre de loopback. Lo segundo cierra
    el "DNS rebinding": una web cualquiera cuyo dominio resuelve a 127.0.0.1
    llega desde localhost, pero su cabecera Host es la de ese dominio.
    """
    cliente = conexion.client.host if conexion.client else ""
    return es_local(cliente) and es_local(_nombre_de_host(conexion.headers.get("host", "")))


def autorizado(conexion):
    return acceso_local(conexion) or token_valido(token_de(conexion), token_configurado())


def origen_permitido(conexion):
    """
    El navegador manda la cabecera Origin en todo WebSocket, y no aplica CORS:
    sin este chequeo, cualquier página abierta en el PC podría conectarse a
    ws://localhost:8000/ws y darle órdenes a CAIN. Solo vale el mismo origen.
    Sin Origin no es un navegador (y entonces no lo maneja ninguna web).
    """
    origen = conexion.headers.get("origin")
    if origen is None:
        return True
    host = conexion.headers.get("host", "").strip().lower()
    return bool(host) and urlsplit(origen.strip().lower()).netloc == host


# ─── Proyectos web ───────────────────────────────────────────────────────────
# Se sirven con CSP "sandbox" (origen opaco): su JavaScript no puede usar la
# cookie de CAIN ni abrir su WebSocket. Como sin cookie el móvil no podría
# cargar ni el CSS del proyecto, la URL lleva una firma que hace de permiso
# de solo lectura para ESE proyecto. La clave cambia en cada arranque.

_CLAVE_PROYECTOS = secrets.token_bytes(32)


def firma_proyecto(nombre):
    return hmac.new(_CLAVE_PROYECTOS, nombre.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def firma_valida(nombre, firma):
    return hmac.compare_digest(firma_proyecto(nombre).encode(), firma.encode("utf-8", "replace"))


def ip_local():
    """IP de esta máquina en la red local (la que usarían otros dispositivos)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # UDP no envía nada al conectar: solo elige la interfaz de salida.
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
