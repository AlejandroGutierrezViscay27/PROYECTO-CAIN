"""
Registro de gasto del LLM: cuántas llamadas y tokens usa cada rol de CAIN
(conversación, enrutador, intención, director, código) y con qué modelo.

Se guarda agregado por día en data/uso_llm.json, así el archivo no crece
con cada llamada, y el costo se calcula al leer con la tabla PRECIOS.
"""
import os
import threading
import time

from core.memory import _cargar_json, _guardar_json

ARCHIVO_USO = "data/uso_llm.json"

# USD por millón de tokens (entrada, salida). Aproximado: revisa la página de
# precios del proveedor si cambian. Un modelo que no esté aquí sale con costo
# None (desconocido); los modelos locales (Ollama) cuestan 0.
PRECIOS = {
    "gpt-4o-mini":  (0.15, 0.60),
    "gpt-4o":       (2.50, 10.00),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1":      (2.00, 8.00),
}


def costo(proveedor, modelo, entrada, salida):
    """Costo en USD de esos tokens, o None si el modelo no tiene precio conocido."""
    if proveedor == "ollama":
        return 0.0
    precio = PRECIOS.get(modelo)
    if precio is None:
        return None
    return (entrada * precio[0] + salida * precio[1]) / 1_000_000


class RegistroUso:

    def __init__(self, ruta=None, reloj=time.time):
        self.ruta   = ruta or ARCHIVO_USO
        self._reloj = reloj
        # El director corre en otro hilo: dos anotaciones a la vez no deben
        # pisarse al leer-modificar-escribir el archivo.
        self._lock  = threading.Lock()

    def anotar(self, rol, proveedor, modelo, entrada, salida):
        """Suma una llamada. Nunca lanza: perder un apunte no debe tumbar un turno."""
        try:
            dia = time.strftime("%Y-%m-%d", time.localtime(self._reloj()))
            clave = f"{proveedor}:{modelo}"
            with self._lock:
                datos = _cargar_json(self.ruta, {})
                fila = (datos.setdefault("dias", {}).setdefault(dia, {})
                        .setdefault(rol, {}).setdefault(clave, {"llamadas": 0, "entrada": 0, "salida": 0}))
                fila["llamadas"] += 1
                fila["entrada"]  += int(entrada or 0)
                fila["salida"]   += int(salida or 0)
                _guardar_json(self.ruta, datos)
        except Exception as e:
            print(f"[DEBUG] No se pudo anotar el uso del LLM: {e}")

    def resumen(self, dias=None):
        """
        Totales por rol y modelo, con costo. dias: lista de fechas "YYYY-MM-DD"
        a incluir (None = todas).

        Returns:
            {"roles": {rol: {"proveedor:modelo": {llamadas, entrada, salida, costo_usd}}},
             "costo_usd": float, "costo_incompleto": bool}
        """
        with self._lock:
            datos = _cargar_json(self.ruta, {})
        roles, total, incompleto = {}, 0.0, False
        for dia, por_rol in datos.get("dias", {}).items():
            if dias is not None and dia not in dias:
                continue
            for rol, por_modelo in por_rol.items():
                for clave, fila in por_modelo.items():
                    acc = roles.setdefault(rol, {}).setdefault(
                        clave, {"llamadas": 0, "entrada": 0, "salida": 0})
                    for campo in ("llamadas", "entrada", "salida"):
                        acc[campo] += fila.get(campo, 0)
        for por_modelo in roles.values():
            for clave, acc in por_modelo.items():
                proveedor, _, modelo = clave.partition(":")
                c = costo(proveedor, modelo, acc["entrada"], acc["salida"])
                acc["costo_usd"] = None if c is None else round(c, 6)
                if c is None:
                    incompleto = True
                else:
                    total += c
        return {"roles": roles, "costo_usd": round(total, 6), "costo_incompleto": incompleto}

    def resumen_hoy(self):
        return self.resumen(dias=[time.strftime("%Y-%m-%d", time.localtime(self._reloj()))])
