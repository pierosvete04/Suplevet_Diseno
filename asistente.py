"""La IA dentro de la Sala de diseño: escribe el texto de cada lámina, el prompt de Flow de cada foto y el copy.

Hay dos y la sala usa la que haya (Configuración → IA):
  Claude  Claude Code de esta PC con la suscripción (sin API ni claves): el de la app de escritorio de Claude o el que
          se instala aparte. Se entra una sola vez («Iniciar sesión en Claude»). Corre solo, sin ventana.
  Gemini  en Antigravity (gemini.py): la sala lo abre con el pedido listo y toma la respuesta sola.
En «automático» va Claude y, si no tiene sesión o se cae (por ejemplo, se acabó el uso del plan), sigue Gemini.
La sala no sabe de ninguna marca: las reglas salen de _MARCA/marca.json del proyecto.
"""
import glob
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import gemini
import nucleo

_estado = {"t": 0, "datos": None}
MODOS = ("auto", "claude", "gemini")
CLAUDE_MAX = 10 * 60  # si Claude no termina en 10 minutos, se corta (antes se quedaba colgado para siempre)
CLAUDE_FLOW_MAX = 30 * 60  # generar y bajar fotos en Flow tarda más: media hora, como Gemini


def modo():
    m = nucleo.CONFIG.get("ia")
    return m if m in MODOS else "auto"


def elegir_modo(m):
    if m not in MODOS:
        raise ValueError("Modo de IA no válido")
    nucleo.guardar_config({"ia": m})


def encontrar():
    """Ruta de claude.exe o None."""
    candidatos = [shutil.which("claude"), str(Path.home() / ".local" / "bin" / "claude.exe")]
    appdata, local = os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")
    patrones = [os.path.join(appdata, "Claude", "claude-code", "*", "*", "claude.exe"),
                os.path.join(local, "Packages", "Claude_*", "LocalCache", "Roaming", "Claude", "claude-code", "*", "*", "claude.exe"),
                os.path.join(local, "Claude-Data", "*", "claude-code", "*", "*", "claude.exe")]  # app de escritorio desde 2026-10
    candidatos += sorted((p for pat in patrones for p in glob.glob(pat)), key=os.path.getmtime, reverse=True)
    candidatos.append(os.path.join(appdata, "npm", "claude.cmd"))
    return next((c for c in candidatos if c and os.path.isfile(c)), None)


def _sin_ventana():
    return {"creationflags": 0x08000000} if os.name == "nt" else {}


def estado_claude(forzar=False):
    if not forzar and _estado["datos"] and time.time() - _estado["t"] < 30:
        return _estado["datos"]
    ruta = encontrar()
    out = {"instalado": bool(ruta), "sesion": False}
    if ruta:
        try:
            r = subprocess.run([ruta, "auth", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=30, cwd=str(nucleo.DATOS), **_sin_ventana())
            out["sesion"] = bool(json.loads(r.stdout or "{}").get("loggedIn"))
        except (subprocess.SubprocessError, ValueError, OSError):
            pass
    _estado.update(t=time.time(), datos=out)
    return out


def quien(c=None, g=None):
    """Qué IA haría el próximo pedido: «claude», «gemini» o None si no hay ninguna lista."""
    c = c or estado_claude()
    g = g or gemini.estado()
    m = modo()
    if m == "claude":
        return "claude" if c["sesion"] else None
    if m == "gemini":
        return "gemini" if g["instalado"] else None
    return "claude" if c["sesion"] else "gemini" if g["instalado"] else None


def estado(forzar=False):
    """Las dos IA: {claude: {instalado, sesion}, gemini: {instalado}, modo, usa}. (instalado y sesion de Claude
    también arriba, como antes, para la cuenta y las otras partes que ya los leían.)"""
    c, g = estado_claude(forzar), gemini.estado()
    return {**c, "claude": c, "gemini": g, "modo": modo(), "usa": quien(c, g)}


# Errores de Claude que no se arreglan reintentando con Claude: en «automático» el pedido sigue con Gemini
_CLAUDE_CAIDO = ("sesión iniciada", "login", "no encuentro claude", "limit", "límite", "usage", "quota", "rate", "credit",
                 "overloaded", "no respondió", "tardó demasiado", "demasiado largo")


def correr(prompt, avance=print, max_turnos=20, que="pedido", navegador=False):
    """Pasa el pedido a la IA que toque y devuelve su texto final (en el que viene el JSON).
    navegador=True: la IA maneja el navegador de esta PC (Claude: el Chrome con la extensión de Claude; Gemini: el de Antigravity)."""
    usa = quien()
    if not usa:
        m = modo()
        raise RuntimeError("Claude no tiene la sesión iniciada en esta PC. Inicia sesión (Configuración → IA) o cambia a Gemini." if m == "claude"
                           else "Antigravity no está instalado en esta PC. Instálalo (antigravity.google) o cambia a Claude en Configuración → IA." if m == "gemini"
                           else "No hay ninguna IA lista: inicia sesión en Claude o instala Antigravity (Configuración → IA).")
    if usa == "gemini":
        return gemini.correr(prompt, que, avance, navegador)
    try:
        return correr_claude(prompt, avance, max_turnos, chrome=navegador)
    except nucleo.Cancelado:
        raise
    except RuntimeError as e:
        # con el navegador, que Chrome o su extensión no estén también es motivo para seguir con Gemini
        caido = _CLAUDE_CAIDO + (("chrome", "extensión", "extension") if navegador else ())
        if modo() != "auto" or not gemini.estado()["instalado"] or not any(x in str(e).lower() for x in caido):
            raise
        avance(f"Claude no pudo ({str(e)[:120]}). Sigue Gemini en Antigravity…")
        _estado["datos"] = None
        return gemini.correr(prompt, que, avance, navegador)


def iniciar_sesion():
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC. Instala la app de escritorio de Claude.")
    _estado["datos"] = None
    subprocess.Popen(["cmd", "/c", "start", "Claude - iniciar sesion", "/wait", ruta, "auth", "login", "--claudeai"], cwd=str(nucleo.DATOS))


def abrir_chrome(avance):
    """Claude in Chrome necesita Chrome abierto: si está cerrado, se abre (con el último perfil usado) y se le da tiempo
    a la extensión para conectarse. (Lo mismo que la Sala de edición.)"""
    if os.name != "nt":
        return
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"], capture_output=True, text=True, errors="replace", **_sin_ventana())
    if "chrome.exe" in r.stdout:
        return
    rutas = [Path(os.environ.get(v, "")) / "Google" / "Chrome" / "Application" / "chrome.exe"
             for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    chrome = next((p for p in rutas if p.is_file()), None)
    if not chrome:
        raise RuntimeError("No encuentro Google Chrome en esta PC: hace falta Chrome con la extensión de Claude")
    avance("Abriendo Chrome…")
    subprocess.Popen([str(chrome)])
    time.sleep(20)


def correr_claude(prompt, avance=print, max_turnos=20, chrome=False):
    """Corre Claude Code sin ventana, solo para responder (sin tocar archivos). Devuelve el texto final.
    El pedido va por la entrada (stdin) y no en la línea de comandos: Windows corta las órdenes de más de 32.767 letras
    (8.191 con claude.cmd), y un pedido con el guion de un video de referencia las pasa.
    chrome=True: también maneja el Chrome de esta PC con la extensión de Claude (Google Flow con la cuenta del usuario),
    como «Generar en Flow» de la Sala de edición. Tiene más tiempo: generar y bajar fotos tarda."""
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC (Configuración → IA)")
    cmd = [ruta, "-p", "--output-format", "stream-json", "--verbose", "--disallowedTools", "Bash", "Write", "Edit",
           "WebFetch", "WebSearch", "--max-turns", str(max_turnos)]
    if chrome:
        abrir_chrome(avance)
        cmd += ["--chrome", "--allowedTools", "mcp__claude-in-chrome", "Skill"]
    limite = CLAUDE_FLOW_MAX if chrome else CLAUDE_MAX
    p = subprocess.Popen(cmd, cwd=str(nucleo.DATOS), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace", **_sin_ventana())
    nucleo.PROCESOS.add(p)
    errores = []  # stderr se lee aparte: si se llena sin leerlo, Claude se queda trabado esperando
    lector = threading.Thread(target=lambda: errores.append(p.stderr.read()), daemon=True)
    lector.start()
    vencido = threading.Event()

    def cortar():
        vencido.set()
        p.kill()
    reloj = threading.Timer(limite, cortar)
    reloj.daemon = True
    reloj.start()
    final = None
    try:
        p.stdin.write(prompt)
        p.stdin.close()
        for linea in p.stdout:
            try:
                ev = json.loads(linea)
            except ValueError:
                continue
            if ev.get("type") == "assistant":
                for b in ev.get("message", {}).get("content", []):
                    if b.get("type") == "tool_use" and b.get("name", "").startswith("mcp__claude-in-chrome__"):
                        arg = b.get("input", {})  # en Chrome: qué está haciendo, en sus palabras
                        avance("Claude · Chrome · " + str(arg.get("action_summary") or arg.get("action") or b["name"].split("__")[-1])[:140])
                    t = b.get("text", "").strip() if b.get("type") == "text" else ""
                    if t and not t.startswith(("{", "`")):  # el JSON de la respuesta no es un avance
                        avance("Claude · " + t.splitlines()[0][:140])
            elif ev.get("type") == "result":
                final = ev
        p.wait()
    except OSError:
        p.kill()
    finally:
        reloj.cancel()
        nucleo.PROCESOS.discard(p)
    nucleo.revisar_cancelado()
    if vencido.is_set():
        raise RuntimeError(f"Claude tardó demasiado (más de {limite // 60} minutos) y se cortó. Intenta de nuevo.")
    if not final:
        lector.join(2)
        raise RuntimeError("Claude no respondió. " + "".join(errores).strip()[-300:])
    if final.get("is_error"):
        texto = final.get("result") or final.get("subtype") or "error"
        if "login" in texto.lower():
            raise RuntimeError("Claude Code no tiene la sesión iniciada: Configuración → «Iniciar sesión en Claude».")
        raise RuntimeError("Claude: " + texto[:300])
    return final.get("result") or ""


def _json_de(texto, falta):
    """El JSON que viene en la respuesta de la IA; si no hay o está roto, un error que se entiende."""
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fin < 0:
        raise RuntimeError(f"La IA no devolvió {falta}. Intenta de nuevo.")
    try:
        return json.loads(texto[inicio:fin + 1])
    except ValueError:
        raise RuntimeError(f"La IA devolvió {falta} con un error de formato. Intenta de nuevo.") from None


def escribir_pieza(pieza, idea, marca, avance=print):
    """{"laminas": [{"rol", "titulo", "texto", "flow"}], "copy"} para una pieza (carrusel o post)."""
    n = len(pieza.get("laminas", [])) or (4 if pieza.get("tipo") != "post" else 1)
    tipo = "un post de una sola imagen" if pieza.get("tipo") == "post" else f"un carrusel de {n} láminas"
    reglas = {k: marca.get(k) for k in CLAVES_MARCA if marca.get(k)}
    prompt = f"""Escribe {tipo} para Instagram ({pieza.get('formato', '4:5')}).
Tema: {pieza.get('titulo', '')}
{('Idea del equipo: ' + idea.strip()) if idea.strip() else ''}
Nivel del embudo: {pieza.get('nivel') or 'elige tú'} · Público: {pieza.get('publico') or 'clientes finales'} · Estilo visual: {pieza.get('estilo') or 'elige tú'}
Marca y reglas (respétalas al pie de la letra): {json.dumps(reglas, ensure_ascii=False)}

Reglas generales: palabras simples, portada de 8 palabras como máximo, una idea por lámina, títulos de 2 a 6 palabras
y textos de 20 palabras como máximo.
Si es un carrusel, la ÚLTIMA lámina es SIEMPRE el CTA (rol «cta»): invita a escribir y usa el «cta» de la marca (título corto,
texto y la acción). En un post, el CTA va al final del copy.
{FOTOS}
{DISENOS_TEXTO}
Marca con *asteriscos* la palabra que va resaltada en el título.
Responde SOLO con JSON, sin texto antes ni después:
{{"laminas": [{{"rol": "portada | idea | señal | cta", "diseno": "…", "titulo": "…", "texto": "…", "accion": "solo en el CTA", "fondo": "escena | estudio | color", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}"""
    datos = _json_de(correr(prompt, avance=avance, que="escribir"), "la pieza")
    if pieza.get("tipo") != "post":
        datos["laminas"] = con_cta(datos.get("laminas", []), marca)
    return datos


FLOW_FORMATO = {"4:5": "3:4", "1:1": "1:1", "9:16": "9:16"}  # el 4:5 no está en Flow: 3:4 es lo más cercano (896×1200)


def generar_fotos(items, proyecto, descargas, avance=print):
    """«✦ Generar fotos con IA»: la IA abre Google Flow en el navegador de esta PC (con la cuenta del usuario), genera
    una foto por prompt y la baja a Descargas con su código, como «Generar en Flow» de la Sala de edición.
    items: [{id, prompt, formato}] · Devuelve {"archivos": {id: nombre en Descargas}, "pendientes": [{id, motivo}]}."""
    pedido = json.dumps([{"codigo": x["id"], "prompt": x["prompt"], "formato": FLOW_FORMATO.get(x.get("formato"), "3:4")} for x in items],
                        ensure_ascii=False, indent=1)
    prompt = f"""Genera en Google Flow estas {len(items)} imágenes y bájalas a la carpeta Descargas de esta PC ({descargas}).
{pedido}

Si tienes la skill «suplevet-flow-chrome», úsala: tiene el mapa de pantallas de Flow. Los pasos:
1. Abre https://labs.google/flow (la sesión de Google ya está abierta). Abre el proyecto «{proyecto}»; si no existe, créalo («Nuevo proyecto»).
2. En los ajustes del generador (ícono de deslizadores → Configuración del agente → Generación de imágenes predeterminada)
   elige el formato de cada imagen (casi todas «3:4») y x1 (una imagen por prompt). Guarda.
3. Para cada imagen pega su código y su prompt juntos (por ejemplo «C05_N1: …») y envíalo. No esperes a que termine
   una para mandar la siguiente: Flow las hace en paralelo. Si Google rechaza un prompt, cámbialo lo mínimo (sin palabras
   de enfermedad ni de dolor) y reenvíalo una vez; si vuelve a fallar, déjalo en «pendientes».
4. Cuando ya no quede ninguna generándose, baja cada una en tamaño original con su código como nombre («C05_N1.jpg»):
   desde la página, con fetch y un enlace <a download>; en la URL de la imagen cambia «=s512-rw» por «=s0».
- Si Google pide iniciar sesión, elegir cuenta, aceptar términos o un captcha, o si se acabó el cupo: para y dilo en
  «pendientes». Nunca escribas contraseñas, no compres créditos ni cambies el plan. No generes nada que no esté en la lista.
- Cierra las pestañas que abriste al terminar.
Al final responde SOLO con JSON, sin texto antes ni después:
{{"archivos": {{"<código>": "<nombre exacto del archivo en Descargas>"}}, "pendientes": [{{"codigo": "<código>", "motivo": "…"}}]}}"""
    datos = _json_de(correr(prompt, avance=avance, max_turnos=150, que="fotos", navegador=True), "la lista de fotos bajadas")
    if "archivos" not in datos:
        raise RuntimeError("La IA no terminó en Flow. Intenta de nuevo.")
    return datos


def rehacer_foto(pieza, n, nota, marca, avance=print):
    """Reescribe el prompt de Flow de la lámina n con la nota del equipo (qué está mal en la foto). Devuelve {"flow", "cambio"}."""
    laminas = (pieza.get("guion") or {}).get("laminas") or []
    lam = laminas[n] if 0 <= n < len(laminas) else {}
    antes = [x["nota"] for x in lam.get("notas", []) if x.get("nota")]
    reglas = {k: marca.get(k) for k in CLAVES_MARCA if marca.get(k)}
    prompt = f"""Hay que rehacer la foto de la lámina {n + 1} de {'un post' if pieza.get('tipo') == 'post' else 'un carrusel'} para Instagram.
Lámina: {json.dumps({k: lam.get(k) for k in ('rol', 'titulo', 'texto', 'fondo') if lam.get(k)}, ensure_ascii=False)}
Prompt de Google Flow con el que se hizo: {lam.get('flow') or '(no hay: escríbelo desde cero)'}
Lo que está mal, según el equipo: {nota.strip()}
{('Notas anteriores de esta misma foto (también valen): ' + ' | '.join(antes)) if antes else ''}
Marca y reglas (respétalas al pie de la letra): {json.dumps(reglas, ensure_ascii=False)}
{FOTOS}
El prompt lleva el encuadre del formato: {ORIENTACION.get(pieza.get('formato', '4:5'), 'vertical 4:5')}.
Escribe el prompt nuevo completo en inglés (no solo el cambio): corrige lo que dice el equipo y mantén lo que estaba bien.
Responde SOLO con JSON, sin texto antes ni después: {{"flow": "…", "cambio": "qué cambiaste, en una frase en español"}}"""
    datos = _json_de(correr(prompt, avance=avance, max_turnos=10, que="foto"), "el prompt nuevo")
    if not str(datos.get("flow", "")).strip():
        raise RuntimeError("La IA no devolvió el prompt nuevo. Intenta de nuevo.")
    return datos


def con_cta(laminas, marca):
    """Todo carrusel termina con la lámina de CTA de la marca: si Claude no la puso, se agrega."""
    if laminas and (laminas[-1].get("rol") == "cta"):
        return laminas
    cta = marca.get("cta") or {}
    return laminas + [{"rol": "cta", "titulo": cta.get("titulo", "¿Te interesa?"), "texto": cta.get("texto", "Escríbenos y te asesoramos"),
                       "flow": "", "accion": cta.get("boton", "")}]


CLAVES_MARCA = ("nombre", "evitar", "obligatorio", "cierres", "cta", "notas_para_claude", "direccion_visual")
FOTOS = """Para cada lámina elige su «fondo» y escribe el prompt de Google Flow de su foto en inglés:
- «escena»: la foto ocupa toda la lámina, con un lugar real (parque, pasto, cielo, sala, cocina); deja una zona limpia para el título.
- «estudio»: el animal contra una pared lisa de un color fuerte.
- «color»: el animal solo, fácil de recortar; va sobre un color de la marca.
Dos láminas seguidas nunca llevan el mismo fondo y todo carrusel lleva al menos una «escena».
Siempre hay un perro o un gato (alterna los dos y cambia de raza); sin texto ni logos, sin productos ni empaques
(el producto real se pone después). Di el ángulo con palabras (fisheye close-up, low angle from the ground, top-down)
y no uses «--ar». Si la marca trae «direccion_visual», síguela."""


# los diseños de lámina que la sala sabe armar (los mismos de DISENOS en app.html): la IA elige uno por lámina y los rota
DISENOS = {"portada": ("titular", "revista", "pregunta", "dato", "franja", "apilado", "circulo", "tapa", "mensajes"),
           "interna": ("clasica", "numero", "lista", "mito", "chat", "cita", "senales", "mensajes"),
           "cta": ("producto", "comenta", "guardar", "pregunta", "oferta", "testimonio")}
DISENOS_TEXTO = """Cada lámina lleva su «diseno» (cómo se arma en la sala). Elige según lo que dice la lámina y varía: en un carrusel,
dos láminas internas seguidas no repiten diseño, y si son varias piezas, sus portadas y sus CTA tampoco se repiten.
- Portada: «titular» (título grande arriba), «revista» (tapa de revista: título enorme abajo y una etiqueta arriba),
  «pregunta» (el título es una pregunta, va en una burbuja), «dato» (el título empieza con un número o cifra: «7 señales…»),
  «franja» (título en una franja de color sobre la foto), «apilado» (título gigante de 3 a 7 palabras en varias líneas a la
  izquierda; la foto deja libre el lado izquierdo y el animal va a la derecha), «circulo» (el animal recortado dentro de un
  círculo de color y el título enorme abajo; su fondo es «color»), «tapa» (tapa de revista: el nombre de la marca enorme
  arriba, detrás de la cabeza del animal; el texto son 2 a 4 titulares cortos de revista, uno por línea con \\n, que van a los
  costados; la foto es un retrato de estudio del animal centrado, mirando a la cámara, con la cabeza a un tercio de la altura).
- Portada o interna: «mensajes» (el título es como «¡Nos llegó un mensaje!»; el texto son 3 o 4 mensajes cortos de dueños,
  de 3 a 8 palabras, uno por línea con \\n, que van en burbujas de chat alrededor del animal; la foto muestra al animal
  mirando un celular o con cara de sorpresa, al centro, con espacio libre a los lados).
- Internas: «clasica» (título y texto), «numero» (paso o señal numerada: número gigante), «lista» (el texto son 2 a 4 puntos,
  uno por línea, con \\n), «mito» (el título es el mito, el texto es la realidad), «chat» (el título es lo que pregunta un dueño,
  el texto es lo que responde el veterinario), «cita» (el texto es una frase de un dueño entre comillas; el título, quién la dijo),
  «senales» (el texto son 2 a 4 frases cortas de 2 a 5 palabras, una por línea con \\n, que van alrededor del animal con
  flechas; la foto pone al animal al centro, recortado, y su fondo es «color» o «estudio»).
- CTA (la última): «producto» (la bolsa y el botón), «comenta» (en «accion» UNA palabra para comentar, por ejemplo PIEL),
  «guardar» (invita a guardar el post; para TOFU, sin vender), «pregunta» (título en pregunta; en «accion» dos respuestas
  separadas por «/», como «SÍ / A VECES»), «oferta» (en «accion» el envío o la presentación: «ENVÍO A TODO EL PERÚ»),
  «testimonio» (el texto es lo que dijo un cliente; el título, su mascota). TOFU: guardar o comenta; MOFU: comenta, pregunta
  o testimonio; BOFU: producto u oferta."""


ORIENTACION = {"4:5": "vertical 4:5", "1:1": "square 1:1", "9:16": "tall vertical 9:16 (story), leave the top and bottom 15% clean"}
# los estilos visuales de la sala (los mismos del selector «Estilo» del editor)
ESTILOS = {"A": "nariz a cámara", "B": "color sólido", "C": "metáfora", "D": "garabatos", "E": "lifestyle"}
ESTILOS_TEXTO = ", ".join(f"{k} ({v})" for k, v in ESTILOS.items())
# por si Claude responde con palabras en vez de la letra
ESTILO_POR_PALABRA = (("A", ("nariz", "cámara", "camara", "primer plano", "close")), ("B", ("sólido", "solido", "color plano", "liso")),
                      ("C", ("metáfora", "metafora")), ("D", ("garabato", "doodle")), ("E", ("lifestyle", "estilo de vida", "cotidian")))


def estilo_letra(valor):
    """«B», «b · Color sólido» o «una metáfora visual…» -> la letra A–E; si no se entiende, vacío."""
    t = str(valor or "").strip()
    if t[:1].upper() in ESTILOS and (len(t) == 1 or not t[1].isalpha()):
        return t[0].upper()
    t = t.lower()
    return next((letra for letra, palabras in ESTILO_POR_PALABRA if any(p in t for p in palabras)), "")


def solo_elegidos(disenos):
    """{grupo: [diseños]} de «Diseños» en Crear con IA, solo con nombres que la sala conoce."""
    return {g: [d for d in (disenos or {}).get(g) or [] if d in DISENOS[g]] for g in DISENOS if (disenos or {}).get(g)}


def respetar_disenos(laminas, elegidos):
    """Cada lámina usa uno de los diseños elegidos para su parte (portada, internas o CTA). Si la IA puso otro, se cambia
    por uno de los elegidos, rotando para que dos internas seguidas no repitan."""
    for i, l in enumerate(laminas):
        grupo = "cta" if l.get("rol") == "cta" else "portada" if i == 0 else "interna"
        lista, previo = elegidos.get(grupo), laminas[i - 1].get("diseno") if i else None
        if lista and (l.get("diseno") not in lista or (len(lista) > 1 and l.get("diseno") == previo)):
            l["diseno"] = next((d for d in lista[i % len(lista):] + lista if d != previo), lista[0])
    return laminas


def _de_los_guiones(cuerpos):
    """La parte del pedido para «Cuerpos de los guiones»: un carrusel por cuerpo, con su mensaje y sus hooks."""
    if not cuerpos:
        return ""
    datos = [{"n": i + 1, "produccion": c["produccion"], "cuerpo": c["id"], "publico": c.get("publico") or "dueños de mascotas",
              "texto_del_cuerpo": c["texto"], "hooks": c.get("hooks", [])[:5], "ctas": c.get("ctas", [])[:3]} for i, c in enumerate(cuerpos)]
    return f"""
Cuerpos de los guiones de la Sala de edición que eligió el equipo. Haz EXACTAMENTE {len(cuerpos)} carruseles: uno por cada
cuerpo, en este mismo orden (la pieza 1 es del cuerpo n=1, y así).
- Cada carrusel lleva de 5 a 7 láminas y cuenta el mensaje de SU cuerpo, partido en una idea por lámina. No inventes datos
  ni ingredientes: usa solo lo que dice el cuerpo, con palabras simples.
- La portada sale de uno de sus hooks: tómalo y acórtalo a 8 palabras como máximo (que enganche, no copies el hook entero).
  Usa un hook distinto en cada carrusel.
- El título de la pieza dice su tema en pocas palabras (no repitas el mismo título entre piezas).
- Si el público son veterinarios: «publico» es «veterinarios», el tono es de colega a colega (B2B) y el CTA invita a escribir
  por WhatsApp o a agendar una visita (usa sus «ctas»). Si no, el público son dueños de mascotas.
- El nivel: TOFU si el cuerpo explica un problema, MOFU si compara o muestra cómo funciona, BOFU si invita a comprar o pedir.
{json.dumps(datos, ensure_ascii=False)[:30000]}"""


def resolver_pedido(texto, marca, semana="", videos=None, avance=print, referencia=None, disenos=None, cuerpos=None):
    """Un pedido libre («3 posts 1:1 sobre omega 3», «una historia 9:16 con esto: …») -> las piezas a crear.
    videos: los ángulos de los videos de la semana (del brief), para que las piezas los acompañen.
    disenos: los que se marcaron en «Diseños» ({portada: [...], interna: [...], cta: [...]}); en lo que no se marcó, elige la IA.
    Devuelve {"piezas": [{tipo, formato, dia, titulo, nivel, publico, estilo, laminas: [{rol, titulo, texto, flow}], copy}]}."""
    reglas = {k: marca.get(k) for k in CLAVES_MARCA if marca.get(k)}
    elegidos = solo_elegidos(disenos)
    nombres = {"portada": "portadas", "interna": "láminas internas", "cta": "CTA"}
    usar = ("El equipo eligió los diseños. Usa SOLO estos (repártelos entre las piezas y las láminas, sin repetir seguidos): "
            + "; ".join(f"{nombres[g]}: {', '.join(v)}" for g, v in elegidos.items()) + ". En lo demás, elige tú.") if elegidos else ""
    base = ""
    if videos:
        base = "Videos de esta semana (las piezas deben acompañarlos, con el mismo tema y nivel):\n" + json.dumps(videos, ensure_ascii=False)
    if referencia:
        base += ("\nVideo de referencia hecho en la Sala de edición: las piezas llevan ESTE mensaje a post o carrusel "
                 "(si el guion trae varios cuerpos, usa el que corresponde al nombre del video):\n"
                 + json.dumps(referencia, ensure_ascii=False)[:24000])
    base += _de_los_guiones(cuerpos)
    prompt = f"""Eres diseñador de contenido para redes. Este es el pedido del equipo, tal cual lo escribió:
---
{texto.strip()}
---
Semana: {semana}
{base}
Marca y reglas (respétalas al pie de la letra): {json.dumps(reglas, ensure_ascii=False)}

Decide qué piezas hacer según el pedido:
- tipo «carrusel» (4 a 8 láminas) o «post» (1 lámina). Una historia es un post 9:16; varias historias seguidas son un carrusel 9:16.
- formato «4:5» (feed, el de siempre), «1:1» (post cuadrado) o «9:16» (historia). Si el pedido no lo dice, 4:5.
- Si el pedido trae su propio contenido, úsalo tal cual (ordénalo y acórtalo, no inventes datos nuevos).
- Si pide un día (lunes, martes…), ponlo en «dia» como LUN, MAR, MIE, JUE, VIE, SAB o DOM; si no, vacío.
Reglas de escritura: palabras simples, portada de 8 palabras como máximo, una idea por lámina, títulos de 2 a 6 palabras,
textos de 20 palabras como máximo (en 9:16, 12 como máximo).
Todo carrusel termina SIEMPRE con una lámina de CTA (rol «cta») que invita a escribir, con el «cta» de la marca.
En un post de una sola imagen, el CTA va al final del copy.
Marca con *asteriscos* la palabra resaltada del título.
{FOTOS}
El prompt de Flow lleva el encuadre del formato: {json.dumps(ORIENTACION)}.
Si son varias piezas, sus portadas llevan fondos distintos entre sí.
En «estilo» va SOLO una letra: {ESTILOS_TEXTO}.
{DISENOS_TEXTO}
{usar}
Responde SOLO con JSON, sin texto antes ni después:
{{"piezas": [{{"tipo": "carrusel", "formato": "4:5", "dia": "", "titulo": "…", "nivel": "TOFU | MOFU | BOFU", "publico": "…", "estilo": "A | B | C | D | E",
  "laminas": [{{"rol": "portada | idea | señal | cta", "diseno": "…", "titulo": "…", "texto": "…", "accion": "solo en el CTA", "fondo": "escena | estudio | color", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}]}}"""
    avance(("Claude" if quien() == "claude" else "Gemini") + " está leyendo el pedido…")
    datos = _json_de(correr(prompt, avance=avance, max_turnos=25, que="pedido"), "las piezas")
    if not datos.get("piezas"):
        raise RuntimeError("La IA no encontró ninguna pieza en el pedido. Escríbelo con más detalle.")
    for p in datos["piezas"]:
        p["estilo"] = estilo_letra(p.get("estilo"))
        if p.get("tipo") != "post" and len(p.get("laminas") or []) > 1:
            p["laminas"] = con_cta(p.get("laminas", []), marca)
        if elegidos:  # aunque la IA se salga de lo elegido, cada lámina queda con uno de los diseños marcados
            respetar_disenos(p.get("laminas") or [], elegidos)
    if cuerpos:  # cada pieza sabe de qué guion y cuerpo salió (la pieza n es del cuerpo n)
        for p, c in zip(datos["piezas"], cuerpos):
            p["fuente"] = {"produccion": c["produccion"], "ruta": c["ruta"], "cuerpo": c["id"]}
        if len(datos["piezas"]) != len(cuerpos):
            avance(f"Ojo: se pidieron {len(cuerpos)} carruseles y la IA armó {len(datos['piezas'])}.")
    return datos
