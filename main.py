#!/usr/bin/env python3
"""
Agente de Preguntas Frecuentes - Parachute S.A.
Hoja de Trabajo #3 (Sistemas RAG) - CC3116

Arquitectura RAG simple:

    [ FAQs.txt en el file system ]
                |
                v
    [ carga en memoria (retrieval trivial: todo el documento) ]
                |
                v
    [ inyeccion del contexto en el system prompt ]
                |
                v
    [ LLM via API compatible con el esquema de OpenAI ]
                |
                v
    [ respuesta anclada unicamente en el documento ]

El agente responde SOLO con informacion del archivo. Si la pregunta no
esta cubierta, admite que no puede responderla.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

# Configuracion (la API Key NUNCA se escribe en el codigo: viene del .env)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
KB_PATH = Path(
    os.getenv("KB_PATH", BASE_DIR / "data" / "FAQs_Parachute_SA_Guatemala_2026.txt")
)

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
MAX_HISTORY = 12  # ultimos N mensajes de la conversacion que se reenvian

EXIT_WORDS = {"bye", "adios", "adios.", "salir", "exit", "quit"}

SYSTEM_TEMPLATE = """Eres el asistente virtual oficial de Parachute S.A., una \
empresa guatemalteca de paracaidismo. Tu unica funcion es responder preguntas \
sobre el evento del 29 de septiembre de 2026.

REGLAS ESTRICTAS:
1. Responde EXCLUSIVAMENTE con informacion contenida en el DOCUMENTO DE \
REFERENCIA delimitado abajo. No uses conocimiento externo ni supongas datos.
2. Si la respuesta no esta en el documento, responde exactamente:
   "Lo siento, no tengo esa informacion en las preguntas frecuentes de \
Parachute S.A. Puedes escribir a info@parachutesa.gt o al WhatsApp \
+502 2300-0000 para ayudarte con esa consulta."
   No inventes, no estimes y no completes con datos plausibles.
3. No hagas calculos, recomendaciones medicas ni excepciones a las reglas del \
evento que no aparezcan en el documento.
4. Responde en el mismo idioma en que te pregunte el usuario (por defecto, \
espanol), de forma breve, clara y cordial.
5. Puedes usar el historial de la conversacion para entender preguntas de \
seguimiento, pero el contenido factual siempre proviene del documento.

===== DOCUMENTO DE REFERENCIA (BASE DE CONOCIMIENTO) =====
{contexto}
===== FIN DEL DOCUMENTO DE REFERENCIA =====
"""

BANNER = """
==================================================================
   PARACHUTE S.A. - Agente de Preguntas Frecuentes (Demo RAG)
   Evento: 29 de septiembre de 2026 | Puerto San Jose, Escuintla
------------------------------------------------------------------
   Modelo: {model}
   Base de conocimiento: {kb} ({chars} caracteres)
------------------------------------------------------------------
   Escribe tu pregunta y presiona Enter.
   Escribe "Bye" o presiona Ctrl-C para salir.
==================================================================
"""


# Capa de "retrieval": en esta arquitectura minima el documento completo es
# el contexto recuperado. Se aisla en una funcion para poder sustituirla
# luego por busqueda semantica / vector store sin tocar el resto del codigo.
def cargar_base_conocimiento(ruta: Path) -> str:
    if not ruta.is_file():
        sys.exit(
            f"[ERROR] No se encontro la base de conocimiento en: {ruta}\n"
            f"        Coloca el archivo .txt en esa ruta o define KB_PATH en el .env."
        )
    contenido = ruta.read_text(encoding="utf-8").strip()
    if not contenido:
        sys.exit(f"[ERROR] El archivo {ruta} esta vacio.")
    return contenido


def construir_system_prompt(contexto: str) -> str:
    return SYSTEM_TEMPLATE.format(contexto=contexto)


def crear_cliente() -> OpenAI:
    if not API_KEY:
        sys.exit(
            "[ERROR] Falta la variable OPENAI_API_KEY.\n"
            "        Copia .env.example a .env y coloca ahi tu API Key.\n"
            "        (Recuerda: el .env esta en .gitignore, nunca se sube al repo.)"
        )
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def preguntar(cliente: OpenAI, mensajes: list[dict]) -> str:
    respuesta = cliente.chat.completions.create(
        model=MODEL,
        messages=mensajes,
        temperature=TEMPERATURE,
    )
    return respuesta.choices[0].message.content.strip()


# Loop principal: multiples preguntas en una sola sesion
def main() -> None:
    contexto = cargar_base_conocimiento(KB_PATH)
    cliente = crear_cliente()

    system_prompt = construir_system_prompt(contexto)
    historial: list[dict] = []

    print(BANNER.format(model=MODEL, kb=KB_PATH.name, chars=len(contexto)))

    while True:
        try:
            pregunta = input("\nTu > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSesion terminada. Gracias por usar el agente de Parachute S.A.")
            break

        if not pregunta:
            continue

        if pregunta.lower() in EXIT_WORDS:
            print("\nAgente > Bye! Nos vemos el 29 de septiembre. Cielos despejados.")
            break

        historial.append({"role": "user", "content": pregunta})
        mensajes = [{"role": "system", "content": system_prompt}] + historial[-MAX_HISTORY:]

        try:
            respuesta = preguntar(cliente, mensajes)
        except OpenAIError as exc:
            print(f"\n[ERROR de API] {exc}")
            historial.pop()  # no dejamos la pregunta sin respuesta en el historial
            continue

        historial.append({"role": "assistant", "content": respuesta})
        print(f"\nAgente > {respuesta}")


if __name__ == "__main__":
    main()
