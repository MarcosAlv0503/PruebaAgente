# Antipatrones del template

Versión extendida de los Top 6 que aparecen en `CLAUDE.md` raíz. Cada uno con motivo, consecuencia operativa y caso real (cuando el playbook lo refleja).

## 1. Lógica de negocio en el template

**Regla.** El template es esqueleto cableado. Cada placeholder lleva `# TODO loang-template:` y el proyecto cliente lo resuelve.

**Por qué duele.**

- El template se acopla a un proyecto concreto y deja de ser reusable para los siguientes.
- El próximo dev que clone hereda decisiones que no tomó y que probablemente no encajen en su caso.
- Versionado del template se vuelve un campo de minas — cualquier bump rompe los proyectos clonados.

**Cómo se mantiene.** `make verify-template-cleanup` lista los TODOs pendientes. El smoke test de Fase 1 (cuando se reactive) clona el template y exige zero TODOs sin tocar.

## 2. Upgrade major sin ADR del playbook

**Regla.** Next.js 15 (no 16), Python 3.13 (no 3.14), NextAuth v5 estable (no beta). Cualquier subida major requiere ADR del playbook, no del proyecto que clona.

**Por qué duele.**

- Proyectos clonados antes de la subida heredan inestabilidades.
- Versiones beta arrastran APIs en flujo; rompes en cada minor del beta.
- El estándar Loang pierde sentido si cada template-bump cambia el stack.

**Caso real.** El equipo que arrancó proyectos con Next.js 13 antes del 14 tuvo que migrar manualmente cuando el template subió, costando ~2 días por proyecto.

## 3. `loang-toolkit` con `pip install -e .` o path local

**Regla.** Siempre `git+https://github.com/LoangIA/loang-toolkit@v<X.Y.Z>` con tag pinned.

**Por qué duele.**

- Path local atan al toolkit a un fork no commiteado. Otros devs no lo pueden reproducir.
- `-e .` arrastra cambios sin pasar por release; se pierde la disciplina de versionado.
- Cuando el toolkit publica `v0.2.0` con cambios, el proyecto debe bumpear conscientemente, no arrastrar.

**Cómo. ** Ver [`agent/pyproject.toml`](../agent/pyproject.toml#L18). Bump cambia esa línea y CI re-instala desde el tag nuevo.

## 4. Commitear `.env` o secretos

**Regla.** Solo `.env.example` en repo. `.env` en `.gitignore` desde el día uno.

**Por qué duele.**

- Una `OPENROUTER_API_KEY` filtrada drena saldo sin rate-limit.
- `FERNET_KEY` filtrada hace descifrables las credenciales del cliente final cifradas en BD.
- Servicios que escanean GitHub público encuentran secretos en minutos.

**Caso real.** Playbook §15: incidente de Q2 2026 con `OPENROUTER_API_KEY` commiteada por error → consumo nocturno de $400 en 6h, rotación + bloqueo + ADR de proceso.

## 5. `agent/context/` con contenido de un proyecto concreto

**Regla.** Mantén placeholders genéricos (`<placeholder>`, `<...>`). Cada proyecto cliente rellena al clonar.

**Por qué duele.**

- El template "habla" de un dominio que no es el del proyecto que lo clona, generando confusión inmediata.
- El primer prompt al LLM en un proyecto nuevo arrastra ejemplos del dominio anterior y produce alucinaciones.

**Cómo se verifica.** Revisión de PR del template: ningún archivo en `agent/src/agent/context/` puede mencionar un cliente, producto o dominio concreto.

## 6. UI mezclando inglés y español

**Regla.** UI siempre en español por defecto. Si el proyecto necesita otro idioma, ADR del proyecto (no del template).

**Por qué duele.**

- i18n a medias es peor que monolingüe — el cliente final ve la mitad en su idioma y la otra en inglés "de placeholder".
- Strings hard-coded en inglés se quedan congelados; nadie las traduce porque "no eran para ese idioma".

**Cómo. ** El layout raíz [`dashboard/src/app/layout.tsx`](../dashboard/src/app/layout.tsx) fija `lang="es"`. Componentes nuevos siempre escriben texto en español o usan keys de traducción si el proyecto añade `next-intl`.
