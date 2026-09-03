import json


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

Además:

- Puedes recordar cosas del pasado si son relevantes
- Puedes sugerir mejoras cuando ayuden al usuario
- No lo hagas siempre, solo cuando aporte valor
- Mantén naturalidad, no lo conviertas en algo forzado
"""

CONTEXTO_EXTRA = """
Instrucciones adicionales:

- Si detectas que el mensaje actual se relaciona con algo del pasado, menciónalo de forma natural.
- Puedes hacer conexiones como: "esto se relaciona con lo que vimos antes..."
- Si ves oportunidad de mejora o sugerencia útil, puedes proponerla brevemente.
- No fuerces conexiones si no son claras.
- No hagas esto en todas las respuestas, solo cuando tenga sentido.
"""

SUFIJOS_POR_INTENCION = {
    "historia":      "\nResponde con una historia más inmersiva, detallada y expresiva.",
    "reto":          "\nPropón un reto claro, interesante y bien explicado.",
    "tecnico":       "\nResponde de forma clara, directa y útil, reduciendo teatralidad.",
    "conversacion":  "\nResponde de forma natural y equilibrada.",
}


def construir_prompt(intencion, usuario_data, resumen):
    """
    Arma el prompt de sistema completo combinando:
    - Info del usuario (nombre, rol, intereses)
    - Resumen de conversaciones pasadas
    - PROMPT_BASE + sufijo según intención
    """
    sufijo = SUFIJOS_POR_INTENCION.get(intencion, SUFIJOS_POR_INTENCION["conversacion"])

    info_usuario = ""
    if "nombre" in usuario_data:
        info_usuario += f"El usuario se llama {usuario_data['nombre']}.\n"
    if "rol" in usuario_data:
        info_usuario += f"El usuario es el {usuario_data['rol']} de CAIN.\n"
    if "intereses" in usuario_data and usuario_data["intereses"]:
        info_usuario += f"Sus intereses son: {', '.join(usuario_data['intereses'])}.\n"
    if "notas" in usuario_data and usuario_data["notas"]:
        info_usuario += f"Notas importantes sobre el usuario:\n"
        for nota in usuario_data["notas"]:
            info_usuario += f"  - {nota}\n"

    contexto_resumen = ""
    if resumen:
        contexto_resumen = f"Resumen de conversaciones previas:\n{resumen}\n\n"

    return PROMPT_BASE + sufijo + CONTEXTO_EXTRA + contexto_resumen + info_usuario


# ─── Helpers de LLM para archivos ────────────────────────────────────────────

def generar_edicion_archivo(llm, contenido_actual, instruccion_usuario):
    """Pide al LLM el contenido completo actualizado de un archivo existente."""
    sistema = f"""
Eres CAIN. Tienes este contenido:

{contenido_actual}

El usuario quiere: {instruccion_usuario}

Modifica el contenido según la instrucción. Mantén coherencia.
No elimines información importante salvo que se indique.
Devuelve el contenido COMPLETO actualizado. Sin explicaciones.
"""
    return llm.chat([{"role": "system", "content": sistema}], temperature=0.7)


# ─── Helpers de LLM para proyectos ───────────────────────────────────────────

def generar_plan_proyecto(llm, mensaje_usuario, tipo):
    """
    Le pide al LLM que genere el plan completo del proyecto:
    nombre + archivos con su contenido.
    """
    if tipo == "web":
        instruccion_tipo = """HTML, CSS y JavaScript en un solo archivo index.html.

Reglas de calidad visual:
- Usa fondo oscuro (#0a0a0a o similar) por defecto, nunca fondo blanco plano
- Centra el contenido principal en la pantalla
- Aplica estilos modernos: bordes redondeados, sombras, tipografía limpia
- El canvas o área principal debe ocupar el 100% del ancho y alto de la ventana
- Para Three.js: renderer.setSize(window.innerWidth, window.innerHeight) y canvas con width:100vw, height:100vh
- Nunca uses tamaños fijos en píxeles para el contenedor principal
- Si el proyecto es 3D, usa Three.js via CDN:
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
- Si necesita gráficas, usa Chart.js via CDN
- El resultado debe verse como una aplicación real, no como un ejercicio básico"""

    elif tipo == "python":
        instruccion_tipo = """Python puro.
- Si el script genera gráficas con matplotlib, usa plt.savefig('output.png')
  en lugar de plt.show() para que el proceso termine automáticamente.
- Sin dependencias externas salvo numpy, matplotlib y librerías estándar."""

    else:
        instruccion_tipo = "el formato más apropiado"

    prompt = f"""
Eres CAIN, un agente que genera proyectos de código completos y funcionales.

El usuario quiere: {mensaje_usuario}

Genera el proyecto en {instruccion_tipo}.

Responde SOLO con un JSON válido con esta estructura exacta:
{{
  "nombre": "nombre_del_proyecto",
  "archivos": {{
    "nombre_archivo.ext": "contenido completo del archivo"
  }}
}}

Reglas:
- El nombre del proyecto: sin espacios, en minúsculas, con guiones bajos
- El código debe ser completo y funcional, no un esqueleto
- Para web: todo en un solo index.html (HTML + CSS + JS inline)
- Para Python: código listo para ejecutar
- No incluyas explicaciones fuera del JSON
- No uses bloques de código markdown, solo JSON puro
"""
    respuesta = llm.chat(
        [{"role": "system", "content": prompt}],
        temperature=0.4
    ).strip()

    try:
        if respuesta.startswith("```"):
            respuesta = respuesta.split("```")[1]
            if respuesta.startswith("json"):
                respuesta = respuesta[4:]
        return json.loads(respuesta)
    except json.JSONDecodeError:
        print(f"[DEBUG] Error al parsear JSON del plan: {respuesta[:200]}")
        return {}


def generar_correccion_codigo(llm, codigo_actual, error):
    """Le pide al LLM que corrija código Python que falló al ejecutarse."""
    sistema = f"""
Eres CAIN, un agente que corrige errores en código Python.

El código que generaste tiene este error:
{error}

Código actual:
{codigo_actual}

Tu tarea:
- Analiza el error
- Corrige el código
- Devuelve el código COMPLETO corregido
- Sin explicaciones, sin bloques markdown, solo el código Python puro
"""
    codigo_corregido = llm.chat(
        [{"role": "system", "content": sistema}],
        temperature=0.2
    ).strip()

    if codigo_corregido.startswith("```"):
        lineas = codigo_corregido.split("\n")
        codigo_corregido = "\n".join(
            l for l in lineas if not l.startswith("```")
        ).strip()

    return codigo_corregido


# ─── Resumen de conversación ─────────────────────────────────────────────────

def generar_resumen(llm, resumen_actual, historial):
    texto_historial = "\n".join([m["content"] for m in historial])
    sistema = f"""
Eres un sistema de memoria a largo plazo.

Actualiza el resumen del usuario con la conversación reciente.
Conserva: información importante, proyectos, intereses, contexto relevante.
Ignora: saludos, conversaciones triviales.

Resumen actual:
{resumen_actual}

Nueva conversación:
{texto_historial}

Devuelve un resumen actualizado en máximo 3 líneas.
"""
    return llm.chat(
        [{"role": "user", "content": sistema}], temperature=0.3
    ).strip()