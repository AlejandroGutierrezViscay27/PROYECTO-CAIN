# Ningún test puede tocar data/ real: todas las rutas de memoria apuntan a
# una carpeta temporal. Un test que olvide parchear limpiar_historial_completo()
# o un guardar_*() borraría o pisaría la memoria de verdad del usuario.
import os
import tempfile

from core import memory

_DATA_PRUEBAS = tempfile.mkdtemp(prefix="cain_tests_")

for _nombre in ("ARCHIVO_MEMORIA", "ARCHIVO_USUARIO", "ARCHIVO_RESUMEN", "ARCHIVO_LARGA"):
    setattr(memory, _nombre, os.path.join(_DATA_PRUEBAS, os.path.basename(getattr(memory, _nombre))))
