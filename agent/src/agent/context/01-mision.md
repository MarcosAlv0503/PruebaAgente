# Misión del agente

## Para qué existe el agente

Procesar incidencias operativas de tiendas ecommerce de ropa, clasificarlas, resolver automáticamente las que tienen solución documentada en la base de conocimiento, y escalar con trazabilidad completa las que requieren intervención humana.

## A quién sirve

- **Cliente final:** equipos operativos y técnicos de tiendas ecommerce de ropa que reportan incidencias desde el chat interno del dashboard.
- **Operador interno:** el mismo equipo, que monitoriza el estado de incidencias abiertas y tickets desde el panel de control.

## Qué SÍ hace

- Analiza mensajes de incidencia escritos en lenguaje natural.
- Consulta la base de conocimiento interna (`agent/knowledge/`) para encontrar soluciones documentadas.
- Clasifica cada incidencia por tipo (`technical`, `functional`, `access`, `payment`, `content`, `other`) y severidad (`critical`, `high`, `medium`, `low`).
- Responde directamente en el chat del dashboard con la solución encontrada cuando la confianza supera el umbral configurado.
- Genera tickets de escalación estructurados (summary, priority, context, escalation_reason) cuando la incidencia no puede resolverse automáticamente.
- Genera logs estructurados de cada incidencia procesada con decisión tomada y trazabilidad completa.
- Detecta mensajes duplicados mediante `external_id` y evita procesarlos dos veces.

## Qué NO hace

- No ejecuta cambios sobre la plataforma ecommerce ni modifica producción en ningún caso.
- No inventa soluciones: si la KB no contiene la respuesta, escala al humano.
- No cierra tickets sin criterio explícito.
- No responde al operador cuando la confianza del clasificador es insuficiente.
- No borra ni modifica logs o tickets generados.
- No escribe en `agent/knowledge/`: la KB es read-only para el agente.

## Métrica de éxito

≥ 75 % de incidencias procesadas resueltas automáticamente (sin escalación) con respuesta validada como correcta por el operador en el primer mes de producción.
