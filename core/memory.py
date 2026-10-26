import json, os, tempfile, time

ARCHIVO_MEMORIA = "data/memoria.json"
ARCHIVO_USUARIO = "data/memoria_usuario.json"
ARCHIVO_RESUMEN = "data/memoria_resumen.txt"   # formato viejo, solo se lee para migrar
ARCHIVO_LARGA   = "data/memoria_larga.json"
MAX_HISTORIAL   = 30
MAX_VERSIONES_NOTAS = 20


# ─── Escritura atómica ───────────────────────────────────────────────────────
# Se escribe a un temporal en la misma carpeta y se reemplaza de un golpe:
# si el proceso muere a mitad, el archivo anterior queda intacto en vez de
# quedar un JSON cortado que luego no carga.

def _escribir_atomico(ruta, texto):
    carpeta = os.path.dirname(ruta) or "."
    os.makedirs(carpeta, exist_ok=True)
    fd, temporal = tempfile.mkstemp(dir=carpeta, prefix=".tmp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(texto)
        os.replace(temporal, ruta)
    except Exception:
        try:
            os.unlink(temporal)
        except FileNotFoundError:
            pass
        raise


def _guardar_json(ruta, datos):
    _escribir_atomico(ruta, json.dumps(datos, indent=4, ensure_ascii=False))


def _cargar_json(ruta, por_defecto):
    if not os.path.exists(ruta):
        return por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return por_defecto


# ─── Historial y usuario ─────────────────────────────────────────────────────

def cargar_memoria():
    return _cargar_json(ARCHIVO_MEMORIA, [])

def guardar_memoria(historial):
    _guardar_json(ARCHIVO_MEMORIA, historial)

def truncar_historial(historial):
    if len(historial) > MAX_HISTORIAL:
        return historial[-MAX_HISTORIAL:]
    return historial

def cargar_usuario():
    return _cargar_json(ARCHIVO_USUARIO, {})

def guardar_usuario(usuario):
    _guardar_json(ARCHIVO_USUARIO, usuario)


# ─── Memoria a largo plazo (la mantiene el director, ver core/director.py) ───

def memoria_larga_vacia():
    return {
        "hechos":             [],   # datos duraderos del usuario (solo crece o se corrige)
        "notas":              "",   # en qué anda el usuario ahora, en primera persona
        "historial_notas":    [],   # versiones anteriores de "notas": nada se pierde
        "eventos_archivados": [],   # temas que se cerraron, archivados como relato corto
        "temas_abiertos":     [],   # hilos pendientes con el usuario
        "guia":               {},   # lectura estratégica del director para CAIN
        "actualizado":        None,
    }


def cargar_memoria_larga():
    mem = _cargar_json(ARCHIVO_LARGA, None)
    if mem is None:
        mem = memoria_larga_vacia()
        # Migración: el resumen de 3 líneas de antes entra como un hecho. Como
        # notas, el director lo reescribía y perdía datos; como hecho se queda
        # hasta que algo lo contradiga.
        if os.path.exists(ARCHIVO_RESUMEN):
            with open(ARCHIVO_RESUMEN, "r", encoding="utf-8") as f:
                resumen = f.read().strip()
            if resumen:
                mem["hechos"] = [f"De conversaciones anteriores: {resumen}"]
        return mem
    vacia = memoria_larga_vacia()
    vacia.update(mem)
    return vacia


def guardar_memoria_larga(mem):
    mem["actualizado"] = time.time()
    mem["historial_notas"] = mem.get("historial_notas", [])[-MAX_VERSIONES_NOTAS:]
    _guardar_json(ARCHIVO_LARGA, mem)


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
    """Borra el historial de conversación y la memoria a largo plazo."""
    for ruta in (ARCHIVO_MEMORIA, ARCHIVO_RESUMEN, ARCHIVO_LARGA):
        if os.path.exists(ruta):
            os.remove(ruta)


def consultar_memoria(usuario_data, memoria_larga):
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

    if memoria_larga.get("hechos"):
        lineas.append(f"\n  • Lo que he ido aprendiendo de ti:")
        for hecho in memoria_larga["hechos"]:
            lineas.append(f"      - {hecho}")
    if memoria_larga.get("notas"):
        lineas.append(f"  • En qué andas:\n    {memoria_larga['notas']}")
    if memoria_larga.get("temas_abiertos"):
        lineas.append(f"  • Temas que tenemos pendientes:")
        for tema in memoria_larga["temas_abiertos"]:
            lineas.append(f"      - {tema}")
    eventos = memoria_larga.get("eventos_archivados", [])[-3:]
    if eventos:
        lineas.append(f"  • Lo último que cerramos:")
        for e in eventos:
            lineas.append(f"      - {e['evento']}")

    if len(lineas) == 1:
        return "🧠 Aún no tengo información guardada sobre ti."

    return "\n".join(lineas)
