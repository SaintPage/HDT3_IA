# Agente de FAQs — Parachute S.A. (RAG simple)

**Hoja de Trabajo #3 — Sistemas RAG — CC3116**

Agente de terminal que responde preguntas sobre el evento de paracaidismo del
29 de septiembre de 2026, usando **únicamente** la información del archivo
`data/FAQs_Parachute_SA_Guatemala_2026.txt`.

---

## Arquitectura

```
  data/FAQs_...txt          main.py                    API OpenAI-compatible
 ┌──────────────┐      ┌──────────────────┐            ┌──────────────────┐
 │ Base de      │─────▶│ cargar_base_     │            │  Groq / NVIDIA / │
 │ conocimiento │      │ conocimiento()   │            │  OpenAI          │
 │ (file system)│      │        │         │            │                  │
 └──────────────┘      │        ▼         │            │  gpt-oss-120b    │
                       │ construir_system │──mensajes─▶│                  │
   usuario ──pregunta─▶│ _prompt()        │◀─respuesta─│                  │
                       │        │         │            └──────────────────┘
                       │        ▼         │
                       │ loop conversac.  │
                       │ (historial)      │
                       └──────────────────┘
```

Es la variante más simple de RAG: el paso de **retrieval** es trivial —el
documento completo (≈4.6 KB) cabe holgadamente en la ventana de contexto, así
que se recupera entero— y el paso de **augmentation** consiste en inyectarlo en
el *system prompt* delimitado por marcadores explícitos. La **generación** la
hace el LLM remoto, restringido por reglas que le prohíben usar conocimiento
externo.

`cargar_base_conocimiento()` está aislada a propósito: para escalar a cientos
de documentos bastaría sustituirla por *chunking* + embeddings + búsqueda
vectorial, sin tocar el resto del programa.

### Cómo se cumple cada requisito

| Requisito | Implementación |
|---|---|
| Responder solo con el archivo | Regla 1 del system prompt + `temperature=0.1` |
| Admitir cuando no sabe | Regla 2: frase de rechazo literal predefinida |
| Múltiples preguntas por sesión | `while True` con historial de conversación |
| Salir con "Bye" | `EXIT_WORDS` (case-insensitive) |
| Salir con Ctrl-C | `except KeyboardInterrupt` en el `input()` |
| No pushear API Keys | `.env` en `.gitignore`; solo se versiona `.env.example` |

---

## Uso

```bash
python main.py
```

```
==================================================================
   PARACHUTE S.A. - Agente de Preguntas Frecuentes (Demo RAG)
==================================================================

Tu > ¿Cuál es el límite de peso para saltar?

Agente > El límite de peso máximo es de 100 kg (220 lbs). Todos los
participantes son pesados en el área de registro antes del salto por
razones de seguridad.

Tu > Bye

Agente > Bye! Nos vemos el 29 de septiembre. Cielos despejados.
```

## Estructura

```
parachute-rag/
├── data/
│   └── FAQs_Parachute_SA_Guatemala_2026.txt
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
## Enlace al vídeo:

https://youtu.be/TZUrX6D1sAY