"""
Reglas del arnés de seguridad (Fase 10).

Viven en el código a propósito: CAIN no puede cambiarlas porque el propio
arnés le prohíbe escribir en su repo. Solo una persona, editando este
archivo, cambia lo que CAIN puede hacer.
"""
import os

# ─── Niveles de acción ───────────────────────────────────────────────────────

N0 = 0   # observar: solo lectura, sin secretos
N1 = 1   # reversible: efecto visible y fácil de deshacer
N2 = 2   # con efecto: siempre se confirma en el dispositivo que lo pidió
N3 = 3   # destructivo: se confirma y nunca es permanente (Papelera, respaldos)

NOMBRE_NIVEL = {N0: "N0", N1: "N1", N2: "N2", N3: "N3"}

# Desde este nivel, la acción no se ejecuta sin confirmación.
NIVEL_CONFIRMACION = N2

# Nivel de cada herramienta. Una herramienta que no está aquí NO se ejecuta.
NIVEL_HERRAMIENTA = {
    "leer_archivo":      N0,
    "memoria_consultar": N0,
    "crear_archivo":     N1,   # nunca sobrescribe
    "editar_archivo":    N1,   # guarda la versión anterior en .respaldos/
    "memoria_recordar":  N1,
    "memoria_olvidar":   N1,   # "todo" e "historial" suben a N3 (ver nivel_de)
    "ejecutar_proyecto": N2,
    "borrar_archivo":    N3,   # va a la Papelera
}

# Herramientas que solo se pueden pedir desde el propio PC (p. ej. teclado y
# ratón en la Fase 10.4: quien pide desde el móvil no ve la pantalla).
SOLO_LOCAL = frozenset()

# Nivel máximo de lo que se pide desde otro dispositivo de la red (decisión
# del usuario, Fase 10): poner música o un vídeo sí; enviar, borrar o
# ejecutar código, solo desde el propio PC.
NIVEL_MAX_REMOTO = N1

# Si CAIN corre como administrador, nada por encima de N1: el código generado
# heredaría permisos para tocar el sistema entero.
NIVEL_MAX_ELEVADO = N1


# ─── Zonas ───────────────────────────────────────────────────────────────────

RAIZ_CAIN = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Dónde viven los archivos que CAIN crea, lee, edita y borra.
CARPETA_ESPACIO   = os.path.join(RAIZ_CAIN, "espacio")
CARPETA_PROYECTOS = os.path.join(RAIZ_CAIN, "proyectos")

# Respaldos de las ediciones, dentro del espacio.
CARPETA_RESPALDOS = ".respaldos"


def zonas_propias():
    """Carpetas de CAIN que son excepción dentro de una zona protegida."""
    return [CARPETA_ESPACIO, CARPETA_PROYECTOS]


def _entorno(nombre, defecto):
    return os.environ.get(nombre) or defecto


def rutas_nunca():
    """
    Sistema: no se tocan nunca, ni siquiera desde una zona propia de CAIN.
    Se leen siempre del entorno real (el LLM no puede influir en él) y además
    con su valor por defecto, por si una variable estuviera vacía o cambiada.
    """
    unidad = _entorno("SystemDrive", "C:")
    rutas = {
        _entorno("SystemRoot", r"C:\Windows"), r"C:\Windows",
        _entorno("ProgramFiles", r"C:\Program Files"), r"C:\Program Files",
        _entorno("ProgramFiles(x86)", r"C:\Program Files (x86)"), r"C:\Program Files (x86)",
        _entorno("ProgramW6432", r"C:\Program Files"),
        _entorno("ProgramData", r"C:\ProgramData"), r"C:\ProgramData",
    }
    # Ojo: nada que sea una junction hacia algo amplio. "Documents and Settings"
    # apunta a C:\Users y, resuelto, prohibiría todo el perfil del usuario.
    for nombre in ("$Recycle.Bin", "System Volume Information", "Recovery", "Boot", "EFI",
                   "pagefile.sys", "hiberfil.sys", "swapfile.sys", "bootmgr"):
        rutas.add(os.path.join(unidad + os.sep, nombre))
    return sorted(rutas)


def rutas_protegidas():
    """
    Protegidas: no se tocan, salvo las zonas propias de CAIN que caen dentro
    (espacio/ y proyectos/ dentro del repo).
    """
    perfil = os.path.expanduser("~")
    rutas = [RAIZ_CAIN, os.path.join(perfil, "AppData")]
    for nombre in (".ssh", ".aws", ".azure", ".gnupg", ".kube", ".docker", ".claude",
                   ".config", ".git-credentials", ".npmrc", ".pypirc", ".netrc"):
        rutas.append(os.path.join(perfil, nombre))
    return rutas


# Nombres de archivo o carpeta que nunca se tocan, estén donde estén.
# (fnmatch, sin distinguir mayúsculas)
NOMBRES_PROHIBIDOS = (
    ".env", "*.env", ".env.*",
    "*.pem", "*.key", "*.pfx", "*.p12", "*.kdbx", "*.ppk",
    "id_rsa*", "id_ed25519*", "id_ecdsa*", "id_dsa*",
    "*credential*", "*.git-credentials", ".netrc", ".npmrc", ".pypirc",
    ".git", ".ssh",
)

# Nombres de dispositivo de Windows: abrir "CON" o "nul.txt" no es un archivo.
NOMBRES_RESERVADOS = frozenset(
    ["CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"]
    + [f"COM{i}" for i in range(10)] + [f"LPT{i}" for i in range(10)]
    + ["COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³"]
)

# Extensiones que CAIN puede escribir en su espacio (lista blanca: texto).
# Nada ejecutable (.exe, .bat, .ps1, .lnk, .reg...).
EXTENSIONES_ESCRITURA = frozenset({
    ".txt", ".md", ".csv", ".json", ".html", ".css", ".js", ".py",
    ".xml", ".yaml", ".yml", ".log", ".svg",
})

LARGO_MAX_RUTA = 240


# ─── Límites ─────────────────────────────────────────────────────────────────

# Lo máximo que se lee de un archivo para mostrarlo o mandarlo al LLM.
BYTES_MAX_LECTURA = 100_000

# Variables de entorno que hereda el código generado. Ninguna otra: ni
# OPENAI_API_KEY, ni CAIN_TOKEN, ni ningún otro secreto del .env.
ENTORNO_PERMITIDO = frozenset({
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "USERNAME",
    "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)",
    "PROGRAMW6432", "COMMONPROGRAMFILES", "COMMONPROGRAMFILES(X86)",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "OS", "LANG",
    "VIRTUAL_ENV",
})
