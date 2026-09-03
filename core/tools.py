import os
import time


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


# ─── Operaciones de archivo ──────────────────────────────────────────────────

def crear_archivo(nombre, contenido):
    try:
        with open(nombre, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"Archivo '{nombre}' creado correctamente."
    except Exception as e:
        return f"Error al crear archivo: {str(e)}"


def leer_archivo(nombre):
    try:
        with open(nombre, "r", encoding="utf-8") as f:
            contenido = f.read()
        return f"📖 Contenido de '{nombre}':\n\n{contenido}"
    except FileNotFoundError:
        return f"🎭 No encontré el archivo '{nombre}'."
    except Exception as e:
        return f"Error al leer archivo: {str(e)}"


def borrar_archivo(nombre):
    try:
        if os.path.exists(nombre):
            os.remove(nombre)
            return f"🗑️ Archivo '{nombre}' eliminado correctamente."
        return f"🎭 El archivo '{nombre}' no existe."
    except Exception as e:
        return f"Error al eliminar archivo: {str(e)}"


def editar_archivo(nombre, contenido):
    try:
        with open(nombre, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"✏️ Archivo '{nombre}' actualizado."
    except Exception as e:
        return f"Error en edición: {str(e)}"


def agregar_a_archivo(nombre, contenido):
    try:
        with open(nombre, "a", encoding="utf-8") as f:
            f.write("\n\n" + contenido)
        return f"✏️ Contenido añadido a '{nombre}'."
    except Exception as e:
        return f"Error al editar archivo: {str(e)}"