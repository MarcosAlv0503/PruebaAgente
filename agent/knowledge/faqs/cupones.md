# Cupones y códigos de descuento — guía general

## Cupones activos en la tienda Demo

| Código | Descripción | Tipo |
|---|---|---|
| PRIMAVERA26 | 20% dto, colección SS26, válido feb–may 2026, mínimo €40 | Campaña temporal |
| BIENVENIDO10 | 10% dto, primer pedido, mínimo €30 | Primer pedido |
| VERANO2026 | 20% dto, colección PV2026, válido may–ago 2026 | Campaña temporal |
| FIDELIDAD20 | 20% dto, 5+ pedidos anteriores, mínimo €50, solo ropa | Fidelización |
| REGALO5 | €5 dto, programa de referidos | Referidos |

Para cada cupón existe un artículo específico en `promotions/` con las condiciones completas y el diagnóstico paso a paso. Consulta el artículo correspondiente según el código que reporte el operador.

## Causas generales de fallo (aplicables a cualquier cupón)

- **Código mal escrito:** pedir al operador que lo introduzca manualmente, sin copiar y pegar (puede haber espacios en blanco invisibles al copiar desde un correo).
- **Cupón de otro comercio:** verificar que el código pertenece a esta tienda.
- **Cupón ya aplicado pero descuento no visible:** refrescar la página del carrito antes de concluir.

## Acumulación entre cupones

- BIENVENIDO10 → **no acumulable** con ningún otro cupón.
- VERANO2026 → **no acumulable** con otros cupones.
- FIDELIDAD20 → **no acumulable** con otros cupones.
- REGALO5 → **sí acumulable** con VERANO2026 y FIDELIDAD20; NO con BIENVENIDO10.

## Escalación necesaria si

- El cupón cumple todas las condiciones documentadas pero el sistema sigue rechazándolo.
- El error afecta a todos los cupones de la tienda de forma simultánea (posible fallo del motor de descuentos).

**Palabras clave:** cupón, cupon, descuento, código descuento, codigo descuento, promoción, promocion, voucher, no funciona cupón, no aplica descuento, código inválido, codigo invalido, ya utilizado
