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
    "sistema_ventanas":  N0,   # Fase 10.1: el resultado va al usuario, nunca al LLM
    "sistema_info":      N0,
    "sistema_abrir_app": N1,   # Fase 10.2: solo apps de APPS_PERMITIDAS
    "sistema_abrir_url": N1,   # solo http(s), en el navegador de CAIN
    "sistema_multimedia": N1,  # play/pausa, siguiente, anterior
    "sistema_volumen":   N1,
    "spotify_que_suena": N0,   # Fase 10.4: solo la API de Spotify, nunca su ventana
    "spotify_mis_listas": N0,
    "spotify_buscar":    N0,
    "spotify_reproducir": N1,  # solo lo que exista en Spotify (URI de la API, no del LLM)
    "spotify_control":   N1,   # pausar, reanudar, siguiente, anterior, aleatorio
    "spotify_sugerir":   N1,   # cada propuesta del LLM se busca antes de sonar
    "spotify_dispositivo": N1, # pasar la música a otro dispositivo (id de la API, no del LLM)
    "navegador_pestanas": N1,  # Fase 10.3: cambiar, cerrar o recargar; "listar" baja a N0 (ver nivel_de)
    "youtube_buscar":    N0,   # los resultados van al usuario, nunca al LLM
    "youtube_reproducir": N1,  # solo vídeos de una página de YouTube (id de la página, no del LLM)
    "youtube_control":   N1,   # pausar, reanudar, siguiente
    "youtube_canal":     N1,   # lo último de un creador; solo listarlo baja a N0 (ver nivel_de)
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


# ─── Apps y URLs (Fase 10.2) ─────────────────────────────────────────────────

# Perfil propio del navegador de CAIN: no ve tus contraseñas, tu historial ni
# tus sesiones. Fuera del repo porque el repo está en OneDrive (las cookies se
# subirían a la nube), y en AppData, que las herramientas de archivo no tocan.
CARPETA_NAVEGADOR = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local"),
    "CAIN", "navegador")


def apps_permitidas():
    """
    Apps que CAIN puede abrir: nombre → rutas exactas candidatas (se usa la
    primera que exista). Por ruta y no por nombre: un "brave.exe" en Descargas
    no es Brave. Nunca con argumentos del LLM. La lista se amplía aquí, a mano.
    """
    archivos = _entorno("ProgramFiles", r"C:\Program Files")
    archivos_x86 = _entorno("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = _entorno("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
    roaming = _entorno("APPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
    return {
        # El navegador de CAIN: Brave (el tuyo) y, si no está, Edge. Siempre
        # con el perfil de CARPETA_NAVEGADOR (ver argumentos_app).
        "navegador": [
            os.path.join(archivos, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(local, "BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            os.path.join(archivos_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(archivos, "Microsoft", "Edge", "Application", "msedge.exe"),
        ],
        "spotify": [
            os.path.join(roaming, "Spotify", "Spotify.exe"),
            os.path.join(local, "Microsoft", "WindowsApps", "Spotify.exe"),   # Microsoft Store
        ],
    }


def argumentos_app(nombre):
    """Argumentos fijos con que se abre cada app. El LLM no añade ninguno."""
    if nombre == "navegador":
        return [f"--user-data-dir={CARPETA_NAVEGADOR}", "--no-first-run", "--no-default-browser-check"]
    return []


ESQUEMAS_URL = frozenset({"http", "https"})
LARGO_MAX_URL = 2000

# Nombres de la red local: el navegador de CAIN no entra en el router, en
# otros equipos de casa ni en el propio CAIN.
SUFIJOS_LOCALES = (".localhost", ".local", ".lan", ".home", ".internal", ".intranet",
                   ".corp", ".home.arpa")


# ─── Navegador de CAIN y YouTube (Fase 10.3) ─────────────────────────────────

# Argumentos fijos con que Playwright abre el navegador de CAIN (el perfil va
# aparte, CARPETA_NAVEGADOR). Los vídeos que pide el usuario suenan sin
# tener que hacer clic en la página.
ARGUMENTOS_NAVEGADOR = ("--no-first-run", "--no-default-browser-check",
                        "--autoplay-policy=no-user-gesture-required")

# Argumentos que Playwright pone por defecto y CAIN quita: sin el bloqueador
# de popups, cualquier página (un anuncio) abre pestañas solas (las about:blank
# de la prueba del 29/10); sin la detección de phishing, menos protección.
# --enable-automation pinta la barra de "controlado por software de prueba".
# El sandbox se pide aparte (chromium_sandbox=True en so/navegador.py).
ARGUMENTOS_PLAYWRIGHT_QUITADOS = ("--enable-automation", "--disable-popup-blocking",
                                  "--disable-client-side-phishing-detection")

# Cuánto se espera al navegador en cada petición (abrirlo la primera vez
# incluido) y a que una página muestre lo que se busca en ella.
NAVEGADOR_TIEMPO_MAX = 30   # segundos
NAVEGADOR_ESPERA_PAGINA = 12
NAVEGADOR_TIEMPO_APAGAR = 3  # al apagar CAIN, para cerrarlo limpio

# Pestañas como máximo: CAIN no abre una más pasado esto.
MAX_PESTANAS = 15

# Dónde actúa el conector de YouTube (el dominio y sus subdominios). Fuera de
# aquí, CAIN puede abrir una página, pero no hace nada dentro de ella.
YOUTUBE_DOMINIOS = ("youtube.com",)
YOUTUBE_URL      = "https://www.youtube.com"


# ─── Spotify (Fase 10.4) ─────────────────────────────────────────────────────

# Los únicos sitios con los que habla el conector. Las URLs que devuelve la
# API ("next", "href") nunca se siguen: cada petición se arma con estas bases.
SPOTIFY_URL_AUTORIZAR = "https://accounts.spotify.com/authorize"
SPOTIFY_URL_TOKEN     = "https://accounts.spotify.com/api/token"
SPOTIFY_URL_API       = "https://api.spotify.com/v1"

# Mínimo privilegio: leer y controlar la reproducción, leer listas y gustos.
# Ninguno de escritura sobre listas ni biblioteca: aunque hubiera un error,
# la API no dejaría a CAIN borrar ni cambiar nada tuyo.
SPOTIFY_PERMISOS = (
    "user-read-playback-state", "user-modify-playback-state", "user-read-currently-playing",
    "playlist-read-private", "playlist-read-collaborative", "user-top-read", "user-library-read",
)

# Si no hay dispositivo, CAIN abre la app de escritorio y espera a que aparezca.
SPOTIFY_ESPERA_DISPOSITIVO = 15   # segundos


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

# Las que heredan las apps que abre CAIN (Fase 10.2): las del sistema, nunca
# las del .env.
ENTORNO_APPS = (ENTORNO_PERMITIDO - {"VIRTUAL_ENV"}) | frozenset({
    "ALLUSERSPROFILE", "PUBLIC", "COMPUTERNAME", "USERDOMAIN", "SESSIONNAME",
    "LOGONSERVER", "PROCESSOR_IDENTIFIER", "PROCESSOR_LEVEL", "PROCESSOR_REVISION",
    "COMMONPROGRAMW6432", "USERDOMAIN_ROAMINGPROFILE", "DRIVERDATA",
})
