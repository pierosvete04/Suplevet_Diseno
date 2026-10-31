Versión 0.21.0: con otra cuenta no se ve nada de la anterior
- **Con otra cuenta ya no se ve ni se sube nada de la cuenta anterior.** La llave de Google siempre trabaja con la carpeta que elegiste: si quedó apuntando a otra (pasó en una PC con la cuenta de Mr Peanut, que veía las sesiones de Suplevet), la app la arregla sola al abrir y cada 10 minutos.
- La copia de esta PC (marca, piezas y listas de videos y guiones) es de una sola carpeta. Si entras con otra cuenta, aunque sea desde otra de las tres apps, la copia de la anterior se guarda aparte y deja de verse; si vuelves a esa cuenta, vuelve tal cual.

Versión 0.20.2: menú de la cuenta más corto
- **Menú de tu cuenta más corto:** solo «👤 Cuenta y dispositivos» y «⚙ Configuración». Configuración abre la página con todas las secciones (Actualizaciones incluida) y lleva un punto de aviso cuando hay una versión nueva.
- Si falla la consulta de la cuenta a Google, la app igual anota esta PC en «Dispositivos».

Versión 0.20.1: otra cuenta ya no termina usando la de antes
- **Otra cuenta ya no termina usando la cuenta de antes.** Un proceso de Drive que había empezado antes de entrar podía volver a poner la llave de la cuenta anterior (la pantalla decía la cuenta nueva, pero se trabajaba con la vieja y se veían sus sesiones y su marca). Ahora cada entrada y cada cambio de carpeta guarda la llave aparte, y eso ya no puede pasar.
- Cada 10 minutos la app confirma con Google con qué cuenta está trabajando, y esa es la que muestra.
- Al entrar con otra cuenta ya no se ofrece «La de antes» (la carpeta de la cuenta anterior).

Versión 0.20.0: cuenta nueva con marca
- **Cuenta nueva con marca.** Al entrar por primera vez, después de elegir la carpeta, ahora hay un paso «Marca» (Entrar → Carpeta → Marca → Equipo): nombre de la marca, cómo te compran, qué vendes, a quién le vendes y dos colores. Se guarda una sola vez en el Drive del equipo y la ven las tres apps. Si la carpeta ya tiene marca, el paso no sale.
- En las salas, el mismo paso trae «⬇ Descargar plantilla de marca» y «⬆ Subir la plantilla llena» (o una carpeta o un .zip): la app muestra lo que encontró y lo guarda con «Guardar mi marca».
- Si Google acepta pero no se puede leer tu correo (internet que se corta), la entrada ya no se pierde.

Versión 0.19.4: actualizar desde la pantalla de entrar
- **La pantalla de entrar avisa si hay una versión nueva.** Antes el aviso salía solo después de entrar con Google, así que si entrar fallaba no había cómo recibir el arreglo. Ahora aparece «⟳ Hay una versión nueva» con el botón «Actualizar ahora» arriba de «Entrar con Google».

Versión 0.19.3: entrar con Google sin quedarse trabado
- **Entrar con Google ya no se queda trabado.** Si la página de Google no aparece (no se abrió, quedó detrás de la app o se cerró la pestaña), la pantalla de entrar muestra «¿No ves la página de Google?» con el link para copiar y los botones «Abrir Google otra vez» y «Cancelar».
- Un intento de entrar que quedó esperando se corta al intentar de nuevo (antes ocupaba el puerto de Google y el nuevo se quedaba esperando detrás). Si pasan 10 minutos sin aceptar, se avisa y se puede volver a intentar.
- Si otra de las tres apps ya está esperando a Google, se avisa con claridad.

Versión 0.19.2: las tres apps se ven igual
- Las tres apps se ven y se sienten igual: el mismo bloque de estilo en la Sala de edición, la Sala de diseño y el Publicador.
- Botones del mismo alto en las tres (36 px; los chicos, 30 px), con el texto centrado.
- Avisos flotantes iguales: abajo al centro, con una franja del color del estado (verde listo, ámbar cuidado, rojo error, azul información).
- Etiquetas (✓ Listo, Por rearmar…) del mismo tamaño y letra; los rótulos de sección en mayúsculas; los títulos con las mismas medidas.
- La rueda de «cargando» es la misma en todas.

Versión 0.19.1: bordes iguales en las tres apps
- Bordes iguales en las tres apps: las casillas para escribir o elegir y los botones con esquinas de 9 px, las tarjetas de 14 px y las ventanas de 16 px. La muestra del selector de color también se ve redondeada.
- Las casillas de fecha y de búsqueda ya tienen el estilo de la sala (antes salían con el cuadro del navegador).

Versión 0.19.0: la ficha de marca ahora es un Excel
- **«Plantilla de marca» trae un Excel con casillas** (en vez del Word): tu marca (qué vendes, a quién, tono, cómo te compran, tipografías), tus colores con su código (#253C61) y para qué se usa cada uno, todas tus palabras (el nombre de la marca, las del producto, las que se resaltan, las frases de compra, lo que nunca se dice y cómo la escribe mal la transcripción), las reglas de las imágenes y de la música, y tus públicos. Llénalo, guárdalo en la carpeta con tus logos y tipografías, y súbela en Marca → «Importar mi marca».
- Lo que la ficha trae para los videos queda en la carpeta de la marca en Drive (perfil.json) y lo usa la Sala de edición: es la misma marca para las dos salas.
- Un color con código malo avisa en vez de perderse; acepta códigos cortos (#F36); una hoja del Excel renombrada se reconoce igual. La ficha en Word de antes se sigue leyendo.
- La pantalla dice «Antigravity» (antes decía «Gemini»).

Versión 0.18.1: el editor ya no pierde ni mezcla lo que haces
- Si cambias de semana justo después de editar, lo último se guarda en la semana de la pieza (antes caía en la otra y creaba una pieza fantasma).
- «Deshacer» ya no borra el copy que escribiste.
- Al agregar, duplicar, borrar o mover láminas, los prompts de Flow, los diseños y los textos de la IA se mueven con ellas: «Generar fotos con IA» y «↻ Otro» ya no usan los de otra lámina.
- Si un guardado falla, la pieza sigue «Sin guardar» y se reintenta; antes de abrir otra pieza, la sala pregunta si quieres perder esos cambios.
- Si la pieza cambió por fuera mientras la editabas (la IA puso fotos, u otra PC la guardó), la sala pregunta cuál queda en vez de pisarla sin avisar.
- Lo que editas a mano se sube solo a Drive unos 20 segundos después del último cambio (antes solo subía al exportar) y lo que falte, al cerrar la sala. Lo último antes de cerrar o recargar ya no se pierde.
- Las flechas, Supr y Ctrl+Z solo actúan en el Editor (antes movían o borraban la capa elegida desde Inicio o Biblioteca). Las fotos que sueltas en «Importar marca» ya no se suben también a la pieza abierta.
Versión 0.18.0:
- **Los trabajos de la IA ya no se chocan.** Antes, si pedías algo mientras la IA trabajaba, salía «Ya hay un trabajo en curso», un pedido podía recibir el resultado de otro y «Cancelar» cortaba lo que estuviera corriendo. Ahora cada pedido (escribir, generar fotos, revisar, crear con IA) tiene su número y **espera su turno en una fila**: corren de a uno porque todos usan la misma IA, el mismo Chrome para Flow y la misma semana. Puedes pedir varios seguidos y cada caja dice «En la fila: va después de…».
- **La tuerca ⚙ (arriba a la derecha)**: dice cuántos procesos hay y gira mientras uno corre. Al tocarla se ven el que corre ahora (qué hace y hace cuánto), los que esperan en la fila (con «Quitar de la fila») y los últimos terminados (cuánto tardaron, si fallaron y por qué, con «Abrir» o «Ver propuesta»).
- Lo que escribe la IA (textos y prompts de Flow) queda guardado en su pieza aunque cierres o recargues la página. Si recargas, la sala retoma todos los trabajos que siguen en la fila.
- **↻ Refrescar** (arriba, junto a la tuerca): trae todo de nuevo desde Drive: piezas, marca, briefs, videos y guiones.
- **+ Nueva semana**, en Inicio, junto a la semana que estás viendo: «Esta semana», «La próxima», «En dos semanas» u otra fecha, con su nombre o tema. Antes de crearla dice cómo se va a llamar («S04 · 26 OCT-1 NOV · PIEL SANA»), si ya existe y si la estrategia ya dejó su brief con piezas. En Inicio también se puede cambiar de semana.
Versión 0.17.0:
- **Revisión de cada pieza**, en el editor: arriba, junto a la guía, dice «⚠ N avisos» o «✓ Sin avisos». Al tocarlo se abre el panel «Revisión».
  - **Reglas automáticas** (al instante, sin IA): letra menor a 28 px; texto que casi no se ve sobre lo que tiene detrás (la sala mira los píxeles de la foto o el color, no adivina); texto que se sale de la lámina, que choca con la barra del pie o que queda encima de otro; demasiadas palabras; dos láminas seguidas con el mismo diseño o el mismo fondo; el «Desliza» puesto a mano que ahora repite la barra del pie; y en la semana: el mismo título, la misma portada o el mismo CTA que otra pieza.
  - Cada aviso tiene «Ir» y, si se puede, su arreglo («Subir a 28 px», «Hacerlo legible», «Subir lo de abajo», «Quitarlo»…). «Arreglar lo automático» hace todos juntos, y «Deshacer» los vuelve atrás de una vez.
  - Al exportar, los errores graves también se avisan.
- **✦ Revisar con ojo de IA**: la sala arma las láminas como imágenes y la IA (Claude o Gemini) las mira como un director de arte. Devuelve una nota del 1 al 10, un resumen y cambios concretos (otro diseño, mover, agrandar, otro color de la marca, otro fondo, acortar un texto, hacerlo legible). Marcas los que quieres y «Aplicar los marcados»: los aplica el código, exacto, y «Deshacer» los vuelve atrás.
Versión 0.16.0:
- **Piezas desde los guiones de la Sala de edición**: en «✦ Crear con IA → Usar como referencia», la opción nueva **«Cuerpos de los guiones»** muestra cada producción (P02, P03, P04…) con sus cuerpos, su texto y su primer hook. Marca los que quieras (hasta 12) y sale **un carrusel por cada cuerpo**: la portada sale de uno de sus hooks, el contenido es el del cuerpo (sin inventar datos) y, si la producción es para veterinarios, va en tono B2B con su CTA de WhatsApp o visita.
- El texto del pedido es opcional cuando eliges cuerpos (sirve para pedir algo más: un día, un formato, un tono).
- Cada pieza queda marcada «De un guion» y la tarjeta dice de cuál: «Guion P04 · C3».
- Los guiones se leen de Drive solo para leer, al abrir la sala y por detrás, y quedan guardados en esta PC: la lista sale al instante. Si un guion está copiado en dos carpetas, sale una sola vez.
Versión 0.15.0:
- **Dos diseños nuevos**: «Tapa de revista» (portada: la marca enorme detrás del animal, titulares a los costados, el título abajo y un sticker «Especial» con el tema de la semana) y «Mensajes» (portada o interna: burbujas de chat azules alrededor del animal, para testimonios o preguntas de dueños). Ya son 23.
- **Crear con IA → «Diseños»**: todos los diseños con su vista previa (con tus colores, tu tipografía y tu bolsa), en tres filas: Portada, Láminas internas y CTA. Marca los que quieras (varios por fila); en la fila que no marques nada, la IA elige.
- La IA usa solo los diseños marcados y los reparte sin repetirlos seguidos. Si se sale, la sala lo corrige sola.
Versión 0.14.0:
- **Diseños de lámina con variaciones**: la IA elige un diseño para cada lámina y los va rotando, para que los carruseles no salgan todos iguales.
  - **Portada (7):** Titular, Revista, Pregunta en burbuja, Dato grande, Franja de color, Título apilado y Animal en círculo.
  - **Internas (7):** Clásica, Número grande, Checklist, Mito vs. realidad, Chat dueño y veterinario, Cita de un dueño y Señales alrededor del animal.
  - **CTA (6):** Producto y botón, Comenta una palabra, Guárdalo, Pregunta con botones, Oferta o envío y Testimonio. La IA lo elige según el nivel (TOFU sin vender; BOFU con la bolsa).
  - En el editor, con la lámina elegida (sin tocar nada encima), «Diseño de la lámina» la cambia y «↻ Otro» prueba el siguiente. Se rearma con sus mismos textos; las fotos y lo agregado a mano se quedan.
  - Las piezas de antes se ven igual que siempre hasta que les cambies el diseño.
- **Barra en el pie de cada lámina** del carrusel: «01 / 06», los puntos de avance y «DESLIZA →» (la última, sin «desliza»). Lleva el número correcto aunque agregues, borres o muevas láminas, y sale al exportar. En el panel de la lámina, «Pie de las láminas» deja elegir solo el número, solo los puntos, solo «Desliza» o sin pie.
- Todo funciona en 4:5, 1:1 y 9:16 (en historias, la barra queda encima de la zona que tapa Instagram).
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
