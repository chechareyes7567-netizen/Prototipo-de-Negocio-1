# Prototipo de tienda para recibir pedidos

Una tienda de demostración en un único `index.html`: catálogo, filtros, búsqueda, carrito, formulario de entrega o para recoger y mensaje de pedido por WhatsApp. No requiere Python, base de datos ni paquetes externos. Puedes abrir `index.html` en tu navegador antes de publicarlo.

## Antes de compartir el enlace

En `index.html` busca `const SHOP = {` cerca del final del archivo y modifica:

- `name`: nombre de tu negocio.
- `whatsapp`: tu número internacional, solo dígitos. Para Guatemala: `502` seguido de tus ocho dígitos; por ejemplo `50212345678` es **solo un ejemplo ficticio**.
- `currency`: `GTQ` para quetzales o un código de moneda ISO apropiado.
- `deliveryFee`: costo estimado del envío; modifica también el texto de confirmación si tu política es distinta.
- `products`: productos de ejemplo. Cambia `name`, `category`, `price`, `emoji`, `tag`, `color` y `description` para cada uno. Usa identificadores `id` distintos. Puedes añadir o quitar objetos de la lista.

Mientras `whatsapp` esté vacío, el botón final dice **Copiar pedido**. Cuando pongas tu número, dirá **Enviar por WhatsApp** y abrirá un mensaje listo para enviar. El cliente debe pulsar **Enviar** dentro de WhatsApp. El sitio no cobra ni guarda pedidos en un servidor: tú recibirás el mensaje en WhatsApp. La disponibilidad, la dirección, el costo final y el método de pago deben confirmarse con el cliente.

Los productos y precios actuales son **ficticios**. No publiques la demostración sin cambiar el contacto y revisar el catálogo.

## Publicar gratis con GitHub Pages

1. Crea un repositorio público nuevo en GitHub para esta tienda.
2. Sube `index.html` a la raíz del repositorio; el archivo debe llamarse exactamente así.
3. En el repositorio ve a **Settings → Pages**. En **Build and deployment**, selecciona **Deploy from a branch**, la rama `main` y la carpeta **/(root)**. Guarda los cambios.
4. GitHub mostrará el enlace público cuando termine de publicar. Copia ese enlace y pruébalo desde otro dispositivo.

## Si prefieres Render

Crea un repositorio nuevo con `index.html` en la raíz. En Render elige **New → Static Site** (no Web Service) y conecta ese repositorio. Si solicita **Build Command**, pon `mkdir -p public && cp index.html public/`; en **Publish Directory**, pon `public`. Render te mostrará una URL `onrender.com` al finalizar. No necesitas `Start Command` para un sitio estático.

**Nota:** un sitio estático mantiene el carrito en el navegador del cliente. Si más adelante quieres un panel de administración, inventario compartido, pagos integrados o pedidos guardados automáticamente, hará falta un servicio adicional y una base de datos.
