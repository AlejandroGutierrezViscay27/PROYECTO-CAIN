"""
Resolución y verificación de rutas (Fase 10).

Toda ruta que viene del LLM pasa por aquí antes de tocar el disco. Se
rechaza lo dudoso ANTES de resolver (UNC, dispositivos, variables, streams
alternativos...) y lo resuelto se compara contra las zonas de reglas.py
después de seguir symlinks y junctions. Si algo no se puede decidir con
certeza, se deniega.
"""
import fnmatch
import os
import re

from core.arnes import reglas


class Denegado(Exception):
    """Una acción o ruta que el arnés no permite. El mensaje es el motivo."""


_CARACTERES_PROHIBIDOS = set('*?"<>|') | {chr(c) for c in range(32)}
_UNIDAD = re.compile(r"^[A-Za-z]:")


def _normal(ruta):
    return os.path.normcase(os.path.realpath(ruta))


def dentro_de(ruta, carpeta):
    """True si `ruta` es `carpeta` o está debajo. Ambas ya resueltas."""
    ruta, carpeta = _normal(ruta), _normal(carpeta)
    try:
        return os.path.commonpath([ruta, carpeta]) == carpeta
    except ValueError:   # distintas unidades
        return False


def _revisar_texto(texto):
    """Lo que se rechaza sin siquiera resolver la ruta."""
    if not isinstance(texto, str) or not texto.strip():
        raise Denegado("la ruta está vacía")
    if len(texto) > reglas.LARGO_MAX_RUTA:
        raise Denegado("la ruta es demasiado larga")
    if texto.startswith(("\\\\", "//")):
        raise Denegado("no se permiten rutas de red ni de dispositivo")
    if "%" in texto or texto.startswith("~") or "$" in texto:
        raise Denegado("no se expanden variables en las rutas")
    if set(texto) & _CARACTERES_PROHIBIDOS:
        raise Denegado("la ruta tiene caracteres no permitidos")
    # Un ":" que no sea la letra de unidad abre un "alternate data stream".
    if ":" in _UNIDAD.sub("", texto, count=1):
        raise Denegado("la ruta tiene ':' fuera de la unidad")

    for parte in re.split(r"[\\/]", texto):
        if parte in ("", ".", ".."):
            continue
        # Windows ignora los puntos y espacios finales: "agent.py." es agent.py.
        if parte != parte.rstrip(". "):
            raise Denegado("un nombre no puede terminar en punto o espacio")
        base = parte.split(".")[0].upper()
        if base in reglas.NOMBRES_RESERVADOS:
            raise Denegado(f"'{parte}' es un nombre reservado de Windows")


def _nombre_prohibido(ruta):
    for parte in re.split(r"[\\/]", ruta):
        parte = parte.lower()
        if any(fnmatch.fnmatch(parte, patron) for patron in reglas.NOMBRES_PROHIBIDOS):
            return parte
    return None


def verificar(ruta):
    """
    Revisa una ruta ya resuelta contra las zonas prohibidas.
    Lanza Denegado con el motivo; si pasa, no devuelve nada.
    """
    for nunca in reglas.rutas_nunca():
        if dentro_de(ruta, nunca):
            raise Denegado("es una carpeta del sistema")

    propias = reglas.zonas_propias()
    for protegida in reglas.rutas_protegidas():
        if not dentro_de(ruta, protegida):
            continue
        excepcion = any(dentro_de(ruta, z) and dentro_de(z, protegida) for z in propias)
        if not excepcion:
            if dentro_de(protegida, reglas.RAIZ_CAIN):
                raise Denegado("es parte de mi propio código o configuración")
            raise Denegado("es una carpeta protegida (credenciales o datos de aplicaciones)")

    prohibido = _nombre_prohibido(ruta)
    if prohibido:
        raise Denegado(f"'{prohibido}' puede contener credenciales")


def resolver(texto, zona, escritura=False):
    """
    Ruta absoluta de `texto` dentro de `zona`, o Denegado con el motivo.

    Las rutas relativas se resuelven contra la zona, nunca contra el cwd.
    Una absoluta solo vale si cae dentro de la zona. Con escritura=True,
    además, la extensión tiene que estar en la lista blanca.
    """
    _revisar_texto(texto)
    zona_real = os.path.realpath(zona)
    for nunca in reglas.rutas_nunca():
        # Defensa contra un error en reglas.py: una zona nunca puede ser del sistema.
        if dentro_de(zona_real, nunca):
            raise Denegado("la zona de trabajo está en una carpeta del sistema")

    # realpath sigue symlinks y junctions: una junction dentro del espacio que
    # apunte a System32 se resuelve a System32 y la atrapa verificar().
    ruta = os.path.realpath(os.path.join(zona_real, texto))
    if not dentro_de(ruta, zona_real) or _normal(ruta) == _normal(zona_real):
        raise Denegado("está fuera de mi espacio de trabajo")
    verificar(ruta)

    if escritura:
        extension = os.path.splitext(ruta)[1]
        if extension not in reglas.EXTENSIONES_ESCRITURA:
            raise Denegado(f"no escribo archivos '{extension or 'sin extensión'}'")
    return ruta


def para_mostrar(ruta, zona):
    """Ruta relativa a la zona, para enseñársela al usuario."""
    try:
        return os.path.relpath(ruta, zona)
    except ValueError:
        return os.path.basename(ruta)
