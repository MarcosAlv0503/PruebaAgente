# Cupón PRIMAVERA26 — Especificación completa

## Datos del cupón

| Campo | Valor |
|---|---|
| Código | PRIMAVERA26 |
| Descuento | 20% sobre precio de venta |
| Colección aplicable | Nueva Colección Primavera-Verano 2026 (etiqueta interna "SS26") |
| Importe mínimo | €40 (IVA incluido, calculado sobre el subtotal ANTES del descuento) |
| Fecha de inicio | 14 de febrero de 2026 |
| Fecha de expiración | 31 de mayo de 2026 (inclusive) |
| Usos por cuenta | 1 único uso por cuenta registrada |
| Acumulable | NO — incompatible con cualquier otro cupón o promoción activa |
| Excluidos | Artículos en Outlet, básicos (camisetas lisas, calcetines, ropa interior), accesorios (bolsos, cinturones, joyería, sombreros) |
| Válido para | Clientes con cuenta registrada; NO válido para compras como invitado |

## Razones documentadas por las que el cupón puede fallar

1. **Importe mínimo no alcanzado** — el subtotal del carrito es inferior a €40 antes del descuento
2. **Cupón ya utilizado** — la cuenta ya tiene un pedido anterior donde se aplicó PRIMAVERA26
3. **Artículos excluidos en el carrito** — si TODOS los artículos son Outlet/básicos/accesorios, el cupón no aplica; si solo algunos son excluidos, el descuento se aplica solo a los artículos elegibles
4. **Cupón combinado con otro** — hay otro código activo en el mismo pedido
5. **Cupón expirado** — la fecha de compra supera el 31 de mayo de 2026
6. **Artículos de temporada anterior** — prendas de colecciones previas a SS26 no son elegibles aunque no sean Outlet
7. **Compra como invitado** — el cliente no está autenticado con su cuenta
8. **Error técnico** — todas las condiciones se cumplen pero el sistema rechaza el cupón igualmente

## Instrucciones para el agente: árbol de diagnóstico

Pregunta en orden. Detente en cuanto encuentres la causa.

**Pregunta 1 — Importe mínimo:**
> "¿El importe total de tu carrito (antes del descuento) supera los 40€?"

- Respuesta **NO** → Resolución determinista:
  *"El cupón PRIMAVERA26 requiere un pedido mínimo de €40. Añade más artículos para poder aplicarlo."*
- Respuesta **SÍ** → continuar con Pregunta 2

---

**Pregunta 2 — Uso previo:**
> "¿Has utilizado el código PRIMAVERA26 alguna vez anteriormente en esta misma cuenta?"

- Respuesta **SÍ** → Resolución determinista:
  *"El cupón PRIMAVERA26 solo puede usarse una vez por cuenta. Si crees que es un error, contacta con soporte técnico."*
- Respuesta **NO** → continuar con Pregunta 3

---

**Pregunta 3 — Artículos excluidos:**
> "¿Todos los artículos de tu pedido pertenecen a la nueva colección SS26? ¿Hay algún artículo de Outlet, básicos (camisetas lisas, calcetines, ropa interior) o accesorios (bolsos, cinturones, joyería)?"

- Respuesta indica **solo artículos excluidos** → Resolución determinista:
  *"El cupón PRIMAVERA26 no aplica sobre artículos de Outlet, básicos ni accesorios. Retíralos del pedido o realiza un pedido separado solo con artículos de nueva colección SS26."*
- Respuesta indica **mezcla** → Resolución parcial:
  *"PRIMAVERA26 aplica solo a los artículos elegibles de la colección SS26. Los artículos de Outlet, básicos y accesorios quedan excluidos del descuento."*
- Respuesta **todos son SS26** → continuar con Pregunta 4

---

**Pregunta 4 — Combinación con otros cupones:**
> "¿Tienes aplicado algún otro código de descuento en el mismo pedido?"

- Respuesta **SÍ** → Resolución determinista:
  *"PRIMAVERA26 no es acumulable con otros cupones. Retira el otro código y aplica únicamente PRIMAVERA26."*
- Respuesta **NO** → continuar con Pregunta 5

---

**Pregunta 5 — Cuenta registrada:**
> "¿Estás comprando con tu cuenta registrada o como invitado?"

- Respuesta **invitado** → Resolución determinista:
  *"El cupón PRIMAVERA26 solo es válido para compras con cuenta registrada. Inicia sesión o crea una cuenta para poder aplicarlo."*
- Respuesta **cuenta registrada** → todas las condiciones se cumplen → **escalar a técnico (+34 910 555 222)**:
  *"El cupón cumple todas las condiciones pero el sistema lo está rechazando. He escalado el caso al equipo técnico que te contactará para resolverlo."*

## Palabras clave de búsqueda

primavera26, primavera 26, PRIMAVERA26, cupón primavera, cupon primavera, descuento primavera, promoción SS26, promo primavera
