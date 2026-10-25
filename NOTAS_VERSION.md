Versión 0.13.0:
- **Videos abre al instante**: antes tardaba unos 15 s cada vez, porque recorría todo el Drive carpeta por carpeta. Ahora la lista se pide de una sola vez (la mitad del tiempo), se guarda en esta PC y se muestra apenas entras; si tiene más de 10 minutos, se busca la nueva por detrás («buscando videos nuevos en Drive…»). La sala la pide al abrir, así que al entrar a Videos ya suele estar.
- **Configuración como la de la Sala de edición**: «🔌 Conexiones» en tarjetas (Drive, Claude, Antigravity con Gemini, Google Flow, Claude en Chrome, la marca y el recortador), cada una con su estado, «Cómo se hace» y su botón, y arriba cuántas están listas. La elección de IA (Automático, Solo Claude, Solo Gemini) queda arriba de las tarjetas. Marca con botones grandes («Ver la marca», «Importar mi marca»).
- La pestaña **«✦ Crear con IA»** pasa a la derecha de la barra.
Versión 0.12.0:
- **✦ Generar fotos con IA**: la IA abre Google Flow con tu cuenta (Claude en tu Chrome con su extensión, o Gemini en Antigravity), genera las fotos que faltan con el prompt de cada lámina, las baja y la sala las pone sola en su lámina. Igual que «Generar en Flow» de la Sala de edición.
  - En cada tarjeta con «Faltan fotos» es el botón principal («Subir a mano» queda al lado). En el editor está arriba del panel de fotos. En Inicio, «✦ Generar las fotos de las N con IA» hace todas las piezas de la semana en un solo viaje a Flow.
  - Cada foto va donde la lámina la esperaba: de fondo, o recortada sin fondo (se recorta sola) si la lámina iba sobre un color.
  - Lo que Google rechace o no se baje queda dicho al final, y el botón sirve para reintentar solo esas.
  - Mientras trabaja se ve qué hace en Chrome, cuánto lleva y «Cancelar».
- **Arreglo:** una lámina con la bolsa del producto pero sin la foto de Flow que espera ya no cuenta como completa.
- La miniatura de la tarjeta sale aunque falten fotos en otras láminas (solo necesita la primera).
Versión 0.11.1:
- **Arreglo: una pieza ya no sale «Lista» si sus fotos no existen.** Cuando la IA escribe una pieza, anota qué foto de Flow va en cada lámina (por ejemplo C05_N1.jpg) antes de que se genere. La sala la contaba como puesta; ahora solo cuenta si la foto está de verdad en la carpeta Flow de la pieza (o en _MARCA). Esas piezas salen como «Faltan fotos», con «Textos listos · Faltan las fotos de Flow» en la tarjeta, y en el editor cada lámina sin su foto dice «sin foto».
Versión 0.11.0:
- **Cada pieza dice en qué paso va**, con las mismas palabras en todas partes: **Por escribir · Faltan fotos · Lista · Exportada** (antes decía «Borrador» aunque la pieza estuviera terminada).
- **Cada tarjeta trae el botón del paso que sigue**: «✦ Escribir con IA», «Poner fotos (2 de 4)» o «Exportar», y una barrita de 3 pasos (textos, fotos, exportar). El botón abre la pieza y lleva directo a esa caja.
- **Los borradores vacíos ya no parecen un error**: se ven como láminas punteadas «por llenar», y la tarjeta dice de dónde salió la pieza (del brief, de un pedido, de un video o hecha a mano).
- **Inicio**: una franja explica que la estrategia dejó las piezas en el brief y que la sala las creó sola. Con **«✦ Escribir las N con IA»**, la IA las escribe todas, una tras otra, con el tema, nivel y estilo del brief.
- **Mientras la IA trabaja** se ve: el botón gira y dice «Escribiendo…», aparece el tiempo que lleva y un «Cancelar» (también con Claude), y las láminas que va a llenar laten.
- **Los textos van solos a las láminas** cuando la IA termina. Si las láminas ya tenían textos, primero pregunta.
- **Editor con guía**: arriba de la lámina, «① Textos ② Fotos 1 de 4 ③ Exportar» y lo que falta («Falta: foto en las láminas 2 y 3»). Solo el botón del paso que sigue va en azul.
- **Fotos de Flow lámina por lámina**: cada lámina de la tira tiene su botón «Prompt» y su aviso «sin foto», y se le puede soltar la foto encima. Si subes varias fotos juntas, la sala ofrece ponerlas en orden en las láminas sin foto. Hay un botón para copiar todos los prompts juntos.
- **Biblioteca más ordenada**: buscador, semana y los 4 estados a la vista (cada uno con cuántas hay); mes, fechas, tipo, formato y nivel van en «Más filtros». Se actualiza cada vez que se abre.
- Mejor contraste en los botones azules y en las etiquetas naranjas del tema claro, y botones y colores un poco más grandes.
Versión 0.10.2:
- **El Publicador sabe con qué video va cada post:** al crear piezas con «✦ Crear con IA» a partir de un video de la Sala de edición, la pieza guarda ese video. En el Publicador el post dice «Va con: …» y el video «Tiene post».
- Cada pieza guarda su **semana** (S03) y un código fijo (S03-D-C01), para que el Publicador la ponga en la semana correcta.
- **Arreglo:** la lista de videos de referencia ya muestra también los que la Sala de edición exporta por día (V.FINALES/DIA_1…), sin las partes sueltas.
Versión 0.10.1:
- **Configuración por páginas**, como en la Sala de edición: cada opción del menú de la izquierda (Cuenta y dispositivos, IA, Marca del proyecto, Tu nombre, Actualizaciones) abre solo su página, en vez de una página larga que baja. Ya no quedan dos opciones marcadas a la vez.
Versión 0.10.0:
- **La IA ya no depende solo de Claude: Claude o Gemini, siempre.** En Configuración → «IA: Claude y Gemini» eliges Automático (recomendado), Solo Claude o Solo Gemini. En Automático escribe Claude y, si no tiene la sesión iniciada o se cae (por ejemplo, se acabó el uso del plan), el mismo pedido sigue con Gemini sin que hagas nada.
- **Gemini trabaja solo en Antigravity**: la sala abre Antigravity, le pasa el pedido a Gemini y toma la respuesta apenas termina (un carrusel tarda alrededor de 1 minuto y medio). Mientras tanto, una caja abajo a la derecha dice qué pasa y tiene «Cancelar». Si algún día no puede pasárselo sola, te copia el mensaje para que lo pegues en Antigravity.
- La pastilla de arriba dice qué IA va a escribir: «IA: Claude», «IA: Gemini» o «Sin IA».
- **Arreglo: pedidos largos con un video de referencia ya no fallan** (Windows cortaba el pedido cuando pasaba de unas 32.000 letras).
- **Arreglo: si Claude se cuelga, ya no se queda trabado para siempre**: a los 10 minutos se corta, y «Cancelar» funciona también mientras se espera a Gemini.
- Si la IA responde algo roto, sale un mensaje que se entiende en vez de un error en inglés.
- **Cabecera nueva, igual en las tres apps**: la Configuración se abre desde el menú de tu cuenta (tu foto, arriba a la derecha).
- Unos 35 arreglos más: el trabajo de la IA se retoma si recargas la página, lo que escribe la IA va siempre a su pieza aunque cambies de pieza, filtros de la Biblioteca, el lienzo, y preguntas con el diálogo de la sala en vez de las del navegador.
Versión 0.9.1 (baja el instalador completo: cambia el programa que abre la sala):
- **Arreglo: el Publicador ya no abre la Sala de diseño.** Las dos usaban el mismo puerto interno de la PC: si la sala estaba abierta, al abrir el Publicador salía la sala. Ahora la sala usa el suyo (8767).
- Si otro programa ocupa el puerto de la sala, avisa en vez de abrir la ventana de ese programa.

Versión 0.9.0:
- **Entrar y elegir la carpeta, paso a paso** (igual en las tres apps): entras con Google sin pegar ningún link, eliges la carpeta del equipo (una tuya, una compartida contigo, una nueva o con su link) y la app te dice cómo invitar al equipo como Editor. Si tu cuenta solo puede mirar esa carpeta, te avisa.
- En **Configuración → Cuenta** está la carpeta del proyecto, con «Abrir en Drive» y «Cambiar de carpeta…». Si cambias de carpeta, lo de la anterior en esta PC queda aparte (no se mezcla).
- **Marca → Importar mi marca** (sin Claude): «Descargar plantilla de marca» y subir la carpeta o el .zip (o arrastrarlos). La sala acomoda logos, tipografías, productos y colores (si no los pones, los saca del logo) y te los muestra antes de guardar. Es la misma marca de la Sala de edición.
- **Actualizar más seguro**: el botón dice «⟳ Actualizando…» y una cortina tapa la sala hasta que la versión nueva arranca. Si algo falla, avisa y todo vuelve a como estaba.
- **Más seguridad**: la sala solo acepta órdenes de su propia ventana (una página de internet ya no puede mandarle nada).

Versión 0.8.0:
- **Rehacer foto**: selecciona una foto (o la foto de fondo), escribe qué está mal («tiene arándanos, que se vea el polvo encima de las croquetas») y toca «✎ Rehacer foto». Claude escribe el prompt nuevo de Flow de esa lámina con tu nota y las reglas de la marca, y lo deja copiado para pegarlo en Flow.
- La nota queda guardada en la pieza, con fecha y quién la escribió, y se ve debajo del prompt en «Escribir con Claude». Las notas anteriores de la misma foto también se respetan al rehacerla.

Versión 0.7.0:
- **Fondos variados**: al crear con IA, cada lámina trae su tipo de fondo: **escena** (la foto de Flow ocupa toda la lámina: parque, cielo, sala), **estudio** (pared de un color fuerte) o **color** (animal recortado sobre un color de la marca). Dos láminas seguidas no repiten fondo y todo carrusel lleva al menos una escena.
- En una lámina de escena, el título lleva contorno y el texto una pastilla, para que se lean encima de la foto. Toca la foto de Flow a la izquierda para ponerla de fondo.
- Los prompts de Flow alternan **perro y gato**, cambian de raza y de ángulo (ojo de pez, desde el suelo, desde arriba).
- La sala lee la nueva «direccion_visual» de _MARCA/marca.json (la guía completa está en _MARCA/direccion_visual.md, con fotos de ejemplo en _MARCA/referencias).
- Arreglo: un «\n» escrito a mano en un texto ya no aparece en la lámina; parte la línea.

Versión 0.6.0:
- La **Configuración** tiene el mismo diseño en las tres apps (menú a la izquierda, secciones a la derecha), con **Cuenta y dispositivos** y **Buscar actualizaciones**.
- Todo carrusel termina **siempre** con la lámina de **CTA** de la marca (título, texto, el botón con la acción y la foto real del producto). Si Claude no la pone, la sala la agrega. El texto del CTA está en _MARCA/marca.json → «cta» y se ve en la pestaña Marca.

Versión 0.5.0:
- Arreglo: «Iniciar sesión en Claude» decía que no estaba instalado. La app de escritorio de Claude movió su Claude Code a otra carpeta; la sala ya lo encuentra.
- **Configuración** es una página (pestaña), no una ventana encima: tu cuenta, dispositivos y seguridad, Claude, tu nombre, la marca y la versión. Tocar tu foto arriba lleva ahí.
- Al abrir, la sala va sola a **la semana de hoy**. Cuando empieza una semana nueva se crea sola, y si la estrategia dejó su brief en _SEMANAS, se crean sus piezas día por día.
- **Videos**: el filtro muestra todas las producciones del Drive; las que aún no tienen videos terminados lo dicen.
- **Editor**: doble clic sobre un texto de la lámina para escribir ahí mismo. En el panel, «★ Resaltar lo seleccionado» marca la palabra resaltada (es lo que hacían los *asteriscos*).

Versión 0.4.0:
- La sala ahora tiene pestañas, como la Sala de edición: **Inicio** (la semana día por día, con lo exportado, lo que falta y los últimos pedidos), **Biblioteca** (todo lo creado en todas las semanas, con filtros por tema, mes, semana, fechas, tipo, formato, nivel y estado), **✦ Crear con IA**, **Videos**, **Editor** y **Marca**.
- **Videos**: los videos terminados de la Sala de edición (V.FINALES de cada producción), con su miniatura. «✦ Crear posts» los usa de referencia: Claude lee el video y el guion de su producción y lleva ese mensaje a carruseles y posts.
- En Crear con IA se elige la referencia: nada, los videos de la semana o un video de la Sala de edición. Al lado, los pedidos anteriores.
- Al guardar una pieza se guarda su miniatura para verla en la biblioteca.
- **Marca**: los colores, productos, logos y reglas que la sala lee de _MARCA.

Versión 0.3.1:
- Arreglo de fondo del error «No module named 'getpass'»: el código ya no usa esa pieza, así que «Actualizar ahora» funciona aunque tengas instalado un instalador viejo.

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
