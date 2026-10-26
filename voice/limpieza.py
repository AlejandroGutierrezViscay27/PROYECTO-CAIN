import re

# Emoji y pictogramas: CAIN usa 🎭 🧠 ✦ etc. en el chat, pero Piper
# los lee como basura o silencios raros.
_EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"   # emoji, símbolos y pictogramas
    "\U0001F1E6-\U0001F1FF"   # banderas
    "☀-➿"           # símbolos varios y dingbats (✦ ✅ ⏳ ...)
    "⬀-⯿"           # flechas y estrellas
    "️‍"            # selector de variación y ZWJ
    "]+"
)

_BLOQUE_CODIGO   = re.compile(r"```.*?(```|$)", re.S)
_CODIGO_EN_LINEA = re.compile(r"`([^`]*)`")
_ENLACE_MD       = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_URL             = re.compile(r"https?://\S+")
_TITULO          = re.compile(r"^\s{0,3}#{1,6}\s*", re.M)
_VINETA          = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+", re.M)
_NEGRITA         = re.compile(r"(\*\*|__)(.+?)\1")
_CURSIVA         = re.compile(r"(?<!\w)\*(\S[^*]*?)\*(?!\w)")
_FLECHAS         = re.compile(r"\s*[→←⇒➜]\s*")

AVISO_CODIGO = " Dejé el código en el chat. "
AVISO_ENLACE = "el enlace del chat"


def limpiar_para_voz(texto: str) -> str:
    """
    Convierte una respuesta pensada para el chat en texto apto para TTS.

    Quita emoji, markdown y bloques de código (que no tiene sentido leer
    en voz alta), y une las líneas en frases para que el motor haga
    pausas naturales.

    Returns:
        Texto listo para sintetizar. Cadena vacía si no queda nada que decir.
    """
    if not texto:
        return ""

    t = _BLOQUE_CODIGO.sub(AVISO_CODIGO, texto)
    t = _CODIGO_EN_LINEA.sub(r"\1", t)
    t = _ENLACE_MD.sub(r"\1", t)
    t = _URL.sub(AVISO_ENLACE, t)
    t = _EMOJI.sub("", t)
    t = _TITULO.sub("", t)
    t = _VINETA.sub("", t)
    t = _NEGRITA.sub(r"\2", t)
    t = _CURSIVA.sub(r"\1", t)
    t = _FLECHAS.sub(", ", t)
    t = t.replace("|", " ").replace("_", " ").replace("*", "").replace("#", "")

    # Cada línea es una frase: si no termina en puntuación, se le pone punto.
    frases = []
    for linea in t.splitlines():
        linea = " ".join(linea.split()).strip(" ,")
        if not linea:
            continue
        if linea[-1] not in ".!?…:;":
            linea += "."
        frases.append(linea)

    t = " ".join(frases)
    t = re.sub(r"\s+([.,!?;:])", r"\1", t)
    # "listo:." / "hecho.." → sin el punto extra (los "..." se respetan: son pausas)
    t = re.sub(r"(?<!\.)([.!?;:])\.(?!\.)", r"\1", t)
    return t.strip()
