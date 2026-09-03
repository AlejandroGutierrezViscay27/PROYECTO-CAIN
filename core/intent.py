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
 
 
