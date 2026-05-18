# Dominio — Soporte Operativo Ecommerce

Reglas de negocio del agente. Fuente de verdad para clasificación, routing y criterios de escalación.

## Tipos de incidencia

| Tipo | Código | Ejemplos típicos |
|---|---|---|
| Técnica | `technical` | Error 500, web caída, lentitud general, fallo de carga de página |
| Funcional | `functional` | Cupón no aplica, filtros no funcionan, carrito no guarda items |
| Acceso | `access` | No puede iniciar sesión, recuperación de contraseña fallida, sesión expirada inesperadamente |
| Pago | `payment` | Checkout no completa, pasarela de pago falla, tarjeta rechazada sin motivo |
| Contenido | `content` | Imágenes no cargan, descripción incorrecta, precio mal mostrado, stock incorrecto |
| Otro | `other` | No encaja en ninguna categoría anterior |

## Niveles de severidad

| Nivel | Código | Criterio operativo |
|---|---|---|
| Crítica | `critical` | Impide completar compras o acceder al sistema para todos los usuarios. **Siempre escala a humano, sin excepción.** |
| Alta | `high` | Afecta a una funcionalidad clave pero existe workaround. Escala si confidence < threshold. |
| Media | `medium` | Molestia funcional o visual, no bloquea la operación de la tienda. |
| Baja | `low` | Cosmética, menor, no urgente. |

## Reglas de asignación de severidad (phase_deterministic)

Aplicadas mediante heurística pura en código, antes del LLM:

| Condición detectada | Severidad asignada |
|---|---|
| Keywords: `checkout`, `pagar`, `pago`, `compra`, `pedido` + `no funciona`/`error`/`falla` | `critical` |
| Keywords: `no puedo acceder`, `login`, `iniciar sesión` + síntoma generalizado | `critical` |
| Keywords: `error 500`, `web caída`, `no carga nada` | `critical` |
| Keywords: `imagen`, `foto`, `no carga` | `high` |
| Keywords: `cupón`, `descuento`, `código promocional` | `medium` (salvo indicación de promoción activa → `high`) |
| Keywords: `lento`, `tarda`, `va mal` | `medium` |
| Keywords: `descripción`, `precio`, `stock` | `low` |
| Sin match | pendiente de clasificación por LLM |

Estas reglas son orientativas y el LLM en `phase_light_llm` puede corregirlas con su clasificación.

## Umbral de confianza

Variable de entorno: `CONFIDENCE_THRESHOLD` (default `0.75`).

| Condición | Acción |
|---|---|
| `confidence >= CONFIDENCE_THRESHOLD` y `severity != critical` y `kb_results` no vacío | Resolución automática — responde en chat |
| `confidence < CONFIDENCE_THRESHOLD` | Pasa a `phase_heavy_llm` |
| `severity == critical` | Pasa a `phase_heavy_llm` siempre |
| `kb_results` vacío | Pasa a `phase_heavy_llm` |

## Base de conocimiento

Archivos `.md` en `agent/knowledge/`. Estructura de carpetas:

```
agent/knowledge/
├── faqs/              ← preguntas frecuentes con solución documentada
├── technical/         ← procedimientos técnicos paso a paso
├── procedures/        ← flujos operativos y de escalación
└── known_issues/      ← incidencias conocidas con solución verificada
```

**Reglas de la KB:**
- Read-only para el agente. Solo el equipo humano actualiza los documentos.
- Cada documento debe tener título descriptivo y palabras clave en el cuerpo.
- Cada documento debe incluir la solución concreta, no solo la descripción del problema.
- Los documentos obsoletos deben moverse a `agent/knowledge/_deprecated/` (no borrar).

**Búsqueda en MVP (v0.1.x):** keyword matching — se buscan los `extracted_keywords` de la incidencia en el contenido de cada archivo `.md`. Se devuelven los top-3 documentos con más coincidencias.

**Evolución planificada (v0.2.0):** `pgvector` con embeddings para búsqueda semántica real (ADR pendiente).

## Formato de log (fichero `.txt`)

Ruta: `/Documentos/logs/<YYYY-MM-DD>_<incident_id>_<type>.txt`

```
INCIDENT LOG
============
incident_id:    <uuid>
execution_id:   <uuid>
timestamp:      <ISO-8601>
reporter:       <nombre>
channel:        web
type:           <technical|functional|access|payment|content|other>
severity:       <critical|high|medium|low>
confidence:     <0.000–1.000>
auto_resolved:  <true|false>
message:        <texto original del operador>
response:       <respuesta generada por el agente>
kb_refs:        <lista de rutas de documentos KB usados, o "none">
```

## Formato de ticket (fichero `.txt`)

Ruta: `/Documentos/tickets/<YYYY-MM-DD>_<ticket_id>_<priority>.txt`

```
INCIDENT TICKET
===============
ticket_id:          <uuid>
execution_id:       <uuid>
timestamp:          <ISO-8601>
priority:           <critical|high|medium|low>
summary:            <resumen en una línea>
reporter:           <nombre>
incident_message:   <texto original del operador>
context:            <análisis del agente>
escalation_reason:  <por qué no se pudo resolver automáticamente>
suggested_steps:    <pasos recomendados para el operador humano>
```

## Ejemplos de incidencias con clasificación esperada

| Mensaje del operador | Tipo | Severidad | Auto-resoluble | Notas |
|---|---|---|---|---|
| "El checkout no deja pagar" | `payment` | `critical` | No | Siempre escala por severidad |
| "No cargan las imágenes de producto" | `content` | `high` | Sí (si KB tiene procedimiento) | |
| "No puedo iniciar sesión" | `access` | `high` | Sí (si KB tiene pasos de reset) | Crítico si afecta a todos |
| "El cupón SUMMER10 no funciona" | `functional` | `medium` | Sí (si KB documenta ese cupón) | |
| "La web va muy lenta" | `technical` | `medium` | Sí (si KB tiene diagnóstico) | |
| "Error 500 en todas las páginas" | `technical` | `critical` | No | Siempre escala |
| "El precio del producto X está mal" | `content` | `low` | Sí (si KB tiene procedimiento) | |
