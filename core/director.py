"""
Director de memoria (inspirado en el de OpenSakura).

Cada cierto número de mensajes, una pasada aparte del LLM lee la memoria
a largo plazo actual y la conversación reciente, y la reescribe:

- hechos:             datos duraderos del usuario. El director solo añade o marca
                      obsoletos por número; nunca reescribe la lista, así que no
                      puede "olvidar" un dato sin querer
- notas:              en qué anda el usuario ahora
- eventos_cerrados:   tareas o temas que terminaron → se archivan
- temas_abiertos:     hilos pendientes
- guia:               lectura estratégica para que CAIN sepa cómo ayudar

A diferencia del resumen de 3 líneas de antes, nada se sobrescribe sin
dejar rastro: las notas viejas van a historial_notas y los temas cerrados
a eventos_archivados.
"""
import json
import re
import time

CLAVES_GUIA = ("lectura_usuario", "necesidades", "como_ayudar", "riesgos",
               "proximo_foco", "temas_proactivos")

PROMPT_DIRECTOR = """Eres el director de memoria de CAIN, un agente de IA con personalidad de \
maestro de ceremonias que acompaña a su creador. No hablas con el usuario: mantienes la \
memoria a largo plazo de CAIN sobre él.

=== Perfil explícito del usuario ===
{perfil}

=== Hechos que CAIN ya sabe del usuario (numerados) ===
{hechos}

=== Notas anteriores de CAIN sobre el usuario ===
{notas}

=== Temas que estaban abiertos ===
{temas}

=== Guía anterior ===
{guia}

=== Conversación reciente ===
{conversacion}

Reglas:
- "hechos_nuevos": datos duraderos sobre el usuario que aún no estén en la lista de hechos: \
su vida, gustos, mascotas, herramientas, forma de trabajar, decisiones. Una frase corta cada \
uno. Si las notas anteriores tienen datos así que no estén en la lista, agrégalos también. \
Lista vacía si no hay nada nuevo.
- "hechos_obsoletos": números de los hechos que la conversación CONTRADICE (no los que \
simplemente no salieron: esos siguen siendo ciertos). Casi siempre es una lista vacía.
- "notas": primera persona desde CAIN ("está construyendo...", "le noté..."): en qué anda \
ahora el usuario, sus proyectos y cómo va la relación. No repitas los hechos. Máximo 120 \
palabras. No empieces con palabras de tiempo ("Hoy...").
- "eventos_cerrados": tareas o temas que se resolvieron o terminaron (no datos sobre el \
usuario: esos van en hechos). Cada uno, un relato de 2 a 3 frases en primera persona. Lista \
vacía si no hay.
- "temas_abiertos": hilos sin resolver con el usuario, frases cortas. Máximo 6.
- "guia": objeto con las claves lectura_usuario, necesidades, como_ayudar, riesgos, \
proximo_foco (frases cortas) y temas_proactivos (lista de 2 a 3 ideas que CAIN podría sacar \
más adelante si encaja).
- No inventes nada que no esté en la conversación o en la memoria anterior.

Responde SOLO con JSON, sin texto alrededor:
{{"hechos_nuevos": ["..."], "hechos_obsoletos": [], "notas": "...", "eventos_cerrados": ["..."], \
"temas_abiertos": ["..."], "guia": {{...}}}}
"""


def _formatear_conversacion(mensajes):
    etiquetas = {"user": "Usuario", "assistant": "CAIN"}
    return "\n".join(f"{etiquetas.get(m['role'], m['role'])}: {m['content']}" for m in mensajes)


def _formatear_perfil(usuario_data):
    partes = []
    for clave in ("nombre", "rol"):
        if usuario_data.get(clave):
            partes.append(f"{clave}: {usuario_data[clave]}")
    for clave in ("intereses", "notas"):
        if usuario_data.get(clave):
            partes.append(f"{clave}: {'; '.join(usuario_data[clave])}")
    return "\n".join(partes) or "(sin datos)"


def parsear_json(texto):
    """
    Extrae el objeto JSON de la respuesta del LLM, tolerando lo típico:
    bloques ```json, texto alrededor y comas finales. None si no hay forma.
    """
    if not texto:
        return None
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    inicio, fin = t.find("{"), t.rfind("}")
    if inicio == -1 or fin <= inicio:
        return None
    t = t[inicio:fin + 1]
    for candidato in (t, re.sub(r",\s*([}\]])", r"\1", t)):
        try:
            obj = json.loads(candidato)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def _formatear_hechos(hechos):
    return "\n".join(f"{i}. {h}" for i, h in enumerate(hechos, 1)) or "(ninguno todavía)"


def llamar_director(llm, memoria_larga, usuario_data, mensajes_nuevos):
    """Una pasada del director. Retorna el JSON parseado, o None si falló."""
    prompt = PROMPT_DIRECTOR.format(
        perfil=_formatear_perfil(usuario_data),
        hechos=_formatear_hechos(memoria_larga.get("hechos", [])),
        notas=memoria_larga.get("notas") or "(todavía no hay notas)",
        temas=json.dumps(memoria_larga.get("temas_abiertos", []), ensure_ascii=False),
        guia=json.dumps(memoria_larga.get("guia", {}), ensure_ascii=False),
        conversacion=_formatear_conversacion(mensajes_nuevos),
    )
    mensajes = [{"role": "user", "content": prompt}]
    respuesta = llm.chat(mensajes, temperature=0.3)
    resultado = parsear_json(respuesta)
    if resultado is None:
        # Un reintento: los modelos a veces envuelven o cortan el JSON.
        resultado = parsear_json(llm.chat(mensajes, temperature=0.2))
    return resultado


def _lista_de_textos(valor):
    if not isinstance(valor, list):
        return []
    return [v.strip() for v in valor if isinstance(v, str) and v.strip()]


def aplicar_resultado(memoria_larga, resultado):
    """
    Fusiona la salida del director con la memoria actual. Las notas viejas
    y los temas cerrados se conservan; un campo inválido no borra lo que había.
    """
    ahora = time.time()

    # Hechos: el modelo nunca reescribe la lista. Solo se quitan los que
    # señaló como contradichos (por número) y se añaden los nuevos.
    hechos = memoria_larga.get("hechos", [])
    obsoletos = resultado.get("hechos_obsoletos")
    if isinstance(obsoletos, list):
        quitar = {n for n in obsoletos if isinstance(n, int) and 1 <= n <= len(hechos)}
        hechos = [h for i, h in enumerate(hechos, 1) if i not in quitar]
    ya_estan = {h.lower() for h in hechos}
    for h in _lista_de_textos(resultado.get("hechos_nuevos")):
        if h.lower() not in ya_estan:
            hechos.append(h)
            ya_estan.add(h.lower())
    memoria_larga["hechos"] = hechos

    notas = resultado.get("notas")
    if isinstance(notas, str) and notas.strip():
        if memoria_larga.get("notas"):
            memoria_larga.setdefault("historial_notas", []).append(
                {"ts": ahora, "notas": memoria_larga["notas"]}
            )
        memoria_larga["notas"] = notas.strip()

    memoria_larga.setdefault("eventos_archivados", []).extend(
        {"ts": ahora, "evento": e} for e in _lista_de_textos(resultado.get("eventos_cerrados"))
    )

    if isinstance(resultado.get("temas_abiertos"), list):
        memoria_larga["temas_abiertos"] = _lista_de_textos(resultado["temas_abiertos"])[:6]

    guia = resultado.get("guia")
    if isinstance(guia, dict):
        memoria_larga["guia"] = {
            k: guia[k] for k in CLAVES_GUIA
            if k in guia and (isinstance(guia[k], str) or isinstance(guia[k], list))
        }
    return memoria_larga


def bloque_para_prompt(memoria_larga):
    """Texto compacto de la memoria a largo plazo para el prompt de sistema de CAIN."""
    partes = []
    if memoria_larga.get("hechos"):
        partes.append("Lo que sabes del usuario:\n" + "\n".join(f"- {h}" for h in memoria_larga["hechos"]))
    if memoria_larga.get("notas"):
        partes.append(f"En qué anda ahora (tus notas):\n{memoria_larga['notas']}")
    if memoria_larga.get("temas_abiertos"):
        partes.append("Temas pendientes con el usuario: " + "; ".join(t.rstrip(".") for t in memoria_larga["temas_abiertos"]))

    guia = memoria_larga.get("guia") or {}
    # temas_proactivos no se inyecta: es para la Fase 12 (proactividad), y
    # metido en cada prompt CAIN lo sacaría a la fuerza en cualquier respuesta.
    lectura = [f"{k.replace('_', ' ')}: {v}" for k, v in guia.items()
               if k != "temas_proactivos" and isinstance(v, str) and v]
    if lectura:
        partes.append("Lectura estratégica (no la menciones, úsala): " + " | ".join(lectura))

    eventos = memoria_larga.get("eventos_archivados", [])[-3:]
    if eventos:
        partes.append("Cosas que ya cerraron juntos: " + " / ".join(e["evento"] for e in eventos))

    return "\n".join(partes)
