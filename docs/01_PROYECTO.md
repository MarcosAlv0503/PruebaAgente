# Proyecto: loang-ecommerce-support-agent

## Cliente

- **Tipo:** tiendas ecommerce de ropa (cliente externo de Grupo Loang IA).
- **Usuario final:** equipos operativos y técnicos de la tienda que gestionan incidencias web.
- **Sponsor:** Tech Lead Loang IA.

## Problema

Los equipos operativos de tiendas ecommerce reciben incidencias técnicas y funcionales (checkout roto, imágenes sin cargar, cupones que fallan, problemas de login) que hoy requieren revisión manual continua. Sin automatización:

- Tiempo de reacción elevado — el operador tiene que leer, entender y buscar solución manualmente.
- Sin trazabilidad estructurada — los logs son informales o inexistentes.
- Sin priorización automática — una incidencia crítica (checkout caído) compite con una menor (precio mal mostrado).
- Conocimiento no centralizado — las soluciones documentadas están dispersas y son de difícil acceso.

## Capacidades × modo

| Capacidad | Descripción | Modo |
|---|---|---|
| Clasificación | Detecta tipo y severidad del mensaje de incidencia | Pipeline automático |
| Resolución KB | Busca solución documentada y responde en el chat | Pipeline automático |
| Generación de ticket | Crea ticket estructurado cuando no puede resolver | Pipeline automático con output humano |
| Trazabilidad | Genera log estructurado de cada incidencia procesada | Pipeline automático |

**No aplica modo conversacional** en v0.1.x — cada mensaje es una ejecución independiente.

## Volumetría asumida

| Métrica | Valor | Fuente |
|---|---|---|
| Incidencias por día (estimado inicial) | 10–50 | declarado por el cliente |
| Tiempo de respuesta objetivo | < 30 s por incidencia | objetivo |
| Tasa de resolución automática objetivo | ≥ 75 % | objetivo de la métrica de éxito |
| Documentos en KB (arranque) | 10–30 | estimado inicial |

## Stakeholders

- **Operadores de la tienda:** reportan incidencias en el chat del dashboard y leen la respuesta del agente.
- **Tech Lead Loang IA:** valida arquitectura y roadmap.
- **Equipo Loang IA:** mantiene el agente, la KB y el dashboard.

## Alcance v0.1.x (MVP)

### Sprint 0 — Documentación y schemas ✅ completado 2026-05-12

- Misión, criterios, dominio, modelos y schemas definidos.
- Arquitectura validada.

### Sprint 1 — Fases del agente (en curso)

- `phase_deterministic`: validación, dedup, keywords, severidad por heurística.
- `phase_light_llm`: clasificación con haiku, búsqueda KB por keyword, respuesta o routing a heavy.
- `phase_heavy_llm`: análisis con sonnet, generación de ticket estructurado.
- Worker real invocando `graph.run`.
- Dispatcher que verifica `ALLOWED_TOOLS_BY_PHASE`.
- `make test` verde con casos golden.

### Sprint 2 — KB y búsqueda

- `agent/knowledge/` con documentos reales de la tienda.
- `kb_client.py` con keyword search sobre archivos `.md`.
- `storage_client.py` con escritura de logs y tickets en `/Documentos/`.
- Prompts `classifier-v1` y `escalator-v1` versionados con front-matter.

### Sprint 3 — API y trazabilidad

- `POST /api/incidents` en FastAPI (recibe mensaje del chat, encola ejecución).
- `GET /api/incidents/{execution_id}` para polling del estado.
- Volumen Docker Compose para `/Documentos/`.
- Test de integración smoke con Docker Compose arriba.

### Sprint 4 — Dashboard

- Vista `/chat` en Next.js: interfaz tipo chat, polling, respuesta del agente.
- Vista `/incidencias`: listado de ejecuciones con estado y clasificación (TanStack Table).
- `lib/db.ts` (pool readonly), `lib/api.ts` (POST a FastAPI).

## Diferido a v0.2.0

- NextAuth (autenticación del dashboard).
- Sentry (observabilidad).
- `pgvector` para búsqueda semántica en KB.
- Migración de logs/tickets de filesystem a Postgres (`audit_log`, `issues`).
- `fly.toml` y `.github/workflows/deploy.yml`.

## Riesgos identificados y mitigaciones

| Riesgo | Mitigación |
|---|---|
| KB desactualizada — el agente responde con soluciones obsoletas | Proceso de revisión trimestral de `agent/knowledge/`; versionar documentos con fecha en el nombre |
| Falsos positivos — responde con solución incorrecta a alta confianza | Umbral configurable `CONFIDENCE_THRESHOLD`; logs para auditar retrospectivamente |
| Clasificación incorrecta de severidad | Reglas heurísticas en `phase_deterministic` como primer filtro; el LLM corrige |
| Tickets duplicados | Idempotencia por `external_id` en `phase_deterministic` |
| Confianza mal calibrada al arranque | Los primeros 30 días se revisan todos los logs; se ajusta `CONFIDENCE_THRESHOLD` según resultados |
| Filesystem `/Documentos/` no persistente en Fly.io | Documentado y aceptado en v0.1.x; migración a Postgres en v0.2.0 |

## Hitos

- **Sprint 0 completado:** 2026-05-12 — documentación y schemas.
- **Sprint 1 completado:** agente procesa incidencias end-to-end con `make rn`.
- **Sprint 2 completado:** KB poblada, búsqueda funcional, logs y tickets generados.
- **Sprint 3 completado:** API HTTP, `make up` + incidencia real procesada.
- **Sprint 4 completado:** dashboard con chat funcional y vista de incidencias.
- **Auditoría externa post-MVP:** sesión Claude Code con plantilla §13.15 del playbook.
