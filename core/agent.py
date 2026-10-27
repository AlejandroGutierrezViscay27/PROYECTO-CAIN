from llm.fabrica import crear_llms
from llm.registro import RegistroUso

from core import memory, tools, intent, prompts, executor, director, emocion
from core.tool_schemas import TOOLS, PROMPT_ENRUTADOR
import copy
import os
import threading

# Cada cuántos mensajes nuevos (usuario + CAIN) pasa el director de memoria.
INTERVALO_DIRECTOR = 10


class Cain:
    """
    Agente principal. Orquesta memoria, herramientas, intención y LLM.
    No conoce a OpenAI ni a Ollama — solo habla con LLMProvider.
    """

    def __init__(self):
        # Un LLM por rol (ver llm/fabrica.py): se configuran en el .env con
        # LLM_PROVIDER_<ROL> / LLM_MODEL_<ROL>. self.llm es el de conversación.
        self.registro_uso   = RegistroUso()
        self.llms           = crear_llms(self.registro_uso)
        self.llm            = self.llms["conversacion"]

        self.historial      = memory.cargar_memoria()
        self.usuario_data   = memory.cargar_usuario()
        self.memoria_larga  = memory.cargar_memoria_larga()
        # Ánimo de CAIN: colorea el tono, La Cara y la prosodia de la voz.
        # Vive en memoria (no en disco): decae solo, así que tras reiniciar
        # simplemente arranca neutral.
        self.emocion        = emocion.EstadoEmocional()
        self.ultimo_archivo = None
        # Mensajes añadidos al historial desde la última pasada del director.
        # No se puede deducir de len(historial): el historial se trunca a
        # MAX_HISTORIAL y se queda fijo en ese tamaño.
        self.mensajes_sin_resumir = 0

        # El director corre en un hilo aparte para no retrasar la respuesta.
        # La generación sube con cada "olvida": si el director termina después
        # de un olvido, su resultado (de una memoria que ya no existe) se tira.
        self._lock_memoria       = threading.Lock()
        self._generacion_memoria = 0
        self._director_activo    = False
        self._hilo_director      = None

        self._herramientas = {
            "crear_archivo":     self._crear_archivo,
            "leer_archivo":      self._leer_archivo,
            "editar_archivo":    self._editar_archivo,
            "borrar_archivo":    self._borrar_archivo,
            "ejecutar_proyecto": self._flujo_ejecutar_proyecto,
            "memoria_recordar":  self._memoria_recordar,
            "memoria_olvidar":   self._memoria_olvidar,
            "memoria_consultar": self._memoria_consultar,
        }

    # ─── Punto de entrada ────────────────────────────────────────────────────

    def chat(self, mensaje_usuario, canal="texto"):
        """
        Procesa un mensaje del usuario y retorna la respuesta de CAIN.

        canal: "texto" o "voz". Con "voz" la respuesta se pide corta y sin
        formato, porque se va a sintetizar.
        """

        resultado = self.llms["enrutador"].chat_with_tools(
            [
                {"role": "system", "content": PROMPT_ENRUTADOR},
                {"role": "user",   "content": mensaje_usuario},
            ],
            tools=TOOLS,
            temperature=0.2,
        )

        tool_call = resultado.get("tool_call")
        if tool_call:
            nombre     = tool_call["name"]
            argumentos = tool_call["arguments"]
            print(f"[DEBUG] Herramienta invocada: {nombre}({argumentos})")
            handler = self._herramientas.get(nombre)
            if handler:
                return handler(argumentos)

        return self._conversar(mensaje_usuario, canal)

    # ─── Herramientas de archivo ─────────────────────────────────────────────

    def _crear_archivo(self, argumentos):
        nombre = argumentos.get("nombre_archivo") or tools.generar_nombre_timestamp()
        nombre = tools.normalizar_nombre_txt(nombre)
        nombre = tools.evitar_sobrescritura(nombre)
        contenido = argumentos.get("contenido", "")
        resultado = tools.crear_archivo(nombre, contenido)
        self.ultimo_archivo = nombre
        return f"🎭 He creado algo para este espectáculo...\n{resultado}"

    def _leer_archivo(self, argumentos):
        nombre = argumentos.get("nombre_archivo") or self.ultimo_archivo
        if not nombre:
            return "🎭 ¿Qué archivo quieres que lea?"
        nombre = tools.normalizar_nombre_txt(nombre)
        if not os.path.exists(nombre):
            return f"🎭 No encontré el archivo '{nombre}'."
        self.ultimo_archivo = nombre
        return tools.leer_archivo(nombre)

    def _borrar_archivo(self, argumentos):
        nombre = argumentos.get("nombre_archivo") or self.ultimo_archivo
        if not nombre:
            return "🎭 Necesito el nombre del archivo que deseas eliminar."
        nombre = tools.normalizar_nombre_txt(nombre)
        resultado = tools.borrar_archivo(nombre)
        if nombre == self.ultimo_archivo:
            self.ultimo_archivo = None
        return resultado

    def _editar_archivo(self, argumentos):
        nombre = argumentos.get("nombre_archivo") or self.ultimo_archivo
        if not nombre:
            return "🎭 ¿A qué archivo te refieres?"
        nombre = tools.normalizar_nombre_txt(nombre)
        if not os.path.exists(nombre):
            return f"🎭 El archivo '{nombre}' no existe aún... ¿quieres que lo cree primero?"

        instruccion = argumentos.get("instruccion", "")
        if not intent.es_misma_intencion_archivo(nombre, instruccion, self.llms["intencion"]):
            return "🎭 Esto no parece encajar con el archivo actual... puedo crear uno nuevo si quieres."
        resultado = self._editar_archivo_inteligente(nombre, instruccion)
        self.ultimo_archivo = nombre
        return resultado

    def _editar_archivo_inteligente(self, nombre, instruccion_usuario):
        try:
            with open(nombre, "r", encoding="utf-8") as f:
                contenido_actual = f.read()
        except Exception as e:
            return f"Error en edición: {str(e)}"

        nuevo_contenido = prompts.generar_edicion_archivo(
            self.llms["codigo"], contenido_actual, instruccion_usuario
        )
        return tools.editar_archivo(nombre, nuevo_contenido)

    # ─── Memoria explícita ───────────────────────────────────────────────────

    def _memoria_consultar(self, argumentos):
        return memory.consultar_memoria(self.usuario_data, self.memoria_larga)

    def _memoria_recordar(self, argumentos):
        contenido = argumentos.get("contenido", "").strip().lower()
        if not contenido:
            return "🎭 ¿Qué quieres que recuerde?"
        self.usuario_data = memory.agregar_nota(self.usuario_data, contenido)
        memory.guardar_usuario(self.usuario_data)
        return f"🧠 Anotado. Recordaré que {contenido}."

    def _memoria_olvidar(self, argumentos):
        objetivo = argumentos.get("objetivo", "")

        if objetivo == "todo":
            self.usuario_data = {}
            self.emocion.reiniciar()
            memory.guardar_usuario(self.usuario_data)
            self._olvidar_conversaciones()
            return "🧠 Hecho. He olvidado todo lo que sabía de ti."

        elif objetivo == "historial":
            self._olvidar_conversaciones()
            return "🧠 Historial borrado. Empezamos desde cero."

        elif objetivo in ("nombre", "rol", "intereses", "notas"):
            self.usuario_data = memory.olvidar_campo(self.usuario_data, objetivo)
            memory.guardar_usuario(self.usuario_data)
            return f"🧠 Listo. He olvidado tu {objetivo}."

        elif objetivo == "nota_especifica":
            fragmento = argumentos.get("fragmento", "").strip().lower()
            if not fragmento:
                return "🎭 ¿Qué nota quieres que olvide?"
            self.usuario_data, eliminadas = memory.olvidar_nota(self.usuario_data, fragmento)
            memory.guardar_usuario(self.usuario_data)
            if eliminadas > 0:
                return f"🧠 Listo. He olvidado lo relacionado con '{fragmento}'."
            return f"🧠 No encontré nada relacionado con '{fragmento}' en mi memoria."

        return "🎭 No entendí qué querías que olvidara."

    # ─── Ejecución de proyectos ──────────────────────────────────────────────

    def _flujo_ejecutar_proyecto(self, argumentos):
        """
        Flujo completo con confirmación.
        - Modo terminal: usa input() clásico
        - Modo web: usa self._confirmar_fn callback inyectado por app.py
        """
        descripcion = argumentos.get("descripcion", "")
        tipo        = argumentos.get("tipo", "otro")
        print(f"[DEBUG] Tipo de proyecto: {tipo}")

        plan            = prompts.generar_plan_proyecto(self.llms["codigo"], descripcion, tipo)
        nombre_proyecto = plan.get("nombre", "proyecto_cain")
        archivos        = plan.get("archivos", {})

        if not archivos:
            return "🎭 No pude generar el proyecto. ¿Puedes darme más detalles?"

        # Modo web: el proyecto lo abre el dispositivo que lo pidió (vía
        # self._abrir_fn de app.py), no el navegador de esta máquina.
        abrir_fn       = getattr(self, "_abrir_fn", None)
        lista_archivos = list(archivos.keys())
        comando        = executor.describir_comando(tipo, lista_archivos, abrir_en_pc=not abrir_fn)

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

        if hasattr(self, "_estado_fn") and self._estado_fn:
            self._estado_fn("ejecutando")

        resultado, url, info_error = executor.ejecutar_proyecto(
            nombre_proyecto, archivos, tipo, abrir_en_pc=not abrir_fn
        )

        if info_error:
            ruta_archivo, error = info_error
            resultado = executor.corregir_y_reintentar(self.llms["codigo"], ruta_archivo, error, resultado)

        if url and abrir_fn:
            abrir_fn(url)

        if url:
            return f"🎭 ¡El espectáculo está en vivo!\n\n{resultado}"
        return f"🎭 ¡Listo!\n\n{resultado}"

    # ─── Conversación ────────────────────────────────────────────────────────

    def _conversar(self, mensaje_usuario, canal="texto"):
        intencion = self._detectar_intencion(mensaje_usuario)
        print(f"[DEBUG] Intención detectada: {intencion}")

        self._actualizar_usuario(mensaje_usuario)

        prompt_sistema = prompts.construir_prompt(
            intencion, self.usuario_data, director.bloque_para_prompt(self.memoria_larga), canal,
            animo=self.emocion.describir(),
        )

        self.historial.append({"role": "user", "content": mensaje_usuario})
        mensajes = (
            [{"role": "system", "content": prompt_sistema}]
            + self.historial
            # Recordatorio al final: con un historial largo, la instrucción del
            # prompt de sistema queda lejos y el modelo deja de poner la etiqueta.
            + [{"role": "system", "content": prompts.RECORDATORIO_ANIMO}]
        )

        respuesta_cruda = self.llms["conversacion"].chat(mensajes, temperature=0.7)
        respuesta_texto, deltas = emocion.extraer_animo(respuesta_cruda)
        aplicados = self.emocion.aplicar(deltas)
        if aplicados:
            print(f"[DEBUG] Animo: {aplicados} -> {self.emocion.describir()}")

        # El historial guarda la respuesta CON la etiqueta: si no la ve en sus
        # respuestas anteriores, el modelo deja de ponerla. Al usuario, a la voz
        # y al director les llega siempre sin ella.
        self.historial.append({"role": "assistant", "content": respuesta_cruda})
        self.historial = memory.truncar_historial(self.historial)
        memory.guardar_memoria(self.historial)

        with self._lock_memoria:
            # Tope en el tamaño del historial: lo que se truncó sin pasar por el director ya no existe.
            self.mensajes_sin_resumir = min(self.mensajes_sin_resumir + 2, len(self.historial))
            pasada = None
            if self.mensajes_sin_resumir >= INTERVALO_DIRECTOR and not self._director_activo:
                pasada = self._preparar_director()
        # El hilo arranca fuera del lock: _correr_director también lo toma.
        if pasada:
            self._hilo_director = threading.Thread(target=self._correr_director, args=pasada, daemon=True)
            self._hilo_director.start()

        print(f"[DEBUG] Mensajes en memoria: {len(self.historial)}")
        return respuesta_texto

    # ─── Director de memoria (ver core/director.py) ──────────────────────────

    def _director_en_curso(self):
        return self._director_activo

    def _preparar_director(self):
        """Copia lo que necesita la pasada. Se llama con _lock_memoria tomado."""
        n = self.mensajes_sin_resumir
        # Solo los mensajes nuevos: los anteriores ya pasaron por el director.
        nuevos  = copy.deepcopy(self.historial[-n:])
        memoria = copy.deepcopy(self.memoria_larga)
        perfil  = copy.deepcopy(self.usuario_data)
        self.mensajes_sin_resumir = 0
        self._director_activo     = True
        return (memoria, perfil, nuevos, self._generacion_memoria)

    def _correr_director(self, memoria, perfil, nuevos, generacion):
        try:
            resultado = director.llamar_director(self.llms["director"], memoria, perfil, nuevos)
        except Exception as e:
            # La memoria es "mejor esfuerzo": un fallo aquí nunca tumba la conversación.
            print(f"[DEBUG] Director de memoria falló: {e}")
            resultado = None

        with self._lock_memoria:
            self._director_activo = False
            if generacion != self._generacion_memoria:
                print("[DEBUG] Director descartado: la memoria se borró mientras corría")
                return
            if resultado is None:
                # Esos mensajes vuelven a la cola para la próxima pasada.
                self.mensajes_sin_resumir = min(self.mensajes_sin_resumir + len(nuevos),
                                                len(self.historial))
                return
            director.aplicar_resultado(self.memoria_larga, resultado)
            memory.guardar_memoria_larga(self.memoria_larga)
        print("[DEBUG] Memoria a largo plazo actualizada por el director")

    def _olvidar_conversaciones(self):
        """Borra historial y memoria a largo plazo (no el perfil explícito)."""
        with self._lock_memoria:
            memory.limpiar_historial_completo()
            self.historial            = []
            self.memoria_larga        = memory.memoria_larga_vacia()
            self.mensajes_sin_resumir = 0
            self._generacion_memoria += 1

    # ─── Detección (delega en intent) ────────────────────────────────────────

    def _detectar_intencion(self, mensaje_usuario):
        return intent.detectar_intencion_llm(mensaje_usuario, self.llms["intencion"])

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

        intereses = intent.detectar_intereses_llm(mensaje_usuario, self.llms["intencion"])
        if intereses:
            if "intereses" not in self.usuario_data:
                self.usuario_data["intereses"] = []
            for i in intereses:
                if i not in self.usuario_data["intereses"]:
                    self.usuario_data["intereses"].append(i)
            memory.guardar_usuario(self.usuario_data)
            print(f"[DEBUG] Intereses guardados: {self.usuario_data['intereses']}")