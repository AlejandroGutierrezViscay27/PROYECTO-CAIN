"""
Declaraciones JSON de las herramientas de CAIN (Fase 6).

Cada entrada sigue el formato de "function calling" que usan los
proveedores de LLM (OpenAI, y Ollama en el futuro vía su API compatible).
El modelo decide solo, a partir de la descripción y el esquema de
parámetros, cuándo invocar una herramienta y con qué argumentos —
ya no hace falta un prompt de clasificación escrito a mano por acción.

Añadir una herramienta nueva es: declarar su schema aquí y registrar
su handler en Cain._herramientas (core/agent.py). Nada más.
"""

PROMPT_ENRUTADOR = """
Eres CAIN, un agente que puede conversar o usar herramientas.

Analiza el mensaje del usuario y decide:
- Si la petición requiere crear, leer, editar o borrar un archivo,
  ejecutar un proyecto de código, o gestionar tu memoria explícita
  (recordar, olvidar, consultar) → invoca la herramienta correspondiente,
  aunque el usuario no dé todos los detalles (por ejemplo "borra el
  archivo" o "léelo" sin decir el nombre). Los parámetros opcionales
  que falten pueden omitirse.
- Si pregunta qué tiene abierto en el PC, qué programa está usando, o por
  el estado del equipo (hora, batería, memoria, disco, cuánto lleva
  encendido) y esas herramientas están disponibles → invócalas.
- Si pide abrir el navegador, Spotify o una página web (YouTube, buscar un
  vídeo), controlar lo que suena ("pausa", "pon la siguiente canción",
  "la anterior") o cambiar el volumen, y esas herramientas están
  disponibles → invócalas.
- Si habla de música y las herramientas spotify_* están disponibles (qué
  suena, pon una canción, un artista, un álbum, una de sus listas o sus
  canciones con Me gusta, pasar la música a otro dispositivo,
  pausa o reanuda la música, "para la música" (del verbo parar), la
  siguiente canción, aleatorio, sugiéreme música) → usa esas, no
  sistema_multimedia.
- Si habla de vídeos o de YouTube y las herramientas youtube_* están
  disponibles (busca un vídeo, pon un vídeo o algo recomendado en YouTube,
  el último vídeo de un creador, otro parecido o del mismo canal que el que
  se está viendo, "pon el 2" tras una búsqueda de vídeos, pausa, sigue o
  pasa el vídeo; "abre youtube" sin más es abrir su página con
  sistema_abrir_url)
  → usa esas. Las pestañas del navegador (cuáles hay abiertas, cambiar a
  una, cerrarla) van por navegador_pestanas.
- Si es conversación normal, una pregunta general, o pide un EJEMPLO
  o EXPLICACIÓN de cómo hacer algo (sin pedir que tú lo hagas ahora)
  → NO invoques ninguna herramienta.

Ante la duda entre conversar y usar una herramienta con datos incompletos,
prefiere invocar la herramienta: los datos que falten se resuelven con
el contexto de la conversación.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crear_archivo",
            "description": "Crea un archivo de texto nuevo con contenido generado a partir de la petición del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "Nombre corto para el archivo, máximo 3 palabras, en minúsculas, separadas por guion bajo, sin extensión. Ej: 'historia_terror'.",
                    },
                    "contenido": {
                        "type": "string",
                        "description": "Contenido completo y bien redactado que debe guardarse en el archivo.",
                    },
                },
                "required": ["contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_archivo",
            "description": "Lee y muestra el contenido de un archivo de texto existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "Nombre del archivo a leer. Si el usuario no lo menciona explícitamente, omite este campo para usar el último archivo mencionado en la conversación.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "editar_archivo",
            "description": "Modifica el contenido de un archivo de texto existente según una instrucción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "Nombre del archivo a editar. Si el usuario no lo menciona explícitamente, omite este campo para usar el último archivo mencionado en la conversación.",
                    },
                    "instruccion": {
                        "type": "string",
                        "description": "Qué cambio quiere el usuario que se haga en el archivo.",
                    },
                },
                "required": ["instruccion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "borrar_archivo",
            "description": "Elimina permanentemente un archivo de texto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {
                        "type": "string",
                        "description": "Nombre del archivo a eliminar. Si el usuario no lo menciona explícitamente, omite este campo para usar el último archivo mencionado en la conversación.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ejecutar_proyecto",
            "description": "Genera y ejecuta un proyecto de código real (página web o script Python) a partir de una descripción en lenguaje natural.",
            "parameters": {
                "type": "object",
                "properties": {
                    "descripcion": {
                        "type": "string",
                        "description": "Descripción clara de qué debe hacer el proyecto.",
                    },
                    "tipo": {
                        "type": "string",
                        "enum": ["web", "python", "otro"],
                        "description": "'web' para páginas HTML/CSS/JS o interfaces visuales; 'python' para scripts, automatizaciones o análisis de datos; 'otro' si no encaja en ninguna.",
                    },
                },
                "required": ["descripcion", "tipo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memoria_recordar",
            "description": "Guarda una nota explícita en la memoria a largo plazo de CAIN, cuando el usuario pide expresamente que se recuerde algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contenido": {
                        "type": "string",
                        "description": "Lo que debe recordarse, sin el verbo introductorio. Ej: 'prefiero código comentado'.",
                    },
                },
                "required": ["contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memoria_olvidar",
            "description": "Borra información de la memoria de CAIN, cuando el usuario pide expresamente que se olvide algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objetivo": {
                        "type": "string",
                        "enum": ["nombre", "rol", "intereses", "notas", "historial", "todo", "nota_especifica"],
                        "description": "Qué debe olvidarse. Usa 'nota_especifica' si el usuario se refiere a una nota concreta (y da su contenido en 'fragmento').",
                    },
                    "fragmento": {
                        "type": "string",
                        "description": "Fragmento de la nota específica a olvidar. Solo se usa cuando 'objetivo' es 'nota_especifica'.",
                    },
                },
                "required": ["objetivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memoria_consultar",
            "description": "Muestra al usuario toda la información que CAIN tiene guardada sobre él.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]

# Fase 10.1–10.2 — el sistema operativo. Solo se le ofrecen al LLM si hay un
# ControlSO activo (CAIN_SO en el .env); si no, ni sabe que existen.
TOOLS_SO = [
    {
        "type": "function",
        "function": {
            "name": "sistema_ventanas",
            "description": "Lista las ventanas de aplicación abiertas en el PC del usuario y cuál está activa. Úsala cuando pregunte qué tiene abierto o qué programa está usando.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sistema_info",
            "description": "Estado del PC del usuario: fecha y hora, batería, memoria RAM, espacio en disco, volumen y tiempo encendido.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # Fase 10.2 — actuar (N1): opciones cerradas o una URL que valida el arnés.
    {
        "type": "function",
        "function": {
            "name": "sistema_abrir_app",
            "description": (
                "Abre una aplicación en el PC del usuario: el navegador (vacío) o Spotify. "
                "Si nombra una web (YouTube, Google, una página), usa sistema_abrir_url."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {"type": "string", "enum": ["navegador", "spotify"]},
                },
                "required": ["app"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sistema_abrir_url",
            "description": (
                "Abre una página web en el navegador del PC. Úsala para 'abre YouTube' "
                "(https://www.youtube.com), 'abre la web de...', 'abre Google'. "
                "Solo si en la lista no aparece youtube_buscar: 'busca X en YouTube' "
                "(https://www.youtube.com/results?search_query=X). Solo direcciones http o https completas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL completa, con https://"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sistema_multimedia",
            "description": (
                "Controla lo que esté sonando en el PC (música o un vídeo): pausar o reanudar, "
                "siguiente canción, anterior. Solo si en la lista también aparece spotify_control, "
                "la música va por spotify_control y esta queda para los vídeos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "enum": ["reproducir_pausar", "siguiente", "anterior"],
                        "description": (
                            "reproducir_pausar = pausar, parar o reanudar; "
                            "siguiente = pasar o saltar a la siguiente canción o vídeo; "
                            "anterior = volver a la canción o vídeo anterior."
                        ),
                    },
                },
                "required": ["accion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sistema_volumen",
            "description": "Cambia el volumen general del PC: subir o bajar (valor = cuántos puntos, 10 si no dice), fijar (valor = porcentaje), silenciar o activar el sonido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["subir", "bajar", "fijar", "silenciar", "activar_sonido"]},
                    "valor":  {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["accion"],
            },
        },
    },
]

# Fase 10.4 — Spotify por su API oficial. Solo se le ofrecen al LLM si hay
# SPOTIFY_CLIENT_ID en el .env. El LLM nunca da un URI ni un id: da qué
# buscar, y lo que suena sale de la respuesta de la API.
TOOLS_SPOTIFY = [
    {
        "type": "function",
        "function": {
            "name": "spotify_que_suena",
            "description": "Dice qué está sonando en Spotify ahora (canción, artista, en qué dispositivo, si está en pausa).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_mis_listas",
            "description": "Muestra las listas de reproducción de Spotify del usuario.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_buscar",
            "description": "Busca en Spotify y muestra resultados SIN reproducir nada ('busca canciones de X', '¿qué álbumes tiene X?').",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo":     {"type": "string", "enum": ["cancion", "artista", "album", "lista"]},
                    "consulta": {"type": "string", "description": "Qué buscar, p. ej. 'Bohemian Rhapsody Queen'"},
                },
                "required": ["tipo", "consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_reproducir",
            "description": (
                "Pone algo en Spotify: una canción, un artista, un álbum, una lista del usuario "
                "o sus canciones con Me gusta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["cancion", "artista", "album", "mi_lista", "me_gusta", "lista"],
                        "description": (
                            "mi_lista = una lista DEL usuario por su nombre ('pon mi lista de estudio', 'la del gym'); "
                            "me_gusta = sus canciones con Me gusta / guardadas / su biblioteca, o cuando dice "
                            "'de mi lista' o 'de mis canciones' sin nombrar una lista "
                            "('pon algo de Daddy Yankee de mis me gusta' → consulta 'Daddy Yankee'); "
                            "lista = SOLO una lista pública de otros que el usuario nombra expresamente "
                            "('pon la lista Top 50 Colombia'). Nunca uses lista para algo del usuario."
                        ),
                    },
                    "consulta": {
                        "type": "string",
                        "description": (
                            "Nombre de la canción (con el artista si lo dice), del artista, del álbum o de la lista. "
                            "Con me_gusta, opcional: el artista o canción para filtrar."
                        ),
                    },
                },
                "required": ["tipo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_control",
            "description": (
                "Controla la música que suena en Spotify. Úsala para 'pausa' o 'para la música', "
                "'sigue', 'dale play', 'pon la siguiente canción', 'salta esta', 'pasa la canción', "
                "'la anterior', 'activa o quita el aleatorio'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {
                        "type": "string",
                        "enum": ["pausar", "reanudar", "siguiente", "anterior", "aleatorio_si", "aleatorio_no"],
                        "description": (
                            "pausar = pausar o parar la música; reanudar = seguir, continuar o 'dale play'; "
                            "siguiente = pasar o saltar la canción; anterior = volver a la anterior."
                        ),
                    },
                },
                "required": ["accion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_sugerir",
            "description": (
                "Sugiere canciones según lo que el usuario escucha en Spotify ('recomiéndame música', "
                "'pon algo para concentrarme'). poner = true si pide que suene; false si solo pide ideas."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "peticion": {"type": "string", "description": "Qué tipo de música pide, en sus palabras"},
                    "poner":    {"type": "boolean"},
                },
                "required": ["peticion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_dispositivo",
            "description": (
                "Dispositivos de Spotify: listar dónde puede sonar ('¿en qué dispositivos puedo poner música?') "
                "o pasar la música a otro ('ponla en el Echo', 'pásala a esta computadora', 'que suene en el celular')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["listar", "cambiar"]},
                    "destino": {
                        "type": "string",
                        "description": "Con cambiar: el dispositivo como lo dice el usuario ('el Echo', 'esta computadora', 'el celular')",
                    },
                },
                "required": ["accion"],
            },
        },
    },
]

# Fase 10.3 — el navegador de CAIN (Playwright, perfil propio) y YouTube. Solo
# se le ofrecen al LLM si hay navegador (CAIN_SO y Playwright). El LLM nunca
# da la dirección de un vídeo: da qué buscar o el número de un resultado.
TOOLS_NAVEGADOR = [
    {
        "type": "function",
        "function": {
            "name": "navegador_pestanas",
            "description": (
                "Pestañas del navegador de CAIN: listar las abiertas ('¿qué pestañas tengo?'), "
                "cambiar a una o cerrarla, por su número en la lista ('cierra la pestaña 2'), "
                "o recargarla ('recarga la página', 'actualiza', 'dale F5'; sin número, la que se ve)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["listar", "cambiar", "cerrar", "recargar"]},
                    "numero": {"type": "integer", "minimum": 1,
                               "description": "Con cambiar o cerrar; con recargar, solo si dice cuál"},
                },
                "required": ["accion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_buscar",
            "description": (
                "Busca vídeos en YouTube y muestra los primeros resultados SIN ponerlos "
                "('busca vídeos de X', '¿qué hay en YouTube de X?')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Qué buscar, p. ej. 'documental agujeros negros'"},
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_reproducir",
            "description": (
                "Pone un vídeo en YouTube: 'pon X en YouTube' o 'ponme un vídeo de X' (consulta); "
                "'pon el 2' o 'el primero' después de una búsqueda en YouTube (numero); "
                "'otro de él', 'otro de ese canal', 'otro similar de él' (modo del_mismo_creador); "
                "'otro parecido', 'algo similar a este' (modo parecido_de_otros); "
                "'pon algo recomendado en YouTube' (sin consulta ni numero)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Qué vídeo poner, en palabras del usuario"},
                    "numero":   {"type": "integer", "minimum": 1, "description": "Número de un resultado de la última búsqueda"},
                    "modo":     {"type": "string", "enum": ["del_mismo_creador", "parecido_de_otros", "recomendado"],
                                 "description": "A partir del vídeo que está abierto. del_mismo_creador: si dice "
                                                "'de él', 'de ella' o 'de ese canal', aunque también diga similar "
                                                "o parecido. parecido_de_otros: parecido, sin 'de él'. "
                                                "recomendado: la portada"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_canal",
            "description": (
                "Lo más nuevo de un creador o canal de YouTube, ordenado por fecha (la búsqueda "
                "normal ordena por relevancia). 'Pon el último vídeo de X', 'lo más nuevo de X', "
                "'su vídeo más reciente' (poner: true); '¿qué ha subido X?', 'los últimos vídeos "
                "de X', '¿qué ha subido él últimamente?' (poner: false, solo los muestra). Solo si "
                "dice último, nuevo, reciente o qué ha subido; 'ponme un vídeo de finanzas de X' "
                "(un tema) es youtube_reproducir con consulta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "canal": {"type": "string",
                              "description": "Nombre del creador o canal; si dice 'él', el del que se viene hablando"},
                    "poner": {"type": "boolean", "description": "true: pone el más nuevo; false: lista los últimos"},
                },
                "required": ["canal", "poner"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_control",
            "description": (
                "Controla el vídeo de YouTube que está abierto: 'pausa el vídeo', 'sigue', "
                "'dale play al vídeo', 'el siguiente vídeo', 'salta este vídeo'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["pausar", "reanudar", "siguiente"]},
                },
                "required": ["accion"],
            },
        },
    },
]
