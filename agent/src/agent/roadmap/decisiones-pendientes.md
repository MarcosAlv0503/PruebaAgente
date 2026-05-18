# Decisiones pendientes

Decisiones aún por cerrar; bloquean a la siguiente fase si no se resuelven. Cuando una decisión se cierra, se mueve a `docs/00_DECISIONES.md` como ADR y desaparece de aquí.

## D1 — Estrategia RAG: tsvector vs pgvector

- **Contexto:** El MVP usa keyword search en ficheros .md (`kb_client.py`). Con alta volumetría de KB o incidencias ambiguas, el recall será bajo. Decidir cuándo y cómo migrar a búsqueda semántica.
- **Opciones:**
  - A. Mantener keyword search hasta tener datos reales de recall (recomendado para v0.1.x).
  - B. Ingestar KB en Postgres con `tsvector` (sin deps extra, mejor que keyword puro).
  - C. Migrar a `pgvector` con embeddings (máxima calidad, requiere llamada a embeddings API en ingesta).
- **Bloquea:** calidad del `search_knowledge_base` tool.
- **Owner:** Tech Lead.
- **Deadline:** tras primer mes de producción real con datos de recall.

## D2 — Persistencia de logs y tickets en v0.2.0

- **Contexto:** Los logs y tickets van a filesystem `/Documentos/` en v0.1.x. No es persistente en Fly.io. Migrar a Postgres (`audit_log` + `issues` tables) en v0.2.0.
- **Opciones:**
  - A. Migrar completamente a Postgres y eliminar storage_client.py de filesystem.
  - B. Doble escritura: filesystem + Postgres (para compatibilidad con herramientas que leen el filesystem).
- **Bloquea:** operación en Fly.io con persistencia real.
- **Owner:** Tech Lead.
- **Deadline:** Sprint 1 de v0.2.0.

## D3 — Chat del dashboard: polling vs Server-Sent Events (SSE)

- **Contexto:** El chat del dashboard necesita mostrar la respuesta del agente cuando el worker la procesa. En Sprint 4, el frontend necesita saber cuándo está lista la respuesta.
- **Opciones:**
  - A. Polling (`GET /api/incidents/{id}` cada 2s) — simple, suficiente para MVP.
  - B. Server-Sent Events desde FastAPI — más eficiente, más complejo.
- **Bloquea:** Sprint 4 (dashboard/chat/).
- **Owner:** Tech Lead.
- **Deadline:** antes de Sprint 4.
