import json, os

ARCHIVO_MEMORIA = "data/memoria.json"
ARCHIVO_USUARIO = "data/memoria_usuario.json"
ARCHIVO_RESUMEN = "data/memoria_resumen.txt"
MAX_HISTORIAL   = 30

def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_memoria(historial):
    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

def truncar_historial(historial):
    if len(historial) > MAX_HISTORIAL:
        return historial[-MAX_HISTORIAL:]
    return historial

def cargar_usuario():
    if os.path.exists(ARCHIVO_USUARIO):
        with open(ARCHIVO_USUARIO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_usuario(usuario):
    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_USUARIO, "w", encoding="utf-8") as f:
        json.dump(usuario, f, indent=4, ensure_ascii=False)

def cargar_resumen():
    if os.path.exists(ARCHIVO_RESUMEN):
        with open(ARCHIVO_RESUMEN, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def guardar_resumen(resumen):
    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_RESUMEN, "w", encoding="utf-8") as f:
        f.write(resumen)


# ─── Notas explícitas del usuario ────────────────────────────────────────────

def agregar_nota(usuario_data, nota):
    """Agrega una nota a la memoria del usuario si no existe ya."""
    if "notas" not in usuario_data:
        usuario_data["notas"] = []
    nota = nota.strip().lower()
    if nota and nota not in usuario_data["notas"]:
        usuario_data["notas"].append(nota)
    return usuario_data


def olvidar_nota(usuario_data, fragmento):
    """Elimina notas que contengan el fragmento dado."""
    if "notas" not in usuario_data:
        return usuario_data, 0
    antes = len(usuario_data["notas"])
    usuario_data["notas"] = [
        n for n in usuario_data["notas"]
        if fragmento.lower() not in n.lower()
    ]
    eliminadas = antes - len(usuario_data["notas"])
    return usuario_data, eliminadas


def olvidar_campo(usuario_data, campo):
    """Elimina un campo específico del usuario (nombre, rol, intereses, notas)."""
    if campo in usuario_data:
        del usuario_data[campo]
    return usuario_data


def limpiar_historial_completo():
    """Borra el historial de conversación y el resumen."""
    if os.path.exists(ARCHIVO_MEMORIA):
        os.remove(ARCHIVO_MEMORIA)
    if os.path.exists(ARCHIVO_RESUMEN):
        os.remove(ARCHIVO_RESUMEN)


def consultar_memoria(usuario_data, resumen):
    """
    Genera un resumen legible de todo lo que CAIN sabe del usuario.
    """
    lineas = ["🧠 Esto es lo que sé de ti:\n"]

    if "nombre" in usuario_data:
        lineas.append(f"  • Nombre: {usuario_data['nombre']}")
    if "rol" in usuario_data:
        lineas.append(f"  • Rol: {usuario_data['rol']}")
    if "intereses" in usuario_data and usuario_data["intereses"]:
        lineas.append(f"  • Intereses: {', '.join(usuario_data['intereses'])}")
    if "notas" in usuario_data and usuario_data["notas"]:
        lineas.append(f"  • Notas personales:")
        for nota in usuario_data["notas"]:
            lineas.append(f"      - {nota}")
    if resumen:
        lineas.append(f"\n  • Resumen de conversaciones:\n    {resumen}")

    if len(lineas) == 1:
        return "🧠 Aún no tengo información guardada sobre ti."

    return "\n".join(lineas)