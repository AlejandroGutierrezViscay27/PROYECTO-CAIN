import os
import shutil
import time

from send2trash import send2trash

from core.arnes import reglas


# Las rutas que reciben estas funciones ya pasaron por arnes.rutas.resolver():
# aquí no se valida nada, se ejecuta. Nunca llamarlas con una ruta del LLM.


# ─── Utilidades internas ─────────────────────────────────────────────────────

def generar_nombre_timestamp():
    """Nombre de fallback con timestamp si la IA no genera uno."""
    return f"archivo_{int(time.time())}.txt"


def evitar_sobrescritura(nombre):
    """Si el archivo ya existe, agrega sufijo numérico."""
    base, extension = os.path.splitext(nombre)
    contador = 1
    nuevo_nombre = nombre
    while os.path.exists(nuevo_nombre):
        nuevo_nombre = f"{base}_{contador}{extension}"
        contador += 1
    return nuevo_nombre


def normalizar_nombre_txt(nombre):
    """Agrega la extensión .txt si el nombre no tiene ninguna."""
    if not os.path.splitext(nombre)[1]:
        return nombre + ".txt"
    return nombre


def respaldar(ruta, espacio):
    """
    Copia la versión actual a <espacio>/.respaldos/ antes de pisarla.
    Retorna la ruta de la copia.
    """
    carpeta = os.path.join(espacio, reglas.CARPETA_RESPALDOS)
    os.makedirs(carpeta, exist_ok=True)
    base, extension = os.path.splitext(os.path.basename(ruta))
    copia = evitar_sobrescritura(os.path.join(carpeta, f"{base}_{time.strftime('%Y%m%d-%H%M%S')}{extension}"))
    shutil.copy2(ruta, copia)
    return copia


# ─── Operaciones de archivo ──────────────────────────────────────────────────

def crear_archivo(ruta, contenido):
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        # "x": falla si el archivo apareció entre la comprobación y la escritura.
        with open(ruta, "x", encoding="utf-8") as f:
            f.write(contenido)
        return True, None
    except Exception as e:
        return False, str(e)


def leer_archivo(ruta):
    """(contenido, recortado) — como mucho reglas.BYTES_MAX_LECTURA."""
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        contenido = f.read(reglas.BYTES_MAX_LECTURA + 1)
    if len(contenido) > reglas.BYTES_MAX_LECTURA:
        return contenido[:reglas.BYTES_MAX_LECTURA], True
    return contenido, False


def mover_a_papelera(ruta):
    """Nunca borra para siempre: el archivo se puede recuperar de la Papelera."""
    try:
        send2trash(ruta)
        return True, None
    except Exception as e:
        return False, str(e)


def editar_archivo(ruta, contenido):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return True, None
    except Exception as e:
        return False, str(e)
