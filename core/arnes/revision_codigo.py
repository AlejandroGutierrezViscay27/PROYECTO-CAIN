"""
Revisión estática del Python que genera el LLM (Fase 10).

NO es una garantía: el código se puede ofuscar. Sirve para dos cosas:
- Avisar en la confirmación de qué hace el código que merezca atención
  ("borra archivos", "lanza otros programas").
- Rechazar el código que nombra literalmente una ruta prohibida (el repo
  de CAIN, System32, .ssh...).
La frontera real es el entorno mínimo del proceso hijo y, en la Fase 10.5,
el aislamiento del propio Windows.
"""
import ast
import re

from core.arnes import reglas
from core.arnes.rutas import Denegado, verificar

MODULOS = {
    "subprocess": "lanza otros programas",
    "ctypes":     "llama directamente a funciones de Windows",
    "winreg":     "toca el registro de Windows",
    "_winapi":    "llama directamente a funciones de Windows",
    "socket":     "abre conexiones de red",
    "requests":   "se conecta a internet",
    "urllib":     "se conecta a internet",
    "http":       "se conecta a internet",
    "httpx":      "se conecta a internet",
    "ftplib":     "se conecta a internet",
    "smtplib":    "envía correos",
    "webbrowser": "abre el navegador",
    "pyautogui":  "controla el teclado y el ratón",
    "keyboard":   "controla el teclado",
    "pynput":     "controla el teclado y el ratón",
    "multiprocessing": "lanza otros procesos",
}

# Funciones de os/shutil → aviso. Solo con el módulo delante (os.remove), o
# importadas con "from os import remove": list.remove o str.replace no cuentan.
LLAMADAS_MODULO = {
    "system": "ejecuta comandos de consola", "popen": "ejecuta comandos de consola",
    "startfile": "abre programas o archivos", "kill": "termina procesos",
    "spawnl": "lanza otros programas", "spawnv": "lanza otros programas",
    "execv": "lanza otros programas", "execl": "lanza otros programas",
    "execvp": "lanza otros programas", "execlp": "lanza otros programas",
    "remove": "borra archivos", "rmdir": "borra carpetas", "removedirs": "borra carpetas",
    "rmtree": "borra carpetas enteras", "rename": "mueve o renombra archivos",
    "replace": "mueve o renombra archivos", "move": "mueve archivos",
    "chmod": "cambia permisos de archivos",
}
MODULOS_DE_ARCHIVOS = {"os", "shutil"}

# Métodos que avisan sobre cualquier objeto (Path("x").unlink()).
METODOS = {"unlink": "borra archivos", "rmtree": "borra carpetas enteras"}

# Funciones con las que se suele esconder lo que hace el código.
OFUSCACION = {"eval", "exec", "compile", "__import__"}

_RUTA_ABSOLUTA = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")
_PISTAS = ("system32", "appdata", ".env", ".ssh", "program files", "proyecto-cain",
           "spotify_token")


def _revisar_literal(texto, avisos):
    bajo = texto.lower()
    if texto.startswith("\\\\"):
        # No se resuelve: realpath sobre una ruta UNC saldría a la red.
        avisos.add("usa rutas de red")
    elif _RUTA_ABSOLUTA.match(texto):
        try:
            verificar(texto)
        except Denegado as e:
            raise Denegado(f"el código generado nombra '{texto[:80]}', que {e}")
        except (ValueError, OSError):
            pass   # no es una ruta válida; igual queda el aviso de abajo
        avisos.add("usa rutas absolutas fuera de su carpeta")
    elif any(pista in bajo for pista in _PISTAS):
        avisos.add(f"menciona '{texto[:60]}'")


def revisar_python(codigo):
    """Avisos (lista ordenada) sobre un archivo .py. Lanza Denegado si nombra una ruta prohibida."""
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return ["no se pudo analizar el código (error de sintaxis)"]

    avisos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres = [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom):
            nombres = [nodo.module or ""]
        else:
            nombres = []
        for nombre in nombres:
            raiz = nombre.split(".")[0]
            if raiz in MODULOS:
                avisos.add(MODULOS[raiz])
        if isinstance(nodo, ast.ImportFrom) and nodo.module in MODULOS_DE_ARCHIVOS:
            for alias in nodo.names:
                if alias.name in LLAMADAS_MODULO:
                    avisos.add(LLAMADAS_MODULO[alias.name])

        if isinstance(nodo, ast.Call):
            funcion = nodo.func
            if isinstance(funcion, ast.Attribute):
                receptor = funcion.value
                if (isinstance(receptor, ast.Name) and receptor.id in MODULOS_DE_ARCHIVOS
                        and funcion.attr in LLAMADAS_MODULO):
                    avisos.add(LLAMADAS_MODULO[funcion.attr])
                elif funcion.attr in METODOS:
                    avisos.add(METODOS[funcion.attr])
            if isinstance(funcion, ast.Name) and funcion.id in OFUSCACION:
                avisos.add("ejecuta código construido en tiempo de ejecución")

        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            _revisar_literal(nodo.value, avisos)
    return sorted(avisos)


def revisar_proyecto(archivos):
    """Avisos de todos los .py de un plan {nombre: contenido}."""
    avisos = []
    for nombre, contenido in archivos.items():
        if nombre.lower().endswith(".py") and isinstance(contenido, str):
            for aviso in revisar_python(contenido):
                avisos.append(f"{nombre}: {aviso}")
    return avisos
