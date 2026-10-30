"""Fase 10.3: el enrutador real (sin ejecutar nada) con frases sueltas y conversaciones."""
import os, sys
from collections import deque
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, RAIZ); os.chdir(RAIZ)
from dotenv import load_dotenv
load_dotenv(os.path.join(RAIZ, ".env"))
from core.agent import Cain, MAX_TURNOS_CONTEXTO
from core.tool_schemas import TOOLS, TOOLS_SO, TOOLS_NAVEGADOR, TOOLS_SPOTIFY, PROMPT_ENRUTADOR
from llm.fabrica import crear_llms
from llm.registro import RegistroUso

enrutador = crear_llms(RegistroUso())["enrutador"]
herramientas = TOOLS + TOOLS_SO + TOOLS_NAVEGADOR + TOOLS_SPOTIFY

def nuevo():
    c = Cain.__new__(Cain)
    c.turnos_recientes = deque(maxlen=MAX_TURNOS_CONTEXTO)
    return c

def decidir(c, mensaje):
    mensajes = [{"role": "system", "content": PROMPT_ENRUTADOR}]
    contexto = c._contexto_reciente()
    if contexto:
        mensajes.append({"role": "system", "content": contexto})
    mensajes.append({"role": "user", "content": mensaje})
    r = enrutador.chat_with_tools(mensajes, tools=herramientas, temperature=0.2).get("tool_call")
    nombre, args = (r["name"], r["arguments"]) if r else (None, {})
    c._anotar_turno(mensaje, nombre, args)
    return nombre, args

def coincide(nombre, args, esperado):
    if esperado is None:
        return nombre is None
    herramienta, *condiciones = esperado
    if nombre != herramienta:
        return False
    return all(cond(args) for cond in condiciones)

def accion(valor):
    return lambda a: a.get("accion") == valor

def numero(valor):
    return lambda a: a.get("numero") == valor

con_consulta = lambda a: bool(str(a.get("consulta", "")).strip())
sin_nada = lambda a: (not str(a.get("consulta", "") or "").strip() and a.get("numero") is None
                      and not a.get("canal") and a.get("modo") in (None, "recomendado"))

def canal(texto):
    return lambda a: texto in str(a.get("canal", "")).lower()

def poner(valor):
    return lambda a: (a.get("poner") is True) == valor

def modo(valor):
    return lambda a: a.get("modo") == valor

SUELTAS = [
    ("busca vídeos de gatos en YouTube", ("youtube_buscar", con_consulta)),
    ("¿qué hay en youtube de recetas de arepas?", ("youtube_buscar", con_consulta)),
    ("pon en youtube el tráiler de Dune", ("youtube_reproducir", con_consulta)),
    ("ponme un video de cómo hacer pan", ("youtube_reproducir", con_consulta)),
    ("pon algo recomendado en youtube", ("youtube_reproducir", sin_nada)),
    ("pon el último video de Andres Garza", ("youtube_canal", canal("garza"), poner(True))),
    ("ponme lo más nuevo de Dot CSV en youtube", ("youtube_canal", canal("dot"), poner(True))),
    ("¿qué ha subido Andrés Garza últimamente?", ("youtube_canal", canal("garza"), poner(False))),
    ("los últimos videos de Platzi", ("youtube_canal", canal("platzi"), poner(False))),
    ("abre youtube", ("sistema_abrir_url",)),
    ("abre google", ("sistema_abrir_url",)),
    ("abre el navegador", ("sistema_abrir_app",)),
    ("¿qué pestañas tengo abiertas?", ("navegador_pestanas", accion("listar"))),
    ("cierra la pestaña 2", ("navegador_pestanas", accion("cerrar"), numero(2))),
    ("cámbiate a la pestaña 1", ("navegador_pestanas", accion("cambiar"), numero(1))),
    ("pausa el video", ("youtube_control", accion("pausar"))),
    ("salta este video", ("youtube_control", accion("siguiente"))),
    ("pon bohemian rhapsody", ("spotify_reproducir",)),
    ("pausa la música", ("spotify_control", accion("pausar"))),
    ("¿qué tengo abierto en el PC?", ("sistema_ventanas",)),
    ("cuéntame un chiste", None),
    ("¿cómo se busca en youtube desde python?", None),
]

CONVERSACIONES = [
    [("busca documentales de agujeros negros en youtube", ("youtube_buscar", con_consulta)),
     ("pon el 2", ("youtube_reproducir", numero(2))),
     ("pausa", ("youtube_control", accion("pausar"))),
     ("sigue", ("youtube_control", accion("reanudar"))),
     ("el siguiente", ("youtube_control", accion("siguiente"))),
     ("súbele", ("sistema_volumen", accion("subir")))],
    [("pon un video de lofi en youtube", ("youtube_reproducir", con_consulta)),
     ("ahora pon música de Bad Bunny", ("spotify_reproducir",)),
     ("pausa", ("spotify_control", accion("pausar")))],
    [("pon mi lista del gym", ("spotify_reproducir",)),
     ("busca en youtube el video de esa canción", ("youtube_buscar", con_consulta)),
     ("el primero", ("youtube_reproducir", numero(1))),
     ("pausa el video", ("youtube_control", accion("pausar")))],
    [("¿qué pestañas tengo?", ("navegador_pestanas", accion("listar"))),
     ("cierra la 3", ("navegador_pestanas", accion("cerrar"), numero(3))),
     ("y cámbiate a la primera", ("navegador_pestanas", accion("cambiar"), numero(1))),
     ("gracias, ¿qué tal tu día?", None)],
    # Lo que falló en la prueba real del 28/10.
    [("busca videos de finanzas de Andres Garza", ("youtube_buscar", con_consulta)),
     ("pon el 2", ("youtube_reproducir", numero(2))),
     ("ponme otro video similar de él", ("youtube_reproducir", modo("del_mismo_creador"))),
     ("otro de él", ("youtube_reproducir", modo("del_mismo_creador"))),
     ("ahora algo parecido a este pero de otro canal", ("youtube_reproducir", modo("parecido_de_otros"))),
     ("pon el último video de andres garza", ("youtube_canal", canal("garza"), poner(True))),
     ("pausa", ("youtube_control", accion("pausar")))],
    [("ponme un video de finanzas de Andres Garza", ("youtube_reproducir", con_consulta)),
     ("pon uno parecido", ("youtube_reproducir", modo("parecido_de_otros"))),
     ("¿qué ha subido él últimamente?", ("youtube_canal", canal("garza"), poner(False)))],
]

bien = total = 0
def probar(c, mensaje, esperado):
    global bien, total
    nombre, args = decidir(c, mensaje)
    ok = coincide(nombre, args, esperado)
    bien += ok; total += 1
    print(f"{'OK ' if ok else 'MAL'} {mensaje!r:55} -> {nombre}({args})")

print("== Frases sueltas ==")
for mensaje, esperado in SUELTAS:
    probar(nuevo(), mensaje, esperado)
for i, conversacion in enumerate(CONVERSACIONES, 1):
    print(f"== Conversación {i} ==")
    c = nuevo()
    for mensaje, esperado in conversacion:
        probar(c, mensaje, esperado)
print(f"\n{bien} de {total}")
