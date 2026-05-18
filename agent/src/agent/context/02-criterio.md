# Criterio de éxito y de fallo

## Cuándo se considera éxito (resolución automática)

- El output valida contra `output.schema.json` sin errores.
- `auto_resolved=true` y `classification.confidence >= CONFIDENCE_THRESHOLD` (default 0.75).
- `kb_refs` contiene al menos un documento relevante de `agent/knowledge/`.
- `final_response` es una respuesta accionable, no genérica.
- El log `.txt` se ha escrito correctamente en `/Documentos/logs/`.
- El operador puede ver la respuesta en el chat del dashboard.

## Cuándo se considera éxito con escalación

- `auto_resolved=false` con motivo explícito en `escalation_reason`.
- El ticket `.txt` se ha escrito en `/Documentos/tickets/` con todos los campos obligatorios: `summary`, `priority`, `context`, `escalation_reason`, `suggested_steps`.
- La respuesta en el chat informa al operador de la escalación de forma clara e indica el número de ticket.
- El log `.txt` se ha escrito correctamente.

## Cuándo se considera fallo recuperable

- `agent/knowledge/` está vacío o los archivos no son legibles en el momento de la ejecución: el worker puede reintentarse una vez tras un intervalo de espera.
- Error de base de datos al verificar duplicados (`psycopg.Error` transitorio): reintentable con backoff.
- Error transitorio del modelo LLM (timeout, HTTP 429 rate-limit): reintentable con backoff exponencial, máximo 3 intentos.

## Cuándo se considera fallo no recuperable

- El mensaje de entrada no supera la validación básica (vacío, longitud > 2000 caracteres, `customer_id` inválido): falla inmediata, no reintenta, `status='failed'`.
- La ejecución es detectada como duplicada por `external_id`: falla silenciosa, no procesa, `status='skipped'`.
- El coste supera el circuit breaker (`loang_toolkit.CircuitBreakerError`): `status='failed'`, `error='budget_exceeded'`.
- El output del LLM no valida contra `output.schema.json` tras 2 reintentos de parseo: `status='failed'`, `error='invalid_output'`.
- HTTP 4xx del cliente OpenRouter (payload inválido): no reintenta, `status='failed'`.

## Cuándo escalar a humano

- Severidad `critical` siempre, independientemente de la confianza del clasificador.
- `classification.confidence < CONFIDENCE_THRESHOLD` (env `CONFIDENCE_THRESHOLD`, default 0.75).
- La búsqueda en KB devuelve `kb_results` vacío para el tipo de incidencia.
- El modelo `phase_light_llm` señala `needs_heavy=True` por cualquier razón.
- El modelo `phase_heavy_llm` tampoco puede clasificar el tipo de incidencia con certeza razonable: genera ticket con `escalation_reason='unclassifiable'`.
