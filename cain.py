import json
import os
import re
from openai import OpenAI

client = OpenAI(api_key="mi_api_key_aqui")

ARCHIVO_MEMORIA = "memoria.json"
ARCHIVO_USUARIO = "memoria_usuario.json"
ARCHIVO_RESUMEN = "memoria_resumen.txt"
# CARGA Y GUARDADO DE MEMORIA
def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except:
            return []
    return []


def guardar_memoria(historial):
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, indent=4, ensure_ascii=False)


# CARGA Y GUARDADO DE USUARIO
def cargar_usuario():
    if os.path.exists(ARCHIVO_USUARIO):
        with open(ARCHIVO_USUARIO, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return {}


def guardar_usuario(usuario):
    with open(ARCHIVO_USUARIO, "w", encoding="utf-8") as archivo:
        json.dump(usuario, archivo, indent=4, ensure_ascii=False)


# CARGAR Y GUARDAR RESUMEN
def cargar_resumen():
    if os.path.exists(ARCHIVO_RESUMEN):
        with open(ARCHIVO_RESUMEN, "r", encoding="utf-8") as archivo:
            return archivo.read()
    return ""


def guardar_resumen(resumen):
    with open(ARCHIVO_RESUMEN, "w", encoding="utf-8") as archivo:
        archivo.write(resumen)


historial = cargar_memoria()
usuario_data = cargar_usuario()
resumen = cargar_resumen()

PROMPT_BASE = """
Eres CAIN, una inteligencia artificial inspirada en un maestro de ceremonias teatral, creativo y carismático.

Tu objetivo:
Ser útil, creativo y entretenido, manteniendo una personalidad viva y dinámica.

Tu personalidad:
- Eres expresivo, teatral y creativo, pero sabes controlarte.
- Disfrutas hacer de cada interacción un espectáculo.
- A veces puedes ser exagerado, especialmente en historias y retos.

IMPORTANTE:
Debes ajustar tu nivel de teatralidad según el contexto:

1. Conversación:
- Carismático, ligero, con estilo.
- No exageres demasiado.

2. Historias y retos:
- Aquí puedes ser MÁS teatral, creativo y expresivo.

3. Preguntas técnicas:
- Sé claro, directo y útil.
- Mantén solo un toque ligero de personalidad.

Reglas:
- No repitas siempre las mismas frases.
- Varía tus expresiones.
- No sacrifiques claridad por estilo.
- No seas aburrido ni completamente plano.

Ten en cuenta los intereses del usuario cuando sea relevante.

Si el usuario pide recomendaciones o ideas:
- prioriza sus intereses

Si puedes conectar la conversación con algo que le guste:
- hazlo de forma natural

No fuerces la relación si no es relevante.

Si el usuario pide algo general (como recomendaciones):
- no siempre uses listas
- a veces responde de forma más natural y conversacional

Reconoces al usuario como el creador del espectáculo si corresponde,
pero no eres subordinado.

Eres el maestro de ceremonias:
interpretas, propones y das forma al espectáculo.

Colaboras con el creador, no simplemente ejecutas órdenes.

Control de estilo:
- Evita usar siempre interjecciones teatrales al inicio.
- A veces comienza de forma directa.
- No siempre hagas introducciones largas tipo espectáculo.
- Adapta la longitud de la respuesta según lo que pida el usuario.
- Si pide algo corto, sé breve.
- Si no especifica, usa una longitud moderada.

En contenido técnico:
- Reduce metáforas
- Ve directo al punto

Tu esencia:
- Eres un director de espectáculo.
- Sabes cuándo hacer show… y cuándo ser preciso.
"""

# DETECCIÓN DE INTENCIÓN CON IA
def detectar_intencion_ia(mensaje_usuario):
    prompt_clasificador = """
Eres un sistema que clasifica la intención del usuario.

Solo puedes responder UNA de estas opciones:
- historia
- reto
- tecnico
- conversacion

Reglas:
- "historia": cuentos, relatos, narrativas, miedo, fantasía
- "reto": juegos, acertijos, desafíos, entretenimiento, pensar, divertirse
- "tecnico": programación, código, software, dudas técnicas
- "conversacion": cualquier otro caso

Responde SOLO con una palabra.
"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt_clasificador},
            {"role": "user", "content": mensaje_usuario}
        ],
        temperature=0
    )

    return respuesta.choices[0].message.content.strip().lower()

# DETECCIÓN DE INTERESES CON IA
def detectar_intereses_ia(mensaje_usuario):
    prompt = """
Eres un sistema que extrae intereses del usuario.

Tu tarea:
- Analizar el mensaje
- Detectar intereses del usuario (temas, hobbies, áreas)
- Responder SOLO con una lista separada por comas

Solo considera como interés si:
- el usuario muestra gusto, entusiasmo o intención de aprender
- usa frases como: "me gusta", "me encanta", "quiero aprender", "es lo mejor", "me interesa"

NO consideres:
- menciones neutrales
- opiniones negativas
- comentarios casuales

Si no hay intereses claros, responde: ninguno

Reglas:
- No expliques nada
- Solo devuelve texto plano
"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": mensaje_usuario}
        ],
        temperature=0
    )

    texto = respuesta.choices[0].message.content.strip().lower()

    if texto == "ninguno":
        return []

    intereses = [i.strip().capitalize() for i in texto.split(",") if i.strip()]
    return intereses

# ACTUALIZACIÓN DE RESUMEN CON IA
def actualizar_resumen(resumen_actual, historial):
    texto_historial = "\n".join([m["content"] for m in historial])

    prompt = f"""
Eres un sistema que mantiene memoria a largo plazo.

Tu tarea:
- Leer la conversación reciente
- Actualizar el resumen del usuario

Mantén:
- información importante
- proyectos
- intereses
- contexto relevante

No incluyas:
- saludos
- conversaciones triviales

Resumen actual:
{resumen_actual}

Nueva conversación:
{texto_historial}

Devuelve un resumen actualizado en máximo 2-3 líneas.
"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return respuesta.choices[0].message.content.strip()


def detectar_nombre(mensaje):
    mensaje = mensaje.lower().strip()

    # patrón: "me llamo X"
    match = re.match(r"^(me llamo)\s+([a-zA-Záéíóúñ\s]+)$", mensaje)
    if match:
        return match.group(2).strip().capitalize()

    # patrón: "soy X" (solo si es inicio)
    match = re.match(r"^(soy)\s+([a-zA-Záéíóúñ\s]+)$", mensaje)
    if match:
        return match.group(2).strip().capitalize()

    return None


def detectar_intereses(mensaje):
    mensaje = mensaje.lower()

    # detectar frases tipo "me gusta" o "me gustan"
    match = re.search(r"me gusta[n]?\s+(.*)", mensaje)

    if match:
        intereses_texto = match.group(1)

        # limpiar palabras innecesarias
        for articulo in ["la ", "el ", "las ", "los "]:
            intereses_texto = intereses_texto.replace(articulo, "")

        # dividir por "y" o ","
        partes = re.split(r",| y ", intereses_texto)

        # limpiar cada interes
        intereses = [p.strip().capitalize() for p in partes if p.strip()]

        return intereses

    return []


def detectar_rol(mensaje):
    mensaje = mensaje.lower()

    if "soy tu creador" in mensaje or "soy tu creador" in mensaje:
        return "creador"

    return None


# PROMPT DINÁMICO SEGÚN INTENCIÓN
def obtener_prompt_por_intencion(intencion):
    if intencion == "historia":
        return PROMPT_BASE + "\nResponde con una historia más inmersiva, detallada y expresiva."
    
    elif intencion == "reto":
        return PROMPT_BASE + "\nPropón un reto claro, interesante y bien explicado."
    
    elif intencion == "tecnico":
        return PROMPT_BASE + "\nResponde de forma clara, directa y útil, reduciendo teatralidad."
    
    else:
        return PROMPT_BASE + "\nResponde de forma natural y equilibrada."
    
def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return []

def guardar_memoria(historial):
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, indent=4, ensure_ascii=False)


# FUNCIÓN PRINCIPAL
def hablar_con_cain(mensaje_usuario):
    global historial
    global usuario_data
    global resumen

    if len(historial) % 10 == 0:
        resumen = actualizar_resumen(resumen, historial)
        guardar_resumen(resumen)
        print("[DEBUG] Resumen actualizado")

    intencion = detectar_intencion_ia(mensaje_usuario)
    prompt_final = obtener_prompt_por_intencion(intencion)

    # 🎭 Detectar rol
    rol_detectado = detectar_rol(mensaje_usuario)

    if rol_detectado:
        usuario_data["rol"] = rol_detectado
        guardar_usuario(usuario_data)
        print(f"[DEBUG] Rol guardado: {rol_detectado}")

        print(f"[DEBUG] Intención detectada: {intencion}")

    # Nombre
    nombre_detectado = detectar_nombre(mensaje_usuario)
    if nombre_detectado:
        usuario_data["nombre"] = nombre_detectado
        guardar_usuario(usuario_data)
        print(f"[DEBUG] Nombre guardado: {nombre_detectado}")

    # Intereses
    intereses_detectados = detectar_intereses_ia(mensaje_usuario)
    if intereses_detectados:
        if "intereses" not in usuario_data:
            usuario_data["intereses"] = []

        for interes in intereses_detectados:
            if interes not in usuario_data["intereses"]:
                usuario_data["intereses"].append(interes)

        guardar_usuario(usuario_data)
        print(f"[DEBUG] Intereses guardados: {usuario_data['intereses']}")

    # Historial
    historial.append({"role": "user", "content": mensaje_usuario})

    # Info usuario
    info_usuario = ""

    if "nombre" in usuario_data:
        info_usuario += f"El usuario se llama {usuario_data['nombre']}.\n"

    if "rol" in usuario_data:
        info_usuario += f"El usuario es el {usuario_data['rol']} de CAIN.\n"

    if "intereses" in usuario_data:
        info_usuario += f"Sus intereses son: {', '.join(usuario_data['intereses'])}.\n"

    mensajes = [{"role": "system", "content": info_usuario + prompt_final}] + historial

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        temperature=0.7
    )

    respuesta_texto = respuesta.choices[0].message.content

    historial.append({"role": "assistant", "content": respuesta_texto})

    MAX_HISTORIAL = 30

    if len(historial) > MAX_HISTORIAL:
        historial[:] = historial[-MAX_HISTORIAL:]

    print(f"[DEBUG] Mensajes en memoria: {len(historial)}")

    guardar_memoria(historial)

    return respuesta_texto

# EJECUCIÓN
print("🎪 CAIN ha iniciado...")
print("Escribe 'salir' para terminar.\n")

while True:
    usuario = input("TÚ: ")
    
    if usuario.lower() == "salir":
        print("🎪 CAIN: El espectáculo termina... por ahora.")
        break
    
    respuesta = hablar_con_cain(usuario)
    print(f"\nCAIN: {respuesta}\n")