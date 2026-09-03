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
