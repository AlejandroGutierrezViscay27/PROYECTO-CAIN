"""
Acceso a CAIN desde la red local (Fase 9).

Desde la propia máquina (localhost) se entra sin más. Desde otro dispositivo
hace falta el token de CAIN_TOKEN: se pasa una vez como /?token=... y queda
guardado en una cookie. Sin CAIN_TOKEN configurado solo entra localhost —
CAIN ejecuta código y toca archivos, no puede quedar abierto a toda la red.
"""
import hmac
import os
import secrets
import socket

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


def autorizado(conexion):
    host = conexion.client.host if conexion.client else ""
    return es_local(host) or token_valido(token_de(conexion), token_configurado())


def ip_local():
    """IP de esta máquina en la red local (la que usarían otros dispositivos)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # UDP no envía nada al conectar: solo elige la interfaz de salida.
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
