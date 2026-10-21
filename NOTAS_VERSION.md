Versión 0.3.0:
- **Entrar con Google**: al abrir, si no hay sesión, aparece la pantalla «Entrar con Google» (con el link de la carpeta del proyecto). La sesión queda abierta hasta que alguien toque «Cerrar sesión», y es una sola para las tres apps de la PC: si entras en una, ya entraste en todas.
- Arriba a la derecha está tu cuenta (foto y nombre). Ahí: **Dispositivos y seguridad**: las PCs donde se abrió tu cuenta, con qué apps, la primera y la última vez, las nuevas marcadas, y «Cerrar sesión ahí» o «Cerrar sesión en todos los demás» (esa PC la cierra sola en máximo 10 minutos).
- El candado de verdad sigue siendo Drive: solo entra quien tenga compartida la carpeta del proyecto.

Versión 0.2.2:
- Arreglo: la sala no abría («No module named 'getpass'»). Faltaban piezas de Python en el instalador. Hay que pasar el instalador de esta versión.

Versión 0.2.1:
- La sala abre más rápido: la ventana aparece al instante con «Abriendo…» y la app carga apenas está lista (antes no se veía nada hasta que todo arrancaba). Para tenerlo hay que pasar una vez el instalador completo de esta versión; con «Actualizar ahora» todo sigue funcionando igual que antes.

Versión 0.2.0:
- **✦ Pedido**: escribe lo que quieres como se lo dirías a un diseñador («3 posts 1:1 sobre omega 3 para el martes», «una historia 9:16 con este texto: …») o pega tu propio contenido. Claude decide las piezas, escribe sus textos, el prompt de Flow de cada foto y el copy, y quedan creadas y maquetadas en la semana. Cada pedido queda anotado en pedidos.json de la semana.
- «Basarse en los videos de esta semana»: las piezas acompañan los ángulos de los videos del brief.
- Formato al crear una pieza: 4:5 (feed), 1:1 (cuadrado) o 9:16 (historia). Los textos se acomodan solos al formato; en 9:16 respetan la zona segura de las historias.

Versión 0.1.0 (primera versión):
- Sala de diseño: carruseles y posts de 1080×1350 (4:5), 1080×1080 o 1080×1920, ordenados por mes y semana de lunes a domingo (S03 · 19-25 OCT).
- Fotos de Flow: arrastrarlas, quitarles el fondo con ✂ (sin internet; la primera vez baja el recortador, 170 MB) y armar encima textos con *palabra* resaltada, garabatos a mano, formas, el producto real y los logos.
- La marca no viene dentro de la sala: colores, logos, productos y reglas se leen de _MARCA en el Drive del proyecto.
- «Escribir con Claude»: el texto de cada lámina, el prompt de Flow de cada foto y el copy, con las reglas de la marca.
- Drive es la base de datos: todo se guarda en DISEÑO/ del Drive del proyecto y lo exportado queda en FINAL/, donde lo toma el Publicador. Si la semana tiene brief en _SEMANAS, se crean solas sus piezas.
- Misma conexión que las otras salas: si la Sala de edición ya está conectada a Drive en esta PC, se usa con un clic.
- Aviso si otra persona tiene abierta la misma pieza.
