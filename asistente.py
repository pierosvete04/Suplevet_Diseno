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


def correr(prompt, avance=print, max_turnos=20, que="pedido"):
    """Pasa el pedido a la IA que toque y devuelve su texto final (en el que viene el JSON)."""
    usa = quien()
    if not usa:
        m = modo()
        raise RuntimeError("Claude no tiene la sesión iniciada en esta PC. Inicia sesión (Configuración → IA) o cambia a Gemini." if m == "claude"
                           else "Antigravity no está instalado en esta PC. Instálalo (antigravity.google) o cambia a Claude en Configuración → IA." if m == "gemini"
                           else "No hay ninguna IA lista: inicia sesión en Claude o instala Antigravity (Configuración → IA).")
    if usa == "gemini":
        return gemini.correr(prompt, que, avance)
    try:
        return correr_claude(prompt, avance, max_turnos)
    except nucleo.Cancelado:
        raise
    except RuntimeError as e:
        if modo() != "auto" or not gemini.estado()["instalado"] or not any(x in str(e).lower() for x in _CLAUDE_CAIDO):
            raise
        avance(f"Claude no pudo ({str(e)[:120]}). Sigue Gemini en Antigravity…")
        _estado["datos"] = None
        return gemini.correr(prompt, que, avance)


def iniciar_sesion():
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC. Instala la app de escritorio de Claude.")
    _estado["datos"] = None
    subprocess.Popen(["cmd", "/c", "start", "Claude - iniciar sesion", "/wait", ruta, "auth", "login", "--claudeai"], cwd=str(nucleo.DATOS))


def correr_claude(prompt, avance=print, max_turnos=20):
    """Corre Claude Code sin ventana, solo para responder (sin tocar archivos). Devuelve el texto final.
    El pedido va por la entrada (stdin) y no en la línea de comandos: Windows corta las órdenes de más de 32.767 letras
    (8.191 con claude.cmd), y un pedido con el guion de un video de referencia las pasa."""
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC (Configuración → IA)")
    cmd = [ruta, "-p", "--output-format", "stream-json", "--verbose", "--disallowedTools", "Bash", "Write", "Edit",
           "WebFetch", "WebSearch", "--max-turns", str(max_turnos)]
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
    reloj = threading.Timer(CLAUDE_MAX, cortar)
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
        raise RuntimeError(f"Claude tardó demasiado (más de {CLAUDE_MAX // 60} minutos) y se cortó. Intenta de nuevo.")
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
Marca con *asteriscos* la palabra que va resaltada en el título.
Responde SOLO con JSON, sin texto antes ni después:
{{"laminas": [{{"rol": "portada | idea | señal | cta", "titulo": "…", "texto": "…", "fondo": "escena | estudio | color", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}"""
    datos = _json_de(correr(prompt, avance=avance, que="escribir"), "la pieza")
    if pieza.get("tipo") != "post":
        datos["laminas"] = con_cta(datos.get("laminas", []), marca)
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


def resolver_pedido(texto, marca, semana="", videos=None, avance=print, referencia=None):
    """Un pedido libre («3 posts 1:1 sobre omega 3», «una historia 9:16 con esto: …») -> las piezas a crear.
    videos: los ángulos de los videos de la semana (del brief), para que las piezas los acompañen.
    Devuelve {"piezas": [{tipo, formato, dia, titulo, nivel, publico, estilo, laminas: [{rol, titulo, texto, flow}], copy}]}."""
    reglas = {k: marca.get(k) for k in CLAVES_MARCA if marca.get(k)}
    base = ""
    if videos:
        base = "Videos de esta semana (las piezas deben acompañarlos, con el mismo tema y nivel):\n" + json.dumps(videos, ensure_ascii=False)
    if referencia:
        base += ("\nVideo de referencia hecho en la Sala de edición: las piezas llevan ESTE mensaje a post o carrusel "
                 "(si el guion trae varios cuerpos, usa el que corresponde al nombre del video):\n"
                 + json.dumps(referencia, ensure_ascii=False)[:24000])
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
Responde SOLO con JSON, sin texto antes ni después:
{{"piezas": [{{"tipo": "carrusel", "formato": "4:5", "dia": "", "titulo": "…", "nivel": "TOFU | MOFU | BOFU", "publico": "…", "estilo": "A | B | C | D | E",
  "laminas": [{{"rol": "portada | idea | señal | cta", "titulo": "…", "texto": "…", "fondo": "escena | estudio | color", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}]}}"""
    avance(("Claude" if quien() == "claude" else "Gemini") + " está leyendo el pedido…")
    datos = _json_de(correr(prompt, avance=avance, max_turnos=25, que="pedido"), "las piezas")
    if not datos.get("piezas"):
        raise RuntimeError("La IA no encontró ninguna pieza en el pedido. Escríbelo con más detalle.")
    for p in datos["piezas"]:
        p["estilo"] = estilo_letra(p.get("estilo"))
        if p.get("tipo") != "post" and len(p.get("laminas") or []) > 1:
            p["laminas"] = con_cta(p.get("laminas", []), marca)
    return datos
