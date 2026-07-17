from llm.openai_provider import OpenAIProvider
# Cuando migres a Ollama, cambia la línea de arriba por esta:
# from llm.ollama_provider import OllamaProvider

from core import memory, tools, intent, prompts, executor
import os
import json


class Cain:
    """
    Agente principal. Orquesta memoria, herramientas, intención y LLM.
    No conoce a OpenAI ni a Ollama — solo habla con LLMProvider.
    """

    def __init__(self):
        self.llm            = OpenAIProvider()
        # Cuando migres a Ollama:
        # self.llm = OllamaProvider(model="llama3")

        self.historial      = memory.cargar_memoria()
        self.usuario_data   = memory.cargar_usuario()
        self.resumen        = memory.cargar_resumen()
        self.ultimo_archivo = None

    # ─── Punto de entrada ────────────────────────────────────────────────────

    def chat(self, mensaje_usuario):
        """Procesa un mensaje del usuario y retorna la respuesta de CAIN."""

        accion = self._detectar_accion(mensaje_usuario)
        print(f"[DEBUG] Acción detectada: {accion}")

        if accion == "crear_archivo":
            return self._crear_archivo(mensaje_usuario)
        elif accion == "leer_archivo":
            return self._leer_archivo(mensaje_usuario)
        elif accion == "borrar_archivo":
            return self._borrar_archivo(mensaje_usuario)
        elif accion == "editar_archivo":
            return self._editar_archivo(mensaje_usuario)
        elif accion == "ejecutar_proyecto":
            return self._flujo_ejecutar_proyecto(mensaje_usuario)
        elif accion in ("memoria_recordar", "memoria_olvidar", "memoria_consultar"):
            return self._flujo_memoria(accion, mensaje_usuario)

        return self._conversar(mensaje_usuario)

    # ─── Herramientas de archivo ─────────────────────────────────────────────

    def _crear_archivo(self, mensaje_usuario):
        nombre    = self._generar_nombre_archivo(mensaje_usuario)
        nombre    = tools.evitar_sobrescritura(nombre)
        contenido = self._generar_contenido_archivo(mensaje_usuario)
        resultado = tools.crear_archivo(nombre, contenido)
        self.ultimo_archivo = nombre
        return f"🎭 He creado algo para este espectáculo...\n{resultado}"

    def _leer_archivo(self, mensaje_usuario):
        nombre = tools.resolver_archivo(mensaje_usuario, self.ultimo_archivo)
        if nombre == "preguntar":
            return "🎭 ¿Qué archivo quieres que lea?"
        if not os.path.exists(nombre):
            return f"🎭 No encontré el archivo '{nombre}'."
        self.ultimo_archivo = nombre
        return tools.leer_archivo(nombre)

    def _borrar_archivo(self, mensaje_usuario):
        nombre = tools.extraer_nombre_archivo(mensaje_usuario)
        if not nombre:
            return "🎭 Necesito el nombre del archivo que deseas eliminar."
        return tools.borrar_archivo(nombre)

    def _editar_archivo(self, mensaje_usuario):
        nombre = tools.resolver_archivo(mensaje_usuario, self.ultimo_archivo)
        if nombre == "preguntar":
            return "🎭 ¿A qué archivo te refieres?"
        if not os.path.exists(nombre):
            return f"🎭 El archivo '{nombre}' no existe aún... ¿quieres que lo cree primero?"
        if not intent.es_misma_intencion_archivo(nombre, mensaje_usuario, self.llm):
            return "🎭 Esto no parece encajar con el archivo actual... puedo crear uno nuevo si quieres."
        resultado = self._editar_archivo_inteligente(nombre, mensaje_usuario)
        self.ultimo_archivo = nombre
        return resultado

    # ─── Memoria explícita ───────────────────────────────────────────────────

    def _flujo_memoria(self, accion, mensaje_usuario):
        """Maneja comandos explícitos de memoria: recordar, olvidar, consultar."""

        if accion == "memoria_consultar":
            return memory.consultar_memoria(self.usuario_data, self.resumen)

        contenido = intent.extraer_contenido_memoria(mensaje_usuario, accion, self.llm)
        print(f"[DEBUG] Contenido de memoria extraído: '{contenido}'")

        if accion == "memoria_recordar":
            self.usuario_data = memory.agregar_nota(self.usuario_data, contenido)
            memory.guardar_usuario(self.usuario_data)
            return f"🧠 Anotado. Recordaré que {contenido}."

        elif accion == "memoria_olvidar":
            if contenido == "todo":
                self.usuario_data = {}
                memory.guardar_usuario(self.usuario_data)
                memory.limpiar_historial_completo()
                self.historial = []
                self.resumen   = ""
                return "🧠 Hecho. He olvidado todo lo que sabía de ti."

            elif contenido == "historial":
                memory.limpiar_historial_completo()
                self.historial = []
                self.resumen   = ""
                return "🧠 Historial borrado. Empezamos desde cero."

            elif contenido in ("nombre", "rol", "intereses", "notas"):
                self.usuario_data = memory.olvidar_campo(self.usuario_data, contenido)
                memory.guardar_usuario(self.usuario_data)
                return f"🧠 Listo. He olvidado tu {contenido}."

            else:
                self.usuario_data, eliminadas = memory.olvidar_nota(
                    self.usuario_data, contenido
                )
                memory.guardar_usuario(self.usuario_data)
                if eliminadas > 0:
                    return f"🧠 Listo. He olvidado lo relacionado con '{contenido}'."
                return f"🧠 No encontré nada relacionado con '{contenido}' en mi memoria."

        return "🎭 No entendí qué querías hacer con la memoria."

    # ─── Ejecución de proyectos ──────────────────────────────────────────────

    def _flujo_ejecutar_proyecto(self, mensaje_usuario):
        """
        Flujo completo con confirmación.
        - Modo terminal: usa input() clásico
        - Modo web: usa self._confirmar_fn callback inyectado por app.py
        """
        tipo = intent.detectar_tipo_proyecto_llm(mensaje_usuario, self.llm)
        print(f"[DEBUG] Tipo de proyecto: {tipo}")

        plan            = self._generar_plan_proyecto(mensaje_usuario, tipo)
        nombre_proyecto = plan.get("nombre", "proyecto_cain")
        archivos        = plan.get("archivos", {})

        if not archivos:
            return "🎭 No pude generar el proyecto. ¿Puedes darme más detalles?"

        lista_archivos = list(archivos.keys())
        comando        = self._describir_comando(tipo, lista_archivos)

        # ── Confirmación: web o terminal ─────────────────────────────────────
        if hasattr(self, "_confirmar_fn") and self._confirmar_fn:
            # Modo web — enviar plan al frontend y esperar respuesta
            confirmado = self._confirmar_fn({
                "archivos": lista_archivos,
                "comando":  comando,
                "nombre":   nombre_proyecto,
            })
        else:
            # Modo terminal — usar input() clásico
            print(f"\nCAIN: 🎭 Plan de ejecución:")
            for a in lista_archivos:
                print(f"      📄 {a}")
            print(f"      📟 {comando}")
            respuesta = input("\n¿Procedo? (s/n): ").strip().lower()
            confirmado = respuesta in ("s", "si", "sí", "yes", "y")

        if not confirmado:
            return "🎭 Entendido, cancelado. Dime cuando quieras intentarlo de nuevo."

        resultado, url, info_error = executor.ejecutar_proyecto(nombre_proyecto, archivos, tipo)

        if info_error:
            ruta_archivo, error = info_error
            resultado = self._corregir_y_reintentar(ruta_archivo, error, resultado)

        if url:
            return f"🎭 ¡El espectáculo está en vivo!\n\n{resultado}"
        return f"🎭 ¡Listo!\n\n{resultado}"

    def _corregir_y_reintentar(self, ruta_archivo, error, mensaje_original, intentos=2):
        """
        Intenta corregir el código automáticamente cuando hay un error.
        Máximo 2 intentos para no entrar en loop infinito.
        """
        for intento in range(1, intentos + 1):
            print(f"\nCAIN: 🔧 Encontré un error. Intentando corregir (intento {intento}/{intentos})...")

            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    codigo_actual = f.read()
            except Exception:
                return mensaje_original

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
            codigo_corregido = self.llm.chat(
                [{"role": "system", "content": sistema}],
                temperature=0.2
            ).strip()

            if codigo_corregido.startswith("```"):
                lineas = codigo_corregido.split("\n")
                codigo_corregido = "\n".join(
                    l for l in lineas if not l.startswith("```")
                ).strip()

            try:
                with open(ruta_archivo, "w", encoding="utf-8") as f:
                    f.write(codigo_corregido)
            except Exception:
                return mensaje_original

            exito, nuevo_mensaje, nuevo_error = executor.ejecutar_python(ruta_archivo)

            if exito:
                return (
                    f"🔧 Detecté y corregí un error automáticamente.\n\n"
                    f"📁 Archivo: {ruta_archivo}\n\n"
                    f"{nuevo_mensaje}"
                )
            else:
                error = nuevo_error

        return (
            f"{mensaje_original}\n\n"
            f"⚠️ Intenté corregirlo {intentos} veces pero el error persiste.\n"
            f"Puedes pedirme que lo intente de nuevo con más detalles."
        )

    # ─── Conversación ────────────────────────────────────────────────────────

    def _conversar(self, mensaje_usuario):
        if len(self.historial) > 0 and len(self.historial) % 10 == 0:
            self.resumen = self._actualizar_resumen()
            memory.guardar_resumen(self.resumen)
            print("[DEBUG] Resumen actualizado")

        intencion = self._detectar_intencion(mensaje_usuario)
        print(f"[DEBUG] Intención detectada: {intencion}")

        self._actualizar_usuario(mensaje_usuario)

        prompt_sistema = prompts.construir_prompt(intencion, self.usuario_data, self.resumen)

        self.historial.append({"role": "user", "content": mensaje_usuario})
        mensajes = [{"role": "system", "content": prompt_sistema}] + self.historial

        respuesta_texto = self.llm.chat(mensajes, temperature=0.7)

        self.historial.append({"role": "assistant", "content": respuesta_texto})
        self.historial = memory.truncar_historial(self.historial)
        memory.guardar_memoria(self.historial)

        print(f"[DEBUG] Mensajes en memoria: {len(self.historial)}")
        return respuesta_texto

    # ─── Detección (delega en intent) ────────────────────────────────────────

    def _detectar_accion(self, mensaje_usuario):
        return intent.detectar_accion_llm(mensaje_usuario, self.llm)

    def _detectar_intencion(self, mensaje_usuario):
        return intent.detectar_intencion_llm(mensaje_usuario, self.llm)

    # ─── Actualización de datos del usuario ──────────────────────────────────

    def _actualizar_usuario(self, mensaje_usuario):
        nombre = intent.detectar_nombre(mensaje_usuario)
        if nombre:
            self.usuario_data["nombre"] = nombre
            memory.guardar_usuario(self.usuario_data)
            print(f"[DEBUG] Nombre guardado: {nombre}")

        rol = intent.detectar_rol(mensaje_usuario)
        if rol:
            self.usuario_data["rol"] = rol
            memory.guardar_usuario(self.usuario_data)
            print(f"[DEBUG] Rol guardado: {rol}")

        intereses = intent.detectar_intereses_llm(mensaje_usuario, self.llm)
        if intereses:
            if "intereses" not in self.usuario_data:
                self.usuario_data["intereses"] = []
            for i in intereses:
                if i not in self.usuario_data["intereses"]:
                    self.usuario_data["intereses"].append(i)
            memory.guardar_usuario(self.usuario_data)
            print(f"[DEBUG] Intereses guardados: {self.usuario_data['intereses']}")

    # ─── Helpers de LLM para archivos ────────────────────────────────────────

    def _generar_contenido_archivo(self, prompt_usuario):
        sistema = f"""
Eres CAIN. Genera contenido útil, claro y bien estructurado para un archivo.

Solicitud: {prompt_usuario}

El contenido debe ser claro, bien organizado y listo para guardarse.
"""
        return self.llm.chat([{"role": "system", "content": sistema}], temperature=0.7)

    def _generar_nombre_archivo(self, mensaje_usuario):
        sistema = f"""
Genera un nombre de archivo corto basado en esta solicitud:
{mensaje_usuario}

Reglas: máximo 3 palabras, sin espacios (usar _), en minúsculas, sin extensión.
Ejemplos: historia_terror, ideas_python, resumen_ia

Solo responde el nombre, nada más.
"""
        nombre = self.llm.chat(
            [{"role": "system", "content": sistema}], temperature=0.3
        ).strip().lower()
        return nombre + ".txt"

    def _editar_archivo_inteligente(self, nombre, instruccion_usuario):
        try:
            with open(nombre, "r", encoding="utf-8") as f:
                contenido_actual = f.read()

            sistema = f"""
Eres CAIN. Tienes este contenido:

{contenido_actual}

El usuario quiere: {instruccion_usuario}

Modifica el contenido según la instrucción. Mantén coherencia.
No elimines información importante salvo que se indique.
Devuelve el contenido COMPLETO actualizado. Sin explicaciones.
"""
            nuevo_contenido = self.llm.chat(
                [{"role": "system", "content": sistema}], temperature=0.7
            )
            with open(nombre, "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            return f"✏️ Archivo '{nombre}' actualizado."
        except Exception as e:
            return f"Error en edición: {str(e)}"

    # ─── Helpers de LLM para proyectos ───────────────────────────────────────

    def _generar_plan_proyecto(self, mensaje_usuario, tipo):
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
        respuesta = self.llm.chat(
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

    def _describir_comando(self, tipo, archivos):
        """Genera una descripción legible del comando que se va a ejecutar."""
        if tipo == "web":
            return "python -m http.server (puerto libre automático)"
        elif tipo == "python":
            py_file = next((a for a in archivos if a.endswith(".py")), archivos[0])
            return f"python {py_file}"
        return "abrir archivo directamente"

    # ─── Resumen de conversación ─────────────────────────────────────────────

    def _actualizar_resumen(self):
        texto_historial = "\n".join([m["content"] for m in self.historial])
        sistema = f"""
Eres un sistema de memoria a largo plazo.

Actualiza el resumen del usuario con la conversación reciente.
Conserva: información importante, proyectos, intereses, contexto relevante.
Ignora: saludos, conversaciones triviales.

Resumen actual:
{self.resumen}

Nueva conversación:
{texto_historial}

Devuelve un resumen actualizado en máximo 3 líneas.
"""
        return self.llm.chat(
            [{"role": "user", "content": sistema}], temperature=0.3
        ).strip()