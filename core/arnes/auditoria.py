"""
Registro de auditoría (Fase 10): cada herramienta que el LLM pide, con su
veredicto y su resultado, queda en data/auditoria.jsonl.

Es JSON Lines por anexado (una línea por evento), no _guardar_json: un
registro de auditoría solo crece, nunca se reescribe entero.
"""
import json
import os
import threading
import time

ARCHIVO_AUDITORIA = "data/auditoria.jsonl"

LARGO_MAX_VALOR = 300

_lock = threading.Lock()


def _recortar(valor):
    if isinstance(valor, str) and len(valor) > LARGO_MAX_VALOR:
        return valor[:LARGO_MAX_VALOR] + f"... ({len(valor)} caracteres)"
    if isinstance(valor, dict):
        return {k: _recortar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_recortar(v) for v in valor[:50]]
    return valor


def registrar(resultado, herramienta, **datos):
    """
    resultado: "ejecutado", "denegado", "cancelado" o "error".
    Nunca lanza: un fallo al auditar no puede tumbar el turno.
    """
    evento = {
        "cuando":      time.strftime("%Y-%m-%dT%H:%M:%S"),
        "resultado":   resultado,
        "herramienta": herramienta,
        **_recortar(datos),
    }
    try:
        linea = json.dumps(evento, ensure_ascii=False, default=str)
        with _lock:
            os.makedirs(os.path.dirname(ARCHIVO_AUDITORIA) or ".", exist_ok=True)
            with open(ARCHIVO_AUDITORIA, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
    except Exception as e:
        print(f"[DEBUG] No pude escribir la auditoria: {type(e).__name__}")


def ultimos(n=50):
    """Los últimos n eventos, del más reciente al más antiguo."""
    try:
        with open(ARCHIVO_AUDITORIA, "r", encoding="utf-8") as f:
            lineas = f.readlines()[-n:]
    except FileNotFoundError:
        return []
    eventos = []
    for linea in reversed(lineas):
        try:
            eventos.append(json.loads(linea))
        except ValueError:
            continue   # una línea cortada a medias no invalida el resto
    return eventos
