# Ningún test puede tocar data/ real: todas las rutas de memoria apuntan a
# una carpeta temporal. Un test que olvide parchear limpiar_historial_completo()
# o un guardar_*() borraría o pisaría la memoria de verdad del usuario.
import os
import tempfile

from core import memory

_DATA_PRUEBAS = tempfile.mkdtemp(prefix="cain_tests_")

for _nombre in ("ARCHIVO_MEMORIA", "ARCHIVO_USUARIO", "ARCHIVO_RESUMEN", "ARCHIVO_LARGA"):
    setattr(memory, _nombre, os.path.join(_DATA_PRUEBAS, os.path.basename(getattr(memory, _nombre))))

from llm import registro

registro.ARCHIVO_USO = os.path.join(_DATA_PRUEBAS, "uso_llm.json")

# Fase 10: la auditoría y las zonas de trabajo de CAIN (espacio/ y proyectos/)
# tampoco pueden ser las reales.
from core.arnes import auditoria, reglas

auditoria.ARCHIVO_AUDITORIA = os.path.join(_DATA_PRUEBAS, "auditoria.jsonl")
reglas.CARPETA_ESPACIO      = os.path.join(_DATA_PRUEBAS, "espacio")
reglas.CARPETA_PROYECTOS    = os.path.join(_DATA_PRUEBAS, "proyectos")

# Fase 10.4: el token de Spotify (equivale a acceso a la cuenta).
from so.conectores import spotify as conector_spotify

conector_spotify.ARCHIVO_TOKEN = os.path.join(_DATA_PRUEBAS, "spotify_token.json")


def mismo_llm_para_todos(clase):
    """Sustituto de crear_llms(): una sola instancia de prueba para todos los roles."""
    from llm.fabrica import ROLES

    def crear(registro=None):
        llm = clase()
        return {rol: llm for rol in ROLES}
    return crear
