# Pago rechazado o no procesado

## Cuándo usar este artículo

El cliente indica que el formulario de pago carga correctamente pero el pago es rechazado. Si el checkout entero no carga o devuelve error 500, consultar el procedimiento de escalación de checkout (incidencia crítica).

## Instrucciones para el agente: cómo diagnosticar

Antes de responder, **solicita los siguientes datos**:

1. ¿Qué método de pago se está usando? (Tarjeta Visa/Mastercard, PayPal, Bizum)
2. ¿Qué mensaje de error aparece exactamente en pantalla?
3. ¿El importe del pedido supera los €300?
4. ¿Cuántos intentos se han realizado ya?

## Diagnóstico por método de pago

### Tarjeta Visa / Mastercard

- **"Fondos insuficientes"** → saldo insuficiente en la cuenta bancaria. No es un error de la tienda.
- **"Tarjeta no autorizada" / "Tarjeta bloqueada"** → el banco ha bloqueado la transacción. El cliente debe llamar a su banco para autorizarla.
- **"Error 3DS" / "Verificación fallida"** → el cliente no completó el paso de autenticación de doble factor (SMS o app bancaria). Reintentar y completar la verificación en el móvil.
- **Pedido > €300 y primer intento fallido** → habitual. Los bancos pueden requerir confirmación adicional la primera vez. Reintentar una vez más.
- **Más de 3 intentos fallidos** → la tarjeta puede quedar bloqueada temporalmente por intentos repetidos. Esperar 24 horas o usar un método de pago alternativo.

### PayPal

- **"Pago pendiente de revisión"** → PayPal ha puesto el pago en revisión manual (frecuente en cuentas nuevas o importes altos). Puede tardar hasta 24 horas. No es necesario reintentar.
- **"Fondos insuficientes en PayPal"** → vincular una tarjeta bancaria a la cuenta PayPal o añadir saldo.
- **Error genérico de PayPal** → cerrar sesión de PayPal, borrar cookies del navegador e intentar de nuevo.

### Bizum

- Solo disponible para clientes con número de teléfono español y banco adherido a Bizum.
- Si Bizum no aparece como opción de pago → el banco del cliente no está adherido. Usar tarjeta o PayPal.
- **Límite por transacción: €500**. Pedido > €500 con Bizum → supera el límite. Usar otro método.
- **Límite diario: €2.000**. Si el cliente ya ha realizado otros pagos por Bizum en el día, puede haber alcanzado el límite.

## Escalación obligatoria si

- El pago es rechazado repetidamente sin ninguno de los motivos anteriores tras probar otra tarjeta o método.
- El cliente indica que el dinero SÍ fue descontado de su cuenta o de PayPal pero el pedido no aparece como confirmado → **ESCALAR URGENTE**: posible cobro sin confirmación de pedido (doble cargo o fallo en la pasarela).
- El error que aparece es un código técnico interno (ejemplo: ERR_GATEWAY_500), no un mensaje de banco.

**Palabras clave:** pago rechazado, pago no procesado, tarjeta rechazada, no puedo pagar, error pago, PayPal rechazado, Bizum, Visa, Mastercard, tarjeta no autorizada, fondos insuficientes, error 3DS, cobro duplicado, me han cobrado dos veces, pago pendiente, no confirma el pedido
