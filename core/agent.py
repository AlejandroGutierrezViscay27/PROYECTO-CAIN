from llm.openai_provider import OpenAIProvider
# Cuando migres a Ollama, cambia la línea de arriba por esta:
# from llm.ollama_provider import OllamaProvider

from core import memory, tools, intent, prompts, executor
import os


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
        nombre    = prompts.generar_nombre_archivo(self.llm, mensaje_usuario)
        nombre    = tools.evitar_sobrescritura(nombre)
        contenido = prompts.generar_contenido_archivo(self.llm, mensaje_usuario)
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

    def _editar_archivo_inteligente(self, nombre, instruccion_usuario):
        try:
            with open(nombre, "r", encoding="utf-8") as f:
                contenido_actual = f.read()
        except Exception as e:
            return f"Error en edición: {str(e)}"

        nuevo_contenido = prompts.generar_edicion_archivo(
            self.llm, contenido_actual, instruccion_usuario
        )
        return tools.editar_archivo(nombre, nuevo_contenido)

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

        plan            = prompts.generar_plan_proyecto(self.llm, mensaje_usuario, tipo)
        nombre_proyecto = plan.get("nombre", "proyecto_cain")
        archivos        = plan.get("archivos", {})

        if not archivos:
            return "🎭 No pude generar el proyecto. ¿Puedes darme más detalles?"

        lista_archivos = list(archivos.keys())
        comando        = executor.describir_comando(tipo, lista_archivos)

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
            resultado = executor.corregir_y_reintentar(self.llm, ruta_archivo, error, resultado)

        if url:
            return f"🎭 ¡El espectáculo está en vivo!\n\n{resultado}"
        return f"🎭 ¡Listo!\n\n{resultado}"

    # ─── Conversación ────────────────────────────────────────────────────────

    def _conversar(self, mensaje_usuario):
        if len(self.historial) > 0 and len(self.historial) % 10 == 0:
            self.resumen = prompts.generar_resumen(self.llm, self.resumen, self.historial)
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