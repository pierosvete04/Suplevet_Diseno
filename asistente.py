"""Claude dentro de la Sala de diseño: escribe el texto de cada lámina, el prompt de Flow de cada foto y el copy.

Usa Claude Code de esta PC con la suscripción (sin API ni claves): el que trae la app de escritorio de Claude
o el que se instala aparte. Se entra una sola vez («Iniciar sesión en Claude»). La sala no sabe de ninguna
marca: las reglas salen de _MARCA/marca.json del proyecto (palabras a evitar, frases obligatorias, cierres).
"""
import glob
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import nucleo

_estado = {"t": 0, "datos": None}


def encontrar():
    """Ruta de claude.exe o None."""
    candidatos = [shutil.which("claude"), str(Path.home() / ".local" / "bin" / "claude.exe")]
    appdata, local = os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")
    patrones = [os.path.join(appdata, "Claude", "claude-code", "*", "*", "claude.exe"),
                os.path.join(local, "Packages", "Claude_*", "LocalCache", "Roaming", "Claude", "claude-code", "*", "*", "claude.exe")]
    candidatos += sorted((p for pat in patrones for p in glob.glob(pat)), key=os.path.getmtime, reverse=True)
    candidatos.append(os.path.join(appdata, "npm", "claude.cmd"))
    return next((c for c in candidatos if c and os.path.isfile(c)), None)


def _sin_ventana():
    return {"creationflags": 0x08000000} if os.name == "nt" else {}


def estado(forzar=False):
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


def iniciar_sesion():
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC. Instala la app de escritorio de Claude.")
    _estado["datos"] = None
    subprocess.Popen(["cmd", "/c", "start", "Claude - iniciar sesion", "/wait", ruta, "auth", "login", "--claudeai"], cwd=str(nucleo.DATOS))


def correr(prompt, avance=print, max_turnos=20):
    """Corre Claude Code sin ventana, solo para responder (sin tocar archivos). Devuelve el texto final."""
    ruta = encontrar()
    if not ruta:
        raise RuntimeError("No encuentro Claude Code en esta PC (Configuración → Claude)")
    cmd = [ruta, "-p", prompt, "--output-format", "stream-json", "--verbose", "--disallowedTools", "Bash", "Write", "Edit",
           "WebFetch", "WebSearch", "--max-turns", str(max_turnos)]
    p = subprocess.Popen(cmd, cwd=str(nucleo.DATOS), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                         text=True, encoding="utf-8", errors="replace", **_sin_ventana())
    nucleo.PROCESOS.add(p)
    final = None
    for linea in p.stdout:
        try:
            ev = json.loads(linea)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") == "text" and b.get("text", "").strip():
                    avance("Claude · " + b["text"].strip().splitlines()[0][:140])
        elif ev.get("type") == "result":
            final = ev
    err = p.stderr.read()
    p.wait()
    nucleo.PROCESOS.discard(p)
    nucleo.revisar_cancelado()
    if not final:
        raise RuntimeError("Claude no respondió. " + err.strip()[-300:])
    if final.get("is_error"):
        texto = final.get("result") or final.get("subtype") or "error"
        if "login" in texto.lower():
            raise RuntimeError("Claude Code no tiene la sesión iniciada: Configuración → «Iniciar sesión en Claude».")
        raise RuntimeError("Claude: " + texto[:300])
    return final.get("result") or ""


def escribir_pieza(pieza, idea, marca, avance=print):
    """{"laminas": [{"rol", "titulo", "texto", "flow"}], "copy"} para una pieza (carrusel o post)."""
    n = len(pieza.get("laminas", [])) or (4 if pieza.get("tipo") != "post" else 1)
    tipo = "un post de una sola imagen" if pieza.get("tipo") == "post" else f"un carrusel de {n} láminas"
    reglas = {k: marca.get(k) for k in ("nombre", "evitar", "obligatorio", "cierres", "notas_para_claude") if marca.get(k)}
    prompt = f"""Escribe {tipo} para Instagram ({pieza.get('formato', '4:5')}).
Tema: {pieza.get('titulo', '')}
{('Idea del equipo: ' + idea.strip()) if idea.strip() else ''}
Nivel del embudo: {pieza.get('nivel') or 'elige tú'} · Público: {pieza.get('publico') or 'clientes finales'} · Estilo visual: {pieza.get('estilo') or 'elige tú'}
Marca y reglas (respétalas al pie de la letra): {json.dumps(reglas, ensure_ascii=False)}

Reglas generales: palabras simples, portada de 8 palabras como máximo, una idea por lámina, títulos de 2 a 6 palabras
y textos de 20 palabras como máximo. La última lámina cierra con uno de los cierres de la marca.
Para cada lámina escribe el prompt de Google Flow de su foto en inglés: un solo animal o persona, sin texto,
sin productos ni empaques (el producto real se pone después), fondo liso o fácil de recortar.
Marca con *asteriscos* la palabra que va resaltada en el título.
Responde SOLO con JSON, sin texto antes ni después:
{{"laminas": [{{"rol": "portada | idea | señal | cierre", "titulo": "…", "texto": "…", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}"""
    texto = correr(prompt, avance=avance)
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fin < 0:
        raise RuntimeError("Claude no devolvió la pieza. Intenta de nuevo.")
    return json.loads(texto[inicio:fin + 1])


ORIENTACION = {"4:5": "vertical 4:5", "1:1": "square 1:1", "9:16": "tall vertical 9:16 (story), leave the top and bottom 15% clean"}


def resolver_pedido(texto, marca, semana="", videos=None, avance=print):
    """Un pedido libre («3 posts 1:1 sobre omega 3», «una historia 9:16 con esto: …») -> las piezas a crear.
    videos: los ángulos de los videos de la semana (del brief), para que las piezas los acompañen.
    Devuelve {"piezas": [{tipo, formato, dia, titulo, nivel, publico, estilo, laminas: [{rol, titulo, texto, flow}], copy}]}."""
    reglas = {k: marca.get(k) for k in ("nombre", "evitar", "obligatorio", "cierres", "notas_para_claude") if marca.get(k)}
    base = ""
    if videos:
        base = "Videos de esta semana (las piezas deben acompañarlos, con el mismo tema y nivel):\n" + json.dumps(videos, ensure_ascii=False)
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
textos de 20 palabras como máximo (en 9:16, 12 como máximo). La última lámina cierra con uno de los cierres de la marca.
Marca con *asteriscos* la palabra resaltada del título.
Para cada lámina escribe el prompt de Google Flow de su foto en inglés, con el encuadre del formato
({json.dumps(ORIENTACION)}): un solo animal o persona, sin texto, sin productos ni empaques (el producto real se pone después),
fondo liso de un color de la marca o fácil de recortar.
Responde SOLO con JSON, sin texto antes ni después:
{{"piezas": [{{"tipo": "carrusel", "formato": "4:5", "dia": "", "titulo": "…", "nivel": "TOFU | MOFU | BOFU", "publico": "…", "estilo": "…",
  "laminas": [{{"rol": "portada | idea | señal | cierre", "titulo": "…", "texto": "…", "flow": "…"}}], "copy": "copy con 3 a 5 hashtags"}}]}}"""
    avance("Claude está leyendo el pedido…")
    respuesta = correr(prompt, avance=avance, max_turnos=25)
    inicio, fin = respuesta.find("{"), respuesta.rfind("}")
    if inicio < 0 or fin < 0:
        raise RuntimeError("Claude no devolvió las piezas. Intenta de nuevo.")
    datos = json.loads(respuesta[inicio:fin + 1])
    if not datos.get("piezas"):
        raise RuntimeError("Claude no encontró ninguna pieza en el pedido. Escríbelo con más detalle.")
    return datos
