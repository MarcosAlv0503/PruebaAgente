# Criterio de éxito y de fallo

> TODO loang-template: rellenar al clonar.

## Cuándo se considera éxito

- <Lista de condiciones objetivas. Ej: "el output valida contra `output.schema.json` y la métrica clave del proyecto se cumple en el caso golden".>

## Cuándo se considera fallo recuperable

- <Lista de condiciones donde el agente abandona pero la ejecución se puede reintentar (mete entrada en `human_tasks` cuando ese módulo aterrice).>

## Cuándo se considera fallo no recuperable

- <Condiciones donde el output es dañino o el coste explota: dispara `bot-pause` y notifica al operador.>

## Cuándo escalar a humano

- <Reglas explícitas de escalación. Ej: monto > X €, sentimiento muy negativo, modelo light no resuelve y heavy tampoco.>
