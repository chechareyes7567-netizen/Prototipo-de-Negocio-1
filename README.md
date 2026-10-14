# Sitio de pedidos de Entre Bocados

Sitio de **Entre Bocados** en un único `index.html`: catálogo, filtros, búsqueda, carrito, formulario de entrega o para recoger y mensaje de pedido por WhatsApp. La interfaz se puede previsualizar abriendo `index.html`; para guardar pedidos y usar el historial privado necesitas activar la API de Python y PostgreSQL según `docs/BASE_DE_DATOS.md`.

Los enlaces de la cabecera abren **vistas independientes** para Menú de Desayunos (`?seccion=desayunos`), Menú del día (`?seccion=menu-dia`), Menú a la carta (`?seccion=carta`), Algo para picar (`?seccion=productos`), Bebidas (`?seccion=bebidas`) y Promociones (`?seccion=promociones`). La historia del negocio aparece integrada en el bloque principal de inicio. El logo y el enlace «Volver al inicio» regresan a la portada. El carrito sigue disponible al cambiar de vista; la página pública mantiene las vistas en el mismo `index.html`, mientras la API y el panel privado se despliegan en un servicio aparte. El menú también está disponible en celular.

**Algo para picar** muestra tres secciones: **Recitos**, **Postres** y **Bebidas**. Recitos contiene Tortrix Barbacoa (Q 2.50), Chicharrones (Q 5.00), Tortrix Limón (Q 2.50) y Tortrix Picante (Q 2.50). Postres contiene Sponch (Q 10.00), Pingüinos (Q 10.00), Gansitos (Q 8.00), Donitas (Q 10.00) y Submarinos (Q 8.00). **Roles de Canela** también aparece con foto y «Precio por confirmar»; no puede pedirse hasta recibir su precio. Las fotos muestran presentaciones de referencia; confirma el tamaño real que corresponde a esos precios antes de compartir el enlace. En la sección Bebidas de «Algo para picar» hay un enlace a la nueva pestaña con los licuados. En celular las tarjetas y fotos son más amplias; al tocarlas o seleccionarlas con el teclado se abre la imagen completa.

En **Menú de Desayunos** aparecen **12 desayunos** con los nombres, precios y fotografías enviados. Cada desayuno utiliza su propia imagen con el nombre amarillo visible. Las fotos se muestran completas, tanto en la tarjeta como al tocarlas para ampliarlas. Se pueden ver a cualquier hora. Los pedidos de desayuno se habilitan únicamente **antes de las 11:00 a. m.** según la hora de Guatemala; desde las 11:00 a. m. siguen visibles, pero su botón queda deshabilitado y se retiran del carrito si cambió el horario. **Menú del día** muestra almuerzos y se habilita para pedirlos a las 11:00 a. m.; por ahora muestra **Arroz con pollo (Q 30.00)**, con elección obligatoria de dos guarniciones, como almuerzo predeterminado todos los días hasta configurar la rotación. **Menú a la carta** muestra siete platos confirmados en dos grupos: platos principales y crepas saladas. La página comprueba la hora al abrirla y cada minuto mientras siga abierta. La sección de Promociones también muestra un aviso hasta recibir ofertas reales. El carrito permite **Vaciar carrito**. No se muestra ni suma una tarifa de envío: para entrega a domicilio, el mensaje indica que el costo se confirmará por WhatsApp.

También muestra horario (7:00 a. m. a 5:00 p. m.), ubicación (3 Calle y 6ta Avenida, Zona 13) y zonas de entrega (calle de los Museos, calle del Ministerio de Ambiente o hasta 1 km a la redonda). El enlace de Google Maps usa la dirección de Street View proporcionada por el negocio; confirma en el mapa el punto exacto antes de compartirlo como ubicación. Incluye enlaces de Instagram (`@_polloalcarbon`) y TikTok (`@_parripollo`) construidos con los nombres proporcionados, pero no fue posible comprobar la titularidad de esas páginas. Facebook muestra el nombre de la cuenta sin enlace: la captura confirma el nombre, pero no revela la URL directa de la página.

Cuando se añada un plato del horario activo con `kind:'seco'` (o `kind:'pollo'` para menús previos), quien pide deberá elegir **dos guarniciones distintas** para poder añadirlo al carrito; aparecerán en el resumen y en el mensaje de WhatsApp. Los menús de tipo `kind:'caldo'` no piden selección; sus acompañamientos van predeterminados. Los otros menús se agregan normalmente.

El logo original de Entre Bocados y el ícono circular están incorporados al mismo `index.html`: el logo aparece en la cabecera y en la portada, y el ícono aparece en la pestaña. La paleta usa los colores del logo. Las imágenes no necesitan subirse por separado; funciona con la configuración actual de Render.

## Antes de compartir el enlace

En `index.html` busca `const SHOP = {` cerca del final del archivo y modifica:

- `name`: nombre de tu negocio, ya configurado como `Entre Bocados`.
- `whatsapp`: configurado como `50241387614` (Guatemala, número facilitado por el negocio). Comprueba en un teléfono que sea el número donde quieres recibir pedidos: el número escrito en la portada de Facebook es diferente.
- `currency`: `GTQ` para quetzales o un código de moneda ISO apropiado.
- `categories`: las tres secciones fijas del catálogo; `products`: los nueve productos con precio confirmado y Roles de Canela sin precio. Los licuados se configuran en `smoothies` y aparecen en la pestaña Bebidas; añade aquí otros productos cuando recibas su menú; usa un `id` distinto para cada producto.
- `breakfastProducts`: doce desayunos con nombre, precio, descripción, foto individual (`imageIndex`). `breakfastPhotos` contiene las doce imágenes originales incrustadas, con los nombres amarillos visibles. El código limita los pedidos de desayuno a antes de las 11:00 a. m.
- `dailyMenus`: `lunch` está vacío hasta recibir los platos de almuerzo. Puedes añadir días (`monday` a `sunday`) con `name`, `description`, `price` y `emoji`; la programación se repite semanalmente. La página estática no aprende por sí sola qué se preparó ese día.
- `sides`: las guarniciones para platos secos son `Arroz`, `Papas salteadas` y `Frijol`. Quien pida debe seleccionar exactamente dos distintas. Marca futuros platos secos con `kind:'seco'` (también se acepta `kind:'pollo'` para menús anteriores) y los caldos con `kind:'caldo'`.
- `menuOverrides`: para una fecha concreta, agrega una entrada por horario, por ejemplo `'2026-10-13': {lunch:{name:'Especial',description:'Incluye bebida',price:55,emoji:'🍲'}}`. La fecha se interpreta en la zona horaria de Guatemala.
- `promotions`: por ahora está vacío; agrega ofertas reales con `price` y, si corresponde, `compareAt` (precio anterior tachado).

**Al actualizar el sitio que ya publicaste:** guarda primero una copia de tu `index.html` de GitHub. Esta versión ya incluye el número `50241387614`; revisa que sea el número deseado y conserva cualquier producto o precio real que hayas cambiado en tu versión actual.

El botón final **Enviar por WhatsApp** abre un mensaje listo para enviar a `50241387614`. El cliente debe pulsar **Enviar** dentro de WhatsApp. El sitio no cobra ni guarda pedidos en un servidor: tú recibirás el mensaje en WhatsApp. La disponibilidad, la dirección, el costo final y el método de pago deben confirmarse con el cliente.

Para **Pasaré a recogerlo** se usa el mismo campo «Tu nombre» del cliente, sin solicitar otro nombre. Si cambia a **Entrega a domicilio**, la dirección pasa a ser obligatoria.

## Historial privado de pedidos: ampliación futura

Este sitio es estático: actualmente no dispone de un historial privado centralizado. Para conservar pedidos de todos los clientes se necesitará un servicio con servidor, una base de datos y un panel protegido por inicio de sesión. Un flujo posible es registrar el intento cuando se envía el formulario, marcarlo como **pendiente**, abrir WhatsApp y, después de recibir el mensaje, confirmarlo desde el panel. Abrir el enlace de WhatsApp no demuestra que el cliente haya enviado el mensaje.

Los nombres y precios de los nueve productos del catálogo y los doce desayunos son los facilitados por el negocio. Roles de Canela no tiene precio asignado. Las imágenes son de referencia y no se ha confirmado el tamaño de las presentaciones ni disponibilidad. Las guarniciones de platos secos son las tres indicadas por el negocio. La página de historia usa únicamente el mensaje de la captura de Facebook (pollo al carbón, comida para compartir y nueva imagen): revisa ese texto si deseas añadir fechas o detalles reales. Facilita el enlace directo de Facebook para activar esa red.

## Publicar gratis con GitHub Pages

1. Crea un repositorio público nuevo en GitHub para esta tienda.
2. Sube `index.html` a la raíz del repositorio; el archivo debe llamarse exactamente así.
3. En el repositorio ve a **Settings → Pages**. En **Build and deployment**, selecciona **Deploy from a branch**, la rama `main` y la carpeta **/(root)**. Guarda los cambios.
4. GitHub mostrará el enlace público cuando termine de publicar. Copia ese enlace y pruébalo desde otro dispositivo.

## Si prefieres Render

Crea un repositorio nuevo con `index.html` en la raíz. En Render elige **New → Static Site** (no Web Service) y conecta ese repositorio. Si solicita **Build Command**, pon `mkdir -p public && cp index.html public/`; en **Publish Directory**, pon `public`. Render te mostrará una URL `onrender.com` al finalizar. No necesitas `Start Command` para un sitio estático.

**Nota:** un sitio estático mantiene el carrito en el navegador del cliente. Si más adelante quieres un panel de administración, inventario compartido, pagos integrados o pedidos guardados automáticamente, hará falta un servicio adicional y una base de datos.

Las líneas del carrito muestran miniaturas de las fotografías aportadas. Los platos sin fotografía facilitada, como Arroz con pollo, muestran el logo en su lugar hasta recibir una imagen real. La franja superior dice «Entre bocados - Sabor para cada momento».

El mensaje de WhatsApp presenta primero los datos de contacto y modalidad de entrega, luego el detalle del pedido y los precios con subtotal al final. El formulario también pide el nombre a cuyo cargo estará el pedido, además del nombre y teléfono de contacto.

### Bebidas y extras

La pestaña «Bebidas» reúne los licuados y «Extras» sigue en desayunos pendiente de precios. Fresa cuesta Q 8 con agua / Q 12 con leche; banano solo Q 12 con leche; papaya Q 12 con agua / Q 15 con leche; mango solo Q 12 con agua; piña solo Q 10 con agua. Cada uno de estos cinco permite seleccionar sin azúcar, poca, media o mucha azúcar. La elección se guarda en el carrito y se incluye en el pedido de WhatsApp. «Licuado Frutas mixtas» ahora es una receta fija con base de agua, fresa, papaya y piña; permite elegir con azúcar o sin azúcar. Al cambiar la receta, no se proporcionó un nuevo precio: permanece visible con «Precio por confirmar», sin opción de pedido hasta recibirlo. Las fotos proporcionadas corresponden a fresa, banano y papaya; faltan fotos de mango, piña y la mezcla.

### Ajustes de ubicación y desayunos

El enlace «Buscar dirección en Maps» abre el enlace directo de Street View proporcionado. En Inicio, el botón principal abre Menú del día y un aviso indica que todos los desayunos incluyen pan francés. «Algo para picar» tiene el icono de un bocadillo. Extras enumera porción de plátanos, porción de frijoles, pan francés extra, 1 huevo extra y porción de crema; sus precios aún no se han facilitado y por eso no pueden agregarse al carrito. El desayuno Chapín requiere elegir huevos revueltos simples, estrellados (bien cocidos o término medio) o en torta; la elección se incluye en el carrito y en WhatsApp.

### Carta y nuevos datos del pedido

Menú a la carta ofrece La Hamburguesa Clásica (Q 30, papas salteadas y bebida natural del día), Torito burger (Q 32, papas salteadas), Burrito de la Casa (Q 30, papas salteadas), y Dieta pechuga de pollo (Q 35, vegetales y ensalada del día). En Crepas saladas: La favorita (Q 30, jamón y mozzarella), La Brunch (Q 32, jamón, huevo y mozzarella) y La italiana (Q 33, pollo al pesto, mozzarella y crema). No se suministraron fotos para estos platos.

El checkout pide siempre el nombre de quien recibirá el pedido. Si el cliente selecciona domicilio, exige dirección y hora entre 11:00 a. m. y 5:00 p. m. Al pagar en efectivo pide el monto (al menos el subtotal de productos); si paga por transferencia, el mensaje de WhatsApp solicita los datos de la cuenta y explica que el cliente enviará el comprobante por el chat. La página no dispone de datos bancarios ni recibe archivos; el comprobante debe enviarse dentro de WhatsApp después del texto de pedido. El envío se confirma aparte.

### Historial y base de datos

Para activar el registro de pedidos y consultar el panel privado, lee [docs/BASE_DE_DATOS.md](docs/BASE_DE_DATOS.md). El sitio publicado sigue funcionando como página estática; el servidor de Python y PostgreSQL se conectan después de configurar la URL pública de la API. Los pedidos se registran como pendientes antes de abrir WhatsApp y solo se cuentan como ventas cuando el negocio los confirma.
