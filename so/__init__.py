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


def crear_navegador():
    """
    El navegador de CAIN (Fase 10.3), según CAIN_SO igual que crear_control_so().
    Con "windows" hace falta Playwright y Brave o Edge; si falta algo, None y
    el navegador se abre como en la 10.2 (sin pestañas ni YouTube). No abre
    nada hasta que se le pide.
    """
    modo = os.getenv("CAIN_SO", "off").strip().lower()
    if modo == "simulado":
        from so.simulado import NavegadorSimulado
        return NavegadorSimulado()
    if modo != "windows":
        return None
    from core.arnes import sistema
    from core.arnes.rutas import Denegado
    try:
        ruta, _ = sistema.resolver_app("navegador")
        from so.navegador import NavegadorCAIN
    except (Denegado, ImportError) as e:
        print(f"[CAIN] Navegador sin pestanas ni YouTube ({type(e).__name__}); falta Playwright o el navegador")
        return None
    return NavegadorCAIN(ruta)
