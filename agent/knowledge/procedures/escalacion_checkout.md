# Procedimiento de escalación: checkout inaccesible

## Cuándo usar este procedimiento

El checkout no funciona o los clientes no pueden completar pedidos. Esta incidencia es siempre **crítica** y **siempre requiere escalación humana inmediata**.

## Acción inmediata del operador (antes de escalar)

1. Verificar si el problema es general o solo para algunos usuarios:
   - Probar en modo incógnito desde otro navegador.
   - Preguntar a otro operador si también lo reproduce.
2. Comprobar el estado de la pasarela de pago en su propio panel:
   - Stripe: https://status.stripe.com
   - PayPal: https://www.paypal-status.com
   - Redsys: consultar con el banco.
3. Revisar si hay mantenimiento programado de la plataforma ecommerce.

## Escalación técnica obligatoria

Notificar al responsable técnico incluyendo:
- Hora exacta de detección del problema.
- Número aproximado de pedidos fallidos (si se conoce).
- Pasarela de pago afectada (Stripe, PayPal, Redsys, otra).
- Mensaje de error exacto que aparece en pantalla (si lo hay).
- Si afecta a todos los métodos de pago o solo a uno.

**Tiempo de respuesta objetivo: 15 minutos desde la notificación.**

## Información que el técnico necesitará

- ¿Qué pasarela de pago está fallando?
- ¿Desde qué hora ocurre?
- ¿Hay algún error concreto visible en pantalla o en los logs?
- ¿Afecta a todos los métodos de pago o solo a algunos?
- ¿El problema empezó después de algún cambio reciente en la plataforma?

**Palabras clave:** checkout, pagar, pago, pasarela, tarjeta, pedido, compra, carrito, stripe, paypal, redsys, no puedo pagar, no deja pagar
