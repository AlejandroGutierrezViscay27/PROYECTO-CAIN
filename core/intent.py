import re
 
 
# ─── Detección con LLMProvider ───────────────────────────────────────────────
 
def detectar_intencion_llm(mensaje_usuario, llm):
    """
    Clasifica la intención conversacional del mensaje.
    Retorna: 'historia' | 'reto' | 'tecnico' | 'conversacion'
    """
    prompt = """
Eres un sistema que clasifica la intención del usuario.
 
Solo puedes responder UNA de estas opciones:
- historia
- reto
- tecnico
- conversacion
 
Reglas:
- "historia": cuentos, relatos, narrativas, miedo, fantasía
- "reto": juegos, acertijos, desafíos, entretenimiento
- "tecnico": programación, código, software, dudas técnicas
- "conversacion": cualquier otro caso
 
Responde SOLO con una palabra.
"""
    respuesta = llm.chat(
        [{"role": "system", "content": prompt},
         {"role": "user",   "content": mensaje_usuario}],
        temperature=0
    )
    return respuesta.strip().lower()
 
 
def detectar_accion_llm(mensaje_usuario, llm):
    """
    Detecta si el usuario quiere operar sobre un archivo, ejecutar un proyecto
    o manipular la memoria de CAIN.
    Retorna: 'crear_archivo' | 'leer_archivo' | 'editar_archivo' |
             'borrar_archivo' | 'ejecutar_proyecto' |
             'memoria_recordar' | 'memoria_olvidar' | 'memoria_consultar' | 'ninguna'
    """
    prompt = """
Eres un sistema que detecta si el usuario quiere operar sobre un ARCHIVO,
EJECUTAR un proyecto o MANIPULAR la memoria del agente.
 
Responde SOLO una de estas opciones:
- crear_archivo
- leer_archivo
- editar_archivo
- borrar_archivo
- ejecutar_proyecto
- memoria_recordar
- memoria_olvidar
- memoria_consultar
- ninguna
 
REGLA PRINCIPAL:
La mayoría de mensajes son "ninguna". Solo detecta una acción específica si
el usuario lo menciona explícitamente.
 
crear_archivo — guardar contenido en un archivo de texto:
"guarda esto en un archivo", "crea un archivo con"
 
editar_archivo — modificar un archivo existente:
"añade al archivo", "edita el archivo X"
 
leer_archivo — ver contenido de un archivo:
"lee el archivo", "muéstrame el archivo"
 
borrar_archivo — eliminar un archivo:
"borra el archivo", "elimina el archivo"
 
ejecutar_proyecto — crear Y ejecutar código real:
"crea una página web", "haz una app", "construye un programa",
"crea un script que haga X", "quiero una web que"
 
memoria_recordar — guardar algo en la memoria explícitamente:
"recuerda que...", "guarda que...", "no olvides que...", "anota que..."
 
memoria_olvidar — borrar algo de la memoria:
"olvida que...", "borra de tu memoria...", "olvida mi historial",
"olvida todo lo que sabes de mí", "olvida mi nombre"
 
memoria_consultar — preguntar qué sabe CAIN del usuario:
"qué sabes de mí", "qué recuerdas de mí", "qué tienes guardado",
"muéstrame mi perfil", "qué información tienes"
 
ninguna — TODO lo demás: conversación normal, preguntas, historias, etc.
 
CLAVE:
"recuerda que prefiero Python"  → memoria_recordar
"olvida mi nombre"              → memoria_olvidar
"qué sabes de mí"               → memoria_consultar
"escríbeme un poema"            → ninguna
"crea una página web animada"   → ejecutar_proyecto
 
Responde solo una palabra.
"""
    respuesta = llm.chat(
        [{"role": "system", "content": prompt},
         {"role": "user",   "content": mensaje_usuario}],
        temperature=0
    )
    return respuesta.strip().lower()
 
 
def detectar_tipo_proyecto_llm(mensaje_usuario, llm):
    """
    Detecta qué tipo de proyecto quiere el usuario.
    Retorna: 'web' | 'python' | 'otro'
    """
    prompt = """
Eres un sistema que detecta qué tipo de proyecto quiere construir el usuario.
 
Responde SOLO una de estas opciones:
- web
- python
- otro
 
Reglas:
- "web": páginas web, HTML, CSS, JavaScript, interfaces visuales, dashboards
- "python": scripts, automatizaciones, algoritmos, análisis de datos, CLI tools
- "otro": cualquier otro caso
 
Responde solo una palabra.
"""
    respuesta = llm.chat(
        [{"role": "system", "content": prompt},
         {"role": "user",   "content": mensaje_usuario}],
        temperature=0
    )
    return respuesta.strip().lower()
 
 
def detectar_intereses_llm(mensaje_usuario, llm):
    """
    Extrae intereses del usuario desde el mensaje.
    Retorna lista de strings, o [] si no hay ninguno.
    """
    prompt = """
Eres un sistema que extrae intereses del usuario.
 
Detecta intereses solo si el usuario muestra gusto o intención de aprender.
Frases como: "me gusta", "me encanta", "quiero aprender", "me interesa".
 
Si no hay intereses claros, responde: ninguno
Si hay intereses, respóndelos separados por comas.
 
No expliques nada. Solo devuelve texto plano.
"""
    respuesta = llm.chat(
        [{"role": "system", "content": prompt},
         {"role": "user",   "content": mensaje_usuario}],
        temperature=0
    ).strip().lower()
 
    if respuesta == "ninguno":
        return []
    return [i.strip().capitalize() for i in respuesta.split(",") if i.strip()]
 
 
def es_misma_intencion_archivo(nombre_archivo, mensaje_usuario, llm):
    """
    Valida si la edición solicitada es coherente con el contenido del archivo.
    """
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
 
        prompt = f"""
Tienes un archivo con este contenido:
 
{contenido[:1000]}
 
El usuario pide: {mensaje_usuario}
 
¿La modificación es razonable para este archivo?
- SI es añadir, mejorar, cambiar estilo o extender → responde "si"
- SI es un tema completamente distinto → responde "no"
- SI tienes duda → responde "si"
 
Responde SOLO: si / no
"""
        respuesta = llm.chat(
            [{"role": "system", "content": prompt}],
            temperature=0
        )
        return respuesta.strip().lower() == "si"
    except Exception:
        return True  # fallback seguro
 
 
# ─── Detección sin LLM (regex) ───────────────────────────────────────────────
 
def detectar_nombre(mensaje):
    """Detecta si el usuario menciona su nombre."""
    mensaje = mensaje.lower().strip()
    match = re.match(r"^(me llamo)\s+([a-zA-Záéíóúñ\s]+)$", mensaje)
    if match:
        return match.group(2).strip().capitalize()
    match = re.match(r"^(soy)\s+([a-zA-Záéíóúñ\s]+)$", mensaje)
    if match:
        return match.group(2).strip().capitalize()
    return None
 
 
def detectar_rol(mensaje):
    """Detecta si el usuario se identifica como creador de CAIN."""
    if "soy tu creador" in mensaje.lower():
        return "creador"
    return None
 
 
def extraer_contenido_memoria(mensaje_usuario, accion, llm):
    """
    Extrae el contenido relevante de un comando de memoria.
 
    Para memoria_recordar: extrae qué debe recordar.
    Para memoria_olvidar:  extrae qué debe olvidar.
 
    Retorna un string con el contenido extraído.
    """
    if accion == "memoria_recordar":
        prompt = f"""
El usuario dijo: "{mensaje_usuario}"
 
Extrae SOLO lo que quiere que recuerdes, sin el verbo introductorio.
 
Ejemplos:
"recuerda que prefiero código comentado" → "prefiero código comentado"
"no olvides que trabajo con Python 3.11" → "trabajo con Python 3.11"
"anota que mi framework favorito es FastAPI" → "mi framework favorito es fastapi"
 
Responde solo el contenido extraído, en minúsculas, sin puntuación final.
"""
    elif accion == "memoria_olvidar":
        prompt = f"""
El usuario dijo: "{mensaje_usuario}"
 
Extrae SOLO lo que quiere que olvides.
 
Ejemplos:
"olvida que me llamo Alejandro" → "nombre"
"olvida mis intereses" → "intereses"
"olvida todo lo que sabes de mí" → "todo"
"olvida mi historial" → "historial"
"olvida que prefiero Python" → "prefiero python"
 
Palabras clave especiales — responde exactamente:
- Si quiere olvidar el nombre → "nombre"
- Si quiere olvidar intereses → "intereses"
- Si quiere olvidar el historial/conversaciones → "historial"
- Si quiere olvidar todo → "todo"
- Si quiere olvidar una nota específica → el fragmento de la nota
 
Responde solo el contenido extraído, en minúsculas.
"""
    else:
        return ""
 
    respuesta = llm.chat(
        [{"role": "system", "content": prompt}],
        temperature=0
    )
    return respuesta.strip().lower()