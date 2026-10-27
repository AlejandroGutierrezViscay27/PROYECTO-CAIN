"""
Control del sistema operativo (Fase 10). Ver FASE10_PLAN.md.

Todo lo que pase por aquí lo pide una herramienta del agente, y toda
herramienta pasa antes por el arnés (core/arnes).
"""
import os


def crear_control_so():
    """
    Fábrica del ControlSO activo, elegido con CAIN_SO en el .env.

    - "off" (default): sin control del sistema; las herramientas de sistema
      ni siquiera se le ofrecen al LLM.
    - "simulado": no toca nada (pruebas, ensayos).
    - "windows": el sistema real.
    """
    modo = os.getenv("CAIN_SO", "off").strip().lower()
    if modo == "off":
        return None
    if modo == "simulado":
        from so.simulado import SimuladoSO
        return SimuladoSO()
    if modo == "windows":
        if os.name != "nt":
            raise ValueError("CAIN_SO='windows' solo funciona en Windows.")
        from so.windows import WindowsSO
        return WindowsSO()
    raise ValueError(f"CAIN_SO='{modo}' no reconocido. Usa 'off', 'simulado' o 'windows'.")
