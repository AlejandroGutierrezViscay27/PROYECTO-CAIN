import subprocess
import os
import re
import webbrowser
import threading
import socket
import time

from core import prompts
from core.arnes import reglas, revision_codigo
from core.arnes.rutas import Denegado, resolver


# ─── Configuración ───────────────────────────────────────────────────────────

# La carpeta de proyectos es reglas.CARPETA_PROYECTOS: el arnés la conoce como
# zona propia de CAIN (excepción dentro del repo protegido).
TIMEOUT_SEGUNDOS   = 30
MAX_ARCHIVOS       = 20
MAX_BYTES_PROYECTO = 2_000_000

EXTENSIONES_WEB    = {".html", ".htm"}
EXTENSIONES_PYTHON = {".py"}


# ─── Utilidades ──────────────────────────────────────────────────────────────

def nombre_seguro(nombre):
    """Nombre de carpeta a partir del que inventa el LLM: solo [a-z0-9_-]."""
    limpio = re.sub(r"[^a-z0-9_-]+", "_", str(nombre).lower()).strip("_-")[:40]
    return limpio or "proyecto_cain"


def preparar_carpeta_proyecto(nombre_proyecto):
    """Crea la carpeta del proyecto con timestamp para evitar colisiones."""
    timestamp      = str(int(time.time()))[-4:]
    nombre_con_ts  = f"{nombre_seguro(nombre_proyecto)}_{timestamp}"
    ruta           = os.path.join(reglas.CARPETA_PROYECTOS, nombre_con_ts)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def validar_archivos(archivos):
    """
    Revisa el plan del LLM antes de escribir nada: cada archivo debe quedar
    dentro de la carpeta del proyecto, con una extensión permitida, y el
    total dentro de los límites. Lanza Denegado con el motivo.
    """
    if len(archivos) > MAX_ARCHIVOS:
        raise Denegado(f"el proyecto tiene más de {MAX_ARCHIVOS} archivos")
    total = 0
    carpeta_prueba = os.path.join(reglas.CARPETA_PROYECTOS, "_validacion")
    for nombre, contenido in archivos.items():
        if not isinstance(contenido, str):
            raise Denegado(f"el contenido de '{nombre}' no es texto")
        total += len(contenido.encode("utf-8"))
        try:
            resolver(nombre, carpeta_prueba, escritura=True)
        except Denegado as e:
            raise Denegado(f"el archivo '{nombre}' del proyecto: {e}")
    if total > MAX_BYTES_PROYECTO:
        raise Denegado("el proyecto es demasiado grande")


def entorno_minimo():
    """
    Entorno para el código generado: solo lo que Python necesita para correr.
    Ninguna clave del .env (OPENAI_API_KEY, CAIN_TOKEN...) llega al hijo.
    """
    entorno = {k: v for k, v in os.environ.items() if k.upper() in reglas.ENTORNO_PERMITIDO}
    entorno["PYTHONIOENCODING"] = "utf-8"   # el hijo escribe stdout/stderr en UTF-8
    return entorno


def detectar_tipo(nombre_archivo):
    """Detecta el tipo de archivo por extensión."""
    _, extension = os.path.splitext(nombre_archivo)
    if extension in EXTENSIONES_WEB:
        return "web"
    if extension in EXTENSIONES_PYTHON:
        return "python"
    return "otro"


def carpeta_de_proyecto(nombre):
    """
    Ruta absoluta de un proyecto, o None si no existe o el nombre intenta
    salirse de la carpeta de proyectos ("..", rutas absolutas...).
    """
    base = os.path.realpath(reglas.CARPETA_PROYECTOS)
    ruta = os.path.realpath(os.path.join(base, nombre))
    if os.path.dirname(ruta) != base or not os.path.isdir(ruta):
        return None
    return ruta


def archivo_de_proyecto(nombre, ruta_relativa):
    """Ruta absoluta de un archivo dentro de un proyecto, o None (igual que arriba)."""
    carpeta = carpeta_de_proyecto(nombre)
    if not carpeta:
        return None
    ruta = os.path.realpath(os.path.join(carpeta, ruta_relativa or "index.html"))
    if os.path.isdir(ruta):
        ruta = os.path.join(ruta, "index.html")
    if os.path.commonpath([carpeta, ruta]) != carpeta or not os.path.isfile(ruta):
        return None
    return ruta


def html_principal(archivos):
    """El HTML con el que se abre un proyecto web: index.html si existe."""
    htmls = sorted(a for a in archivos if os.path.splitext(a)[1] in EXTENSIONES_WEB)
    if "index.html" in htmls:
        return "index.html"
    return htmls[0] if htmls else None


def guardar_archivo_proyecto(ruta_proyecto, nombre_archivo, contenido):
    """Guarda un archivo dentro de la carpeta del proyecto (o Denegado si se sale)."""
    ruta_completa = resolver(nombre_archivo, ruta_proyecto, escritura=True)
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta_completa


# ─── Puerto dinámico ─────────────────────────────────────────────────────────

def encontrar_puerto_libre(desde=8080, hasta=8100):
    """Busca el primer puerto disponible en el rango dado."""
    for puerto in range(desde, hasta):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", puerto)) != 0:
                return puerto
    return 8080  # fallback


# ─── Ejecución ───────────────────────────────────────────────────────────────

def ejecutar_python(ruta_archivo):
    """
    Ejecuta un archivo Python desde su propia carpeta (cwd).
    Retorna tupla (exito, mensaje, error).
    """
    try:
        carpeta = os.path.dirname(os.path.abspath(ruta_archivo))
        resultado = subprocess.run(
            ["python", os.path.basename(ruta_archivo)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_SEGUNDOS,
            cwd=carpeta,  # ← ejecuta desde la carpeta del proyecto
            env=entorno_minimo(),
        )
        if resultado.returncode == 0:
            salida  = resultado.stdout.strip()
            mensaje = f"✅ Ejecutado correctamente.\n\n{salida}" if salida else "✅ Ejecutado correctamente."
            return True, mensaje, None
        else:
            error = resultado.stderr.strip()
            return False, f"⚠️ Error al ejecutar:\n\n{error}", error
    except subprocess.TimeoutExpired:
        # Lo normal en un programa con ventana (pygame, tkinter): no es un error
        # que corregir, pero tampoco un "ejecutado correctamente".
        return True, f"⏱️ El programa siguió corriendo más de {TIMEOUT_SEGUNDOS} s y lo detuve.", None
    except Exception as e:
        return False, f"❌ Error al ejecutar: {str(e)}", str(e)


def abrir_servidor_web(ruta_proyecto):
    """
    Inicia un servidor HTTP local en un puerto libre
    y abre el navegador automáticamente.
    """
    puerto = encontrar_puerto_libre()

    def iniciar_servidor():
        subprocess.run(
            ["python", "-m", "http.server", str(puerto)],
            cwd=ruta_proyecto,
            env=entorno_minimo(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    hilo = threading.Thread(target=iniciar_servidor, daemon=True)
    hilo.start()

    time.sleep(1)  # pausa para que el servidor arranque

    url = f"http://localhost:{puerto}"
    webbrowser.open(url)
    return url


# ─── Flujo principal ─────────────────────────────────────────────────────────

def mostrar_plan(archivos, comando_ejecucion):
    archivos_texto = "\n".join([f"      📄 {a}" for a in archivos])
    return (
        f"\n📋 Plan de ejecución:\n\n"
        f"   Archivos a crear:\n{archivos_texto}\n\n"
        f"   Comando a ejecutar:\n"
        f"      📟 {comando_ejecucion}\n\n"
        f"¿Procedo? (s/n): "
    )


def describir_comando(tipo, archivos, abrir_en_pc=True):
    """Genera una descripción legible del comando que se va a ejecutar."""
    if tipo == "web":
        if not abrir_en_pc:
            return "servido por CAIN en /proyectos/ (se abre en tu dispositivo)"
        return "python -m http.server (puerto libre automático)"
    elif tipo == "python":
        py_file = next((a for a in archivos if a.endswith(".py")), archivos[0])
        return f"python {py_file}"
    return "abrir archivo directamente"


def _avisos_confirmados(advertencias, ruta_archivo):
    """Avisos de revisar_proyecto ("archivo: aviso") que son de ese archivo."""
    nombre = os.path.basename(ruta_archivo)
    avisos = set()
    for advertencia in advertencias:
        archivo, _, aviso = advertencia.partition(": ")
        if os.path.basename(archivo) == nombre:
            avisos.add(aviso)
    return avisos


def corregir_y_reintentar(llm, ruta_archivo, error, mensaje_original, intentos=2,
                          advertencias_confirmadas=()):
    """
    Intenta corregir el código automáticamente cuando hay un error.
    Máximo 2 intentos para no entrar en loop infinito.

    El código corregido no lo ve el usuario: si hace algo que el original
    confirmado no hacía (avisos nuevos de la revisión) o nombra una ruta
    prohibida, no se ejecuta.
    """
    permitidos = _avisos_confirmados(advertencias_confirmadas, ruta_archivo)
    for intento in range(1, intentos + 1):
        print(f"[DEBUG] Error en el proyecto -> corrigiendo (intento {intento}/{intentos})")

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                codigo_actual = f.read()
        except Exception:
            return mensaje_original

        codigo_corregido = prompts.generar_correccion_codigo(llm, codigo_actual, error)

        try:
            nuevos = set(revision_codigo.revisar_python(codigo_corregido)) - permitidos
        except Denegado as e:
            return f"{mensaje_original}\n\n🛡️ No ejecuté la corrección automática: {e}."
        if nuevos:
            return (
                f"{mensaje_original}\n\n🛡️ No ejecuté la corrección automática: hace cosas "
                f"que no confirmaste ({'; '.join(sorted(nuevos))}). Pídemelo de nuevo si la quieres."
            )

        try:
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                f.write(codigo_corregido)
        except Exception:
            return mensaje_original

        exito, nuevo_mensaje, nuevo_error = ejecutar_python(ruta_archivo)

        if exito:
            return (
                f"🔧 Detecté y corregí un error automáticamente.\n\n"
                f"📁 Archivo: {ruta_archivo}\n\n"
                f"{nuevo_mensaje}"
            )
        else:
            error = nuevo_error

    return (
        f"{mensaje_original}\n\n"
        f"⚠️ Intenté corregirlo {intentos} veces pero el error persiste.\n"
        f"Puedes pedirme que lo intente de nuevo con más detalles."
    )


def para_mostrar(ruta):
    """Ruta relativa a CAIN (proyectos/...), para los mensajes."""
    return os.path.relpath(ruta, os.path.dirname(reglas.CARPETA_PROYECTOS))


def url_en_cain(ruta_proyecto, archivo):
    """URL relativa con la que el servidor web de CAIN sirve un archivo del proyecto."""
    return f"/proyectos/{os.path.basename(ruta_proyecto)}/{archivo}"


def ejecutar_proyecto(nombre_proyecto, archivos_contenido, tipo, abrir_en_pc=True):
    """
    Flujo completo: crea carpeta, guarda archivos, ejecuta y retorna resultado.
    Retorna tupla (mensaje, url, info_error).

    abrir_en_pc: modo terminal — levanta un http.server y abre el navegador
    (o la imagen) en esta máquina. Con False (modo web) no abre nada aquí:
    la url es relativa al servidor de CAIN y la abre el dispositivo que
    pidió el proyecto, sea el PC o el móvil.
    """
    validar_archivos(archivos_contenido)   # defensa en profundidad: ya se validó al confirmar
    ruta_proyecto = preparar_carpeta_proyecto(nombre_proyecto)

    rutas_guardadas = []
    for nombre_archivo, contenido in archivos_contenido.items():
        ruta = guardar_archivo_proyecto(ruta_proyecto, nombre_archivo, contenido)
        rutas_guardadas.append(ruta)

    if tipo == "web":
        archivo_principal = next(
            (n for n in archivos_contenido if n.endswith(".html")), None
        )
        if not archivo_principal:
            return "❌ No encontré un archivo HTML principal.", None, None

        if abrir_en_pc:
            url     = abrir_servidor_web(ruta_proyecto)
            mensaje = (
                f"✅ Proyecto '{nombre_proyecto}' creado y ejecutado.\n"
                f"🌐 Abierto en: {url}\n"
                f"📁 Archivos en: {para_mostrar(ruta_proyecto)}"
            )
        else:
            url     = url_en_cain(ruta_proyecto, archivo_principal)
            mensaje = (
                f"✅ Proyecto '{nombre_proyecto}' creado.\n"
                f"📁 Archivos en: {para_mostrar(ruta_proyecto)}"
            )
        return mensaje, url, None

    elif tipo == "python":
        archivo_principal = next(
            (r for r in rutas_guardadas if r.endswith(".py")), None
        )
        if not archivo_principal:
            return "❌ No encontré un archivo Python principal.", None, None

        exito, mensaje_ejecucion, error = ejecutar_python(archivo_principal)

        # Si generó una imagen, abrirla automáticamente (en el PC, o en el
        # dispositivo que lo pidió si es el modo web)
        url         = None
        ruta_imagen = os.path.join(ruta_proyecto, "output.png")
        if exito and os.path.exists(ruta_imagen):
            if not abrir_en_pc:
                url = url_en_cain(ruta_proyecto, "output.png")
                mensaje_ejecucion += f"\n🖼️ Imagen guardada: {para_mostrar(ruta_imagen)}"
            else:
                try:
                    os.startfile(os.path.abspath(ruta_imagen))
                    mensaje_ejecucion += f"\n🖼️ Imagen guardada: {para_mostrar(ruta_imagen)}"
                except Exception:
                    mensaje_ejecucion += f"\n🖼️ Imagen guardada en: {para_mostrar(ruta_imagen)}"

        mensaje = (
            f"📁 Archivos en: {para_mostrar(ruta_proyecto)}\n\n"
            f"{mensaje_ejecucion}"
        )
        return mensaje, url, (archivo_principal, error) if not exito else None

    else:
        mensaje = (
            f"✅ Proyecto '{nombre_proyecto}' creado.\n"
            f"📁 Archivos en: {para_mostrar(ruta_proyecto)}\n"
            f"ℹ️ Este tipo de archivo no se ejecuta automáticamente."
        )
        return mensaje, None, None