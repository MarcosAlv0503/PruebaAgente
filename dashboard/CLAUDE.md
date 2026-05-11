# `dashboard/` — convenciones

Frontend Next.js 15 (App Router). UI **siempre en español**, código en inglés.

## Top 5 cosas que NO hacer

1. **No mezcles UI en inglés y español.** Cliente final hispanohablante por defecto. Si el proyecto necesita inglés, ADR del proyecto que lo decida. Consecuencia: i18n a medias.
2. **No llames a la BD desde Server Components con queries ad-hoc.** Usa `lib/db.ts` (pool `pg` readonly). Si necesitas escribir, llama al backend FastAPI vía `lib/api.ts`. Consecuencia: lógica duplicada agente↔dashboard.
3. **No metas estado de servidor en client components.** Server components por defecto. Marca `"use client"` solo donde haga falta interactividad. Consecuencia: bundle gigante.
4. **No saltes `react-hook-form` + `zod` para formularios.** Validación cliente y servidor con el mismo schema. Consecuencia: formularios divergentes, errores feos.
5. **No instales más de las shadcn primitives que necesites.** Cada primitive es código copiado a `components/ui/`. Consecuencia: dependency bloat sin ganancia.

## Comandos

```bash
npm run dev         # arranca next dev (puerto 3000)
npm run build       # build producción
npm run typecheck   # tsc --noEmit
npm run lint        # next lint
```

## Cómo añadir una página

1. Crea `src/app/<ruta>/page.tsx` (Server Component por defecto).
2. Si lee de BD → usa `lib/db.ts`. Si llama al agente → usa `lib/api.ts`.
3. Si necesita interactividad → componente client en `components/...` con `"use client"`.
4. Tests: smoke con Playwright en `tests/<ruta>.spec.ts` (deferido a v0.2.0 del template).

## Por qué el dashboard existe

Dos roles esperables:

- **Operador interno:** ve la cola, reintenta ejecuciones, marca issues como resueltos, pausa el bot.
- **Stakeholder:** ve métricas de coste y volumen sin tocar la cola.

v0.1.0 del template no implementa ninguno de los dos — ship una landing placeholder con un botón shadcn para verificar que el stack compila. El primer proyecto cliente añade páginas reales.
