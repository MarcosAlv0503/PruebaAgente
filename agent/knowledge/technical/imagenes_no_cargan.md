# Imágenes de producto no cargan

## Síntomas
Las imágenes de la ficha de producto aparecen rotas (icono de imagen rota), en gris o directamente no se muestran.

## Diagnóstico rápido

1. Abrir la URL directa de la imagen en el navegador (clic derecho → "Abrir imagen en nueva pestaña").
   - Error 404: el archivo no existe en el servidor → subir de nuevo.
   - Error 403: problema de permisos → escalar a técnico.
   - Carga correctamente: problema de caché del navegador o del CDN.

2. Limpiar la caché del navegador (Ctrl+Shift+R) y verificar en modo incógnito.

## Pasos de resolución

1. Verificar en el panel de administración que la imagen está subida correctamente (Admin → Catálogo → Producto → Imágenes).
2. Si el archivo existe pero no se muestra: intentar descargar y volver a subir la imagen.
3. Si el problema afecta a un solo producto: puede ser un archivo corrupto → resubir.
4. Si el problema afecta a múltiples productos o a toda la tienda → escalar inmediatamente.

## Escalación necesaria si

- El problema afecta a más de 5 productos simultáneamente.
- El problema afecta a todas las imágenes de la tienda.
- Las imágenes cargan directamente pero no a través de la tienda → posible fallo en el CDN o proxy de imágenes.

**Palabras clave:** imagen, imágenes, imagenes, foto, fotos, no carga, no cargan, rota, roto, broken, CDN, falta imagen
