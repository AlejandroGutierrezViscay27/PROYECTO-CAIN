from llm.fabrica import crear_llms
from llm.registro import RegistroUso

from core import memory, tools, intent, prompts, executor, director, emocion, arnes
from core.arnes import auditoria, reglas, revision_codigo, rutas
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

        # Todas pasan por _usar_herramienta (el arnés): ninguna se llama directo.
        # Las de nivel N2+ no actúan: devuelven una arnes.Accion a confirmar.
        self._herramientas = {
            "crear_archivo":     self._crear_archivo,
            "leer_archivo":      self._leer_archivo,
            "editar_archivo":    self._editar_archivo,
            "borrar_archivo":    self._borrar_archivo,
            "ejecutar_proyecto": self._preparar_proyecto,
            "memoria_recordar":  self._memoria_recordar,
            "memoria_olvidar":   self._preparar_olvido,
            "memoria_consultar": self._memoria_consultar,
        }

    # ─── Punto de entrada ────────────────────────────────────────────────────

    def chat(self, mensaje_usuario, canal="texto", origen="local"):
        """
        Procesa un mensaje del usuario y retorna la respuesta de CAIN.

        canal: "texto" o "voz". Con "voz" la respuesta se pide corta y sin
        formato, porque se va a sintetizar.
        origen: "local" (el propio PC) o "remoto" (otro dispositivo). El
        arnés limita lo que se puede pedir desde fuera.
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
            if nombre in self._herramientas:
                return self._usar_herramienta(nombre, argumentos, canal, origen)

        return self._conversar(mensaje_usuario, canal)

    # ─── Arnés: la única puerta hacia las herramientas ───────────────────────

    def _usar_herramienta(self, nombre, argumentos, canal="texto", origen="local"):
        veredicto = arnes.evaluar(nombre, argumentos, origen)
        registro  = {"argumentos": argumentos, "origen": origen, "canal": canal,
                     "nivel": veredicto.nombre_nivel}
        if not veredicto.permitido:
            auditoria.registrar("denegado", nombre, motivo=veredicto.motivo, **registro)
            return f"🛡️ No puedo hacer eso: {veredicto.motivo}."

        try:
            resultado = self._herramientas[nombre](argumentos)
            if isinstance(resultado, arnes.Accion):
                if veredicto.confirmar:
                    plan = {**resultado.confirmacion, "nivel": veredicto.nombre_nivel}
                    if not self._confirmar(plan):
                        auditoria.registrar("cancelado", nombre, **registro)
                        return resultado.al_cancelar
                resultado = resultado.ejecutar()
            elif veredicto.confirmar:
                # Un handler N2+ que devuelve texto no puede haber actuado
                # (falta un dato, el archivo no existe...): es una respuesta.
                auditoria.registrar("sin_accion", nombre, **registro)
                return resultado
        except arnes.Denegado as e:
            auditoria.registrar("denegado", nombre, motivo=str(e), **registro)
            return f"🛡️ No puedo hacer eso: {e}."
        except Exception as e:
            auditoria.registrar("error", nombre, motivo=f"{type(e).__name__}: {e}", **registro)
            raise

        auditoria.registrar("ejecutado", nombre, **registro)
        return resultado

    def _confirmar(self, plan):
        """
        Pide confirmación a quien hizo la petición.
        - Modo web: self._confirmar_fn, inyectado por app.py para ese turno.
        - Modo terminal: input().
        Solo un True explícito confirma.
        """
        confirmar_fn = getattr(self, "_confirmar_fn", None)
        if confirmar_fn:
            return confirmar_fn(plan) is True

        print(f"\nCAIN: 🛡️ Necesito tu confirmación ({plan.get('nivel')}):")
        if plan.get("clase") == "accion":
            print(f"      {plan.get('titulo', '')}")
            if plan.get("detalle"):
                print(f"      {plan['detalle']}")
        else:
            for a in plan.get("archivos", []):
                print(f"      📄 {a}")
            print(f"      📟 {plan.get('comando', '')}")
        for aviso in plan.get("advertencias", []):
            print(f"      ⚠️ {aviso}")
        respuesta = input("\n¿Procedo? (s/n): ").strip().lower()
        return respuesta in ("s", "si", "sí", "yes", "y")

    # ─── Herramientas de archivo (confinadas a espacio/) ─────────────────────

    def _ruta_en_espacio(self, argumentos, escritura=False):
        """Ruta resuelta del archivo pedido (o del último usado), o None si no hay nombre."""
        nombre = argumentos.get("nombre_archivo") or self.ultimo_archivo
        if not nombre:
            return None
        return rutas.resolver(tools.normalizar_nombre_txt(nombre), reglas.CARPETA_ESPACIO, escritura)

    def _mostrar(self, ruta):
        return rutas.para_mostrar(ruta, reglas.CARPETA_ESPACIO)

    def _crear_archivo(self, argumentos):
        nombre = argumentos.get("nombre_archivo") or tools.generar_nombre_timestamp()
        ruta   = self._ruta_en_espacio({"nombre_archivo": nombre}, escritura=True)
        ruta   = tools.evitar_sobrescritura(ruta)
        ok, error = tools.crear_archivo(ruta, argumentos.get("contenido", ""))
        if not ok:
            return f"Error al crear archivo: {error}"
        self.ultimo_archivo = ruta
        return f"🎭 He creado algo para este espectáculo...\nArchivo '{self._mostrar(ruta)}' creado correctamente."

    def _leer_archivo(self, argumentos):
        ruta = self._ruta_en_espacio(argumentos)
        if not ruta:
            return "🎭 ¿Qué archivo quieres que lea?"
        if not os.path.isfile(ruta):
            return f"🎭 No encontré el archivo '{self._mostrar(ruta)}'."
        contenido, recortado = tools.leer_archivo(ruta)
        self.ultimo_archivo = ruta
        aviso = "\n\n(… el archivo sigue, solo muestro el principio)" if recortado else ""
        return f"📖 Contenido de '{self._mostrar(ruta)}':\n\n{contenido}{aviso}"

    def _borrar_archivo(self, argumentos):
        ruta = self._ruta_en_espacio(argumentos)
        if not ruta:
            return "🎭 Necesito el nombre del archivo que deseas eliminar."
        if not os.path.isfile(ruta):
            return f"🎭 El archivo '{self._mostrar(ruta)}' no existe."
        visible = self._mostrar(ruta)

        def ejecutar():
            ok, error = tools.mover_a_papelera(ruta)
            if not ok:
                return f"Error al eliminar archivo: {error}"
            if ruta == self.ultimo_archivo:
                self.ultimo_archivo = None
            return f"🗑️ Archivo '{visible}' enviado a la Papelera de reciclaje."

        return arnes.Accion(ejecutar, {
            "clase":        "accion",
            "titulo":       f"Borrar '{visible}'",
            "detalle":      f"Va a la Papelera de reciclaje ({os.path.getsize(ruta)} bytes); se puede recuperar.",
            "advertencias": [],
        })

    def _editar_archivo(self, argumentos):
        ruta = self._ruta_en_espacio(argumentos, escritura=True)
        if not ruta:
            return "🎭 ¿A qué archivo te refieres?"
        if not os.path.isfile(ruta):
            return f"🎭 El archivo '{self._mostrar(ruta)}' no existe aún... ¿quieres que lo cree primero?"

        instruccion = argumentos.get("instruccion", "")
        if not intent.es_misma_intencion_archivo(ruta, instruccion, self.llms["intencion"]):
            return "🎭 Esto no parece encajar con el archivo actual... puedo crear uno nuevo si quieres."
        resultado = self._editar_archivo_inteligente(ruta, instruccion)
        self.ultimo_archivo = ruta
        return resultado

    def _editar_archivo_inteligente(self, ruta, instruccion_usuario):
        try:
            contenido_actual, recortado = tools.leer_archivo(ruta)
        except Exception as e:
            return f"Error en edición: {str(e)}"
        if recortado:
            # Editar solo el principio y guardarlo cortaría el resto del archivo.
            return "🎭 Ese archivo es demasiado grande para editarlo entero."

        nuevo_contenido = prompts.generar_edicion_archivo(
            self.llms["codigo"], contenido_actual, instruccion_usuario
        )
        copia = tools.respaldar(ruta, reglas.CARPETA_ESPACIO)
        ok, error = tools.editar_archivo(ruta, nuevo_contenido)
        if not ok:
            return f"Error en edición: {error}"
        return (f"✏️ Archivo '{self._mostrar(ruta)}' actualizado.\n"
                f"(La versión anterior quedó en '{self._mostrar(copia)}'.)")

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

    def _preparar_olvido(self, argumentos):
        """'todo' e 'historial' no tienen vuelta atrás: se confirman (N3)."""
        objetivo = argumentos.get("objetivo", "")
        if objetivo not in ("todo", "historial"):
            return self._memoria_olvidar(argumentos)
        que = ("todo lo que sé de ti: perfil, notas, historial y memoria a largo plazo"
               if objetivo == "todo" else "el historial de conversación y la memoria a largo plazo")
        return arnes.Accion(lambda: self._memoria_olvidar(argumentos), {
            "clase":        "accion",
            "titulo":       "Borrar memoria" if objetivo == "todo" else "Borrar historial",
            "detalle":      f"Se borra {que}. No se puede deshacer.",
            "advertencias": [],
        }, al_cancelar="🧠 Entendido, no olvido nada.")

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

    def _preparar_proyecto(self, argumentos):
        """
        Genera el plan (sin escribir nada) y lo devuelve como Accion: el
        arnés lo confirma con quien lo pidió y solo entonces se ejecuta.
        """
        descripcion = argumentos.get("descripcion", "")
        tipo        = argumentos.get("tipo", "otro")
        print(f"[DEBUG] Tipo de proyecto: {tipo}")

        plan            = prompts.generar_plan_proyecto(self.llms["codigo"], descripcion, tipo)
        nombre_proyecto = executor.nombre_seguro(plan.get("nombre", "proyecto_cain"))
        archivos        = plan.get("archivos", {})

        if not archivos or not isinstance(archivos, dict):
            return "🎭 No pude generar el proyecto. ¿Puedes darme más detalles?"

        # Antes de confirmar: ningún archivo puede salirse de su carpeta y el
        # código no puede nombrar rutas prohibidas (ambos lanzan Denegado).
        executor.validar_archivos(archivos)
        advertencias = revision_codigo.revisar_proyecto(archivos)

        # Modo web: el proyecto lo abre el dispositivo que lo pidió (vía
        # self._abrir_fn de app.py), no el navegador de esta máquina.
        abrir_fn       = getattr(self, "_abrir_fn", None)
        lista_archivos = list(archivos.keys())
        comando        = executor.describir_comando(tipo, lista_archivos, abrir_en_pc=not abrir_fn)

        def ejecutar():
            if getattr(self, "_estado_fn", None):
                self._estado_fn("ejecutando")

            resultado, url, info_error = executor.ejecutar_proyecto(
                nombre_proyecto, archivos, tipo, abrir_en_pc=not abrir_fn
            )

            if info_error:
                ruta_archivo, error = info_error
                resultado = executor.corregir_y_reintentar(
                    self.llms["codigo"], ruta_archivo, error, resultado, advertencias_confirmadas=advertencias
                )

            if url and abrir_fn:
                abrir_fn(url)

            if url:
                return f"🎭 ¡El espectáculo está en vivo!\n\n{resultado}"
            return f"🎭 ¡Listo!\n\n{resultado}"

        return arnes.Accion(ejecutar, {
            "clase":        "proyecto",
            "nombre":       nombre_proyecto,
            "archivos":     lista_archivos,
            "comando":      comando,
            "advertencias": advertencias,
        }, al_cancelar="🎭 Entendido, cancelado. Dime cuando quieras intentarlo de nuevo.")

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