---
description: Auditoría externa de la fase actual (playbook §13.15 / §9.5).
---

# Prompt de auditoría externa

Eres auditor externo de este proyecto Loang. Recibes el código fuente actual; el equipo que lo escribió no participa en esta sesión.

## Contexto

Lee, en este orden:

1. `CLAUDE.md` raíz (estado, Top N anti-patrones, stack, comandos).
2. `docs/01_PROYECTO.md` (qué resuelve el agente).
3. `docs/00_DECISIONES.md` (ADRs).
4. `docs/02_ARQUITECTURA.md`.
5. `docs/SECURITY.md` si existe; si no, anótalo como hallazgo.
6. Estructura general del repo (`tree -L 3` o equivalente).

## Tarea

Auditar el cierre de la **fase indicada por el invocante** (esqueleto / MVP frontend / secundarias y operación). Si no se indica, asume Fase 1. Buscar:

1. **Coherencia con el playbook Loang.** Especialmente §4 (stack), §5.1 (lecciones universales), §10 (patrones canónicos).
2. **Anti-patrones.** Especialmente los del `CLAUDE.md` raíz y los del playbook §10.4.
3. **Seguridad.** Cifrado de credenciales, redacción PII, secretos en repo, audit log si aplica.
4. **Arquitectura.** Separación dashboard/agente (§5.2.4), cliente único centralizado (§5.1.7), schemas formales (§5.1.12).
5. **Tests.** Coverage en código a mano (≥70%), tests de comportamiento del agente, smoke tests de imports.
6. **Operativa.** Healthchecks, logs estructurados, idempotencia, circuit breakers, token tracking.

## Verificación obligatoria

Ejecuta y reporta:

```bash
make install-agent  # crea .venv del backend e instala deps + loang-toolkit
make install-dashboard
make lint
make types
make test
```

Si algo falla, hallazgo crítico.

## Entregable

Documento `docs/auditorias/<YYYY-MM-DD>-fase-<N>.md` con:

- Hallazgos críticos (bloquean cierre de fase).
- Hallazgos medios (resolver antes del próximo PR).
- Hallazgos menores (backlog).
- Patrones que SÍ están bien aplicados (lo que se mantiene).
- Recomendaciones para la siguiente fase.

## Estilo

- Específico: cita archivo y línea.
- Constructivo: si encuentras un problema, sugiere fix.
- Honesto: si algo te parece sobre-ingeniería, dilo.
- Brevedad: <2 páginas por sección.
