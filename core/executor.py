import subprocess
import os
import webbrowser
import threading
import socket
import time


# ─── Configuración ───────────────────────────────────────────────────────────

TIMEOUT_SEGUNDOS  = 30
CARPETA_PROYECTOS = "proyectos"

EXTENSIONES_WEB    = {".html", ".htm"}
EXTENSIONES_PYTHON = {".py"}


# ─── Utilidades ──────────────────────────────────────────────────────────────

def preparar_carpeta_proyecto(nombre_proyecto):
    """Crea la carpeta del proyecto con timestamp para evitar colisiones."""
    timestamp      = str(int(time.time()))[-4:]
    nombre_con_ts  = f"{nombre_proyecto}_{timestamp}"
    ruta           = os.path.join(CARPETA_PROYECTOS, nombre_con_ts)
    os.makedirs(ruta, exist_ok=True)
    return ruta


def detectar_tipo(nombre_archivo):
    """Detecta el tipo de archivo por extensión."""
    _, extension = os.path.splitext(nombre_archivo)
    if extension in EXTENSIONES_WEB:
        return "web"
    if extension in EXTENSIONES_PYTHON:
        return "python"
    return "otro"


def guardar_archivo_proyecto(ruta_proyecto, nombre_archivo, contenido):
    """Guarda un archivo dentro de la carpeta del proyecto."""
    ruta_completa = os.path.join(ruta_proyecto, nombre_archivo)
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
            timeout=TIMEOUT_SEGUNDOS,
            cwd=carpeta  # ← ejecuta desde la carpeta del proyecto
        )
        if resultado.returncode == 0:
            salida  = resultado.stdout.strip()
            mensaje = f"✅ Ejecutado correctamente.\n\n{salida}" if salida else "✅ Ejecutado correctamente."
            return True, mensaje, None
        else:
            error = resultado.stderr.strip()
            return False, f"⚠️ Error al ejecutar:\n\n{error}", error
    except subprocess.TimeoutExpired:
        return True, "✅ Ejecutado correctamente (proceso interactivo cerrado).", None
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


def ejecutar_proyecto(nombre_proyecto, archivos_contenido, tipo):
    """
    Flujo completo: crea carpeta, guarda archivos, ejecuta y retorna resultado.
    Retorna tupla (mensaje, url, info_error).
    """
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

        url     = abrir_servidor_web(ruta_proyecto)
        mensaje = (
            f"✅ Proyecto '{nombre_proyecto}' creado y ejecutado.\n"
            f"🌐 Abierto en: {url}\n"
            f"📁 Archivos en: {ruta_proyecto}"
        )
        return mensaje, url, None

    elif tipo == "python":
        archivo_principal = next(
            (r for r in rutas_guardadas if r.endswith(".py")), None
        )
        if not archivo_principal:
            return "❌ No encontré un archivo Python principal.", None, None

        exito, mensaje_ejecucion, error = ejecutar_python(archivo_principal)

        # Si generó una imagen, abrirla automáticamente
        ruta_imagen = os.path.join(ruta_proyecto, "output.png")
        if exito and os.path.exists(ruta_imagen):
            try:
                os.startfile(os.path.abspath(ruta_imagen))
                mensaje_ejecucion += f"\n🖼️ Imagen guardada: {ruta_imagen}"
            except Exception:
                mensaje_ejecucion += f"\n🖼️ Imagen guardada en: {ruta_imagen}"

        mensaje = (
            f"📁 Archivos en: {ruta_proyecto}\n\n"
            f"{mensaje_ejecucion}"
        )
        return mensaje, None, (archivo_principal, error) if not exito else None

    else:
        mensaje = (
            f"✅ Proyecto '{nombre_proyecto}' creado.\n"
            f"📁 Archivos en: {ruta_proyecto}\n"
            f"ℹ️ Este tipo de archivo no se ejecuta automáticamente."
        )
        return mensaje, None, None