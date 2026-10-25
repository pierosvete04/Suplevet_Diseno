"""Gemini en Antigravity: la otra IA de la sala, para cuando Claude no está (o si se elige en Configuración).

La sala arma una carpeta con el pedido (INSTRUCCIONES.md y GEMINI.md) y se lo pasa a Gemini:
  1. Sola: Antigravity trae «agentapi» (language_server.exe agentapi new-conversation …), que abre una conversación
     con un mensaje. Pide la dirección de su servidor, su código CSRF y un proyecto: la sala los saca del proceso que
     está corriendo (puertos que escucha y su línea de comandos) y de la última conversación guardada.
  2. Si eso falla (Antigravity cambió, no hay proyecto…), como en la Sala de edición: abre Antigravity con la carpeta y
     copia el mensaje para que la persona lo pegue.
Gemini deja su respuesta en respuesta.json y la sala la toma sola apenas aparece.

  ACTUAL  lo que la página muestra mientras se espera a Gemini: {carpeta, mensaje, abierto, copiado, enviado, desde}
"""
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import nucleo

CARPETAS = nucleo.DATOS / "gemini"
ESPERA_MAX = 30 * 60  # Gemini tiene media hora para responder; después se da por perdido
ACTUAL = {}
# sin tildes a propósito: se pega en el chat tal cual y el portapapeles de Windows no siempre las respeta
MENSAJE = ("Lee el archivo INSTRUCCIONES.md de esta carpeta y haz exactamente lo que dice. "
           "Escribe tu respuesta en el archivo respuesta.json de esta misma carpeta y despues responde solo: listo.")


def exe():
    """Antigravity.exe si está instalado en esta PC."""
    for base in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")):
        f = Path(base) / ("Programs" if base == os.environ.get("LOCALAPPDATA") else "") / "Antigravity" / "Antigravity.exe"
        if base and f.exists():
            return f
    return None


def estado():
    return {"instalado": bool(exe())}


def _sin_ventana():
    return {"creationflags": 0x08000000} if os.name == "nt" else {}


def copiar_mensaje():
    """Deja el mensaje para Gemini en el portapapeles de Windows. True si se pudo."""
    try:
        subprocess.run(["clip"], input=MENSAJE.encode("utf-16-le"), timeout=10, check=True, **_sin_ventana())
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def abrir(carpeta=None):
    """Abre Antigravity con la carpeta del pedido (o, si no está instalado, la carpeta en el Explorador)."""
    carpeta = Path(carpeta or ACTUAL.get("carpeta") or CARPETAS)
    ag = exe()
    try:
        subprocess.Popen([str(ag), str(carpeta)] if ag else ["explorer", str(carpeta)])
    except OSError:
        return False
    return bool(ag)


# ---------- Mandarle el pedido a Antigravity sin que nadie pegue nada (agentapi) ----------
GEMINI_DIR = Path.home() / ".gemini" / "antigravity"
_NO_EXISTE = "00000000-0000-0000-0000-000000000000"


def _servidor():
    """(language_server.exe, código CSRF, pid) del Antigravity abierto, o None."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='language_server.exe'\" | "
          "Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20, **_sin_ventana())
        procesos = json.loads(r.stdout or "[]")
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    for p in procesos if isinstance(procesos, list) else [procesos]:
        csrf = re.search(r"--csrf_token[ =](\S+)", p.get("CommandLine") or "")
        if csrf and "antigravity" in (p.get("CommandLine") or "") and p.get("ExecutablePath"):
            return p["ExecutablePath"], csrf.group(1), int(p["ProcessId"])
    return None


def _puertos(pid):
    """Los puertos de 127.0.0.1 en los que escucha ese proceso."""
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=20, **_sin_ventana())
    except (OSError, subprocess.SubprocessError):
        return []
    # «0.0.0.0:0» = escuchando (la palabra LISTENING sale traducida en Windows en español: ESCUCHANDO)
    return [int(m.group(1)) for m in re.finditer(rf"127\.0\.0\.1:(\d+)\s+0\.0\.0\.0:0\s+\S+\s+{pid}\s*$", r.stdout, re.M)]


def _agentapi(srv, env, *args):
    exe, csrf, _ = srv
    r = subprocess.run([exe, "agentapi", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=60, env={**os.environ, "ANTIGRAVITY_CSRF_TOKEN": csrf, **env}, **_sin_ventana())
    try:
        return json.loads(r.stdout or "{}")
    except ValueError:
        return {"error": (r.stdout or r.stderr or "sin respuesta").strip()[:300]}


def _proyecto(srv, env):
    """El proyecto de Antigravity de la última conversación guardada (sin proyecto, no deja abrir una)."""
    brain = GEMINI_DIR / "brain"
    if not brain.is_dir():
        return None
    ids = sorted((d for d in brain.iterdir() if d.is_dir() and re.fullmatch(r"[0-9a-f-]{36}", d.name)),
                 key=lambda d: d.stat().st_mtime, reverse=True)
    for d in ids[:5]:
        meta = _agentapi(srv, env, "get-conversation-metadata", d.name)
        pid = re.search(r'"projectId":\s*"([0-9a-f-]{36})"', json.dumps(meta))
        if pid:
            return pid.group(1)
    return None


def enviar(mensaje, esperar=45):
    """Abre una conversación de Gemini en el Antigravity abierto con el mensaje. Devuelve "" si se pudo o por qué no."""
    fin = time.time() + esperar
    srv = _servidor()
    while not srv and time.time() < fin:  # se acaba de abrir: su servidor tarda unos segundos en arrancar
        time.sleep(3)
        srv = _servidor()
    if not srv:
        return "Antigravity no está abierto"
    try:
        env = None
        while not env and time.time() < fin:
            for puerto in _puertos(srv[2]):
                prueba = _agentapi(srv, {"ANTIGRAVITY_LS_ADDRESS": f"127.0.0.1:{puerto}"}, "get-conversation-metadata", _NO_EXISTE)
                if "connection error" not in json.dumps(prueba) and "CSRF" not in json.dumps(prueba):
                    env = {"ANTIGRAVITY_LS_ADDRESS": f"127.0.0.1:{puerto}"}
                    break
            else:
                time.sleep(3)
        if not env:
            return "no encontré el servidor de Antigravity"
        proyecto = _proyecto(srv, env)
        if not proyecto:
            return "Antigravity no tiene ningún proyecto (ábrelo una vez y empieza una conversación)"
        r = _agentapi(srv, {**env, "ANTIGRAVITY_PROJECT_ID": proyecto}, "new-conversation", "--model=flash",
                      "--title=Sala de diseño", mensaje)
    except (OSError, subprocess.SubprocessError) as e:
        return str(e)[:200]
    return "" if (r.get("response") or {}).get("newConversation") else str(r.get("error") or "no respondió")[:200]


def _leer_respuesta(f):
    """El JSON de respuesta.json (Gemini a veces lo envuelve en ```json … ```), o None si todavía no está completo."""
    try:
        texto = f.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fin < 0:
        return None
    try:
        json.loads(texto[inicio:fin + 1])
    except ValueError:
        return None
    return texto[inicio:fin + 1]


def _limpiar_viejas():
    """Las carpetas de pedidos de hace más de 7 días ya no sirven."""
    if not CARPETAS.exists():
        return
    for d in CARPETAS.iterdir():
        try:
            if d.is_dir() and time.time() - d.stat().st_mtime > 7 * 86400:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def correr(prompt, que="pedido", avance=print):
    """Le pasa el pedido a Gemini en Antigravity y espera su respuesta. Devuelve el texto JSON que dejó en respuesta.json."""
    if not exe():
        raise RuntimeError("Antigravity no está instalado en esta PC. Instálalo desde antigravity.google o conecta Claude (Configuración → IA).")
    _limpiar_viejas()
    carpeta = CARPETAS / time.strftime(f"{que}-%Y%m%d-%H%M%S")
    carpeta.mkdir(parents=True, exist_ok=True)
    respuesta = carpeta / "respuesta.json"
    texto = f"""# Pedido de la Sala de diseño

Trabaja solo en esta carpeta ({carpeta}). No hace falta el navegador ni otros archivos: todo lo que necesitas está aquí abajo.
Gemini Flash basta: no hace falta pensar mucho, solo seguir las reglas al pie de la letra.

## Lo que hay que hacer

{prompt}

## Cómo entregar

1. Escribe SOLO el JSON pedido (sin texto antes ni después, sin ```) en el archivo `respuesta.json` de esta carpeta.
2. Revisa que sea JSON válido: comillas dobles, sin comas sobrantes y los saltos de línea dentro de un texto como \\n.
3. Responde en el chat solo «listo». La Sala de diseño toma el archivo sola.
"""
    (carpeta / "INSTRUCCIONES.md").write_text(texto, encoding="utf-8")
    (carpeta / "GEMINI.md").write_text(texto, encoding="utf-8")  # Antigravity lee GEMINI.md solo al abrir la carpeta
    # 1) sola: si Antigravity no está abierto se abre (con la carpeta) y se le manda el pedido por agentapi
    avance("Pasándole el pedido a Gemini en Antigravity…")
    ya_estaba = bool(_servidor())
    abierto = ya_estaba or abrir(carpeta)
    directo = (f"Lee el archivo {carpeta / 'INSTRUCCIONES.md'} y haz exactamente lo que dice. "
               f"Escribe tu respuesta en el archivo {respuesta} y despues responde solo: listo.")
    porque = enviar(directo) if abierto else "Antigravity no se pudo abrir"
    # 2) si no se pudo, como en la Sala de edición: el mensaje queda copiado y la persona lo pega en esa carpeta
    copiado = bool(porque) and copiar_mensaje()
    if porque and ya_estaba:
        abrir(carpeta)
    ACTUAL.clear()
    ACTUAL.update(carpeta=str(carpeta), mensaje=MENSAJE, abierto=abierto, copiado=copiado, enviado=not porque,
                  desde=time.time())
    avance("Gemini está escribiendo en Antigravity (no hace falta tocar nada)…" if not porque else
           f"No pude pasarle el pedido solo ({porque}): pega el mensaje en el chat de Antigravity (ya está copiado)…")
    try:
        aviso_roto = 0.0
        while time.time() - ACTUAL["desde"] < ESPERA_MAX:
            if nucleo.CANCELAR.is_set():
                nucleo.revisar_cancelado()
            if respuesta.exists():
                listo = _leer_respuesta(respuesta)
                if listo:
                    avance("Gemini respondió: armando…")
                    return listo
                # el archivo está, pero a medias o con un error: se espera (puede estar escribiéndolo) y se avisa
                if time.time() - respuesta.stat().st_mtime > 20 and time.time() - aviso_roto > 60:
                    aviso_roto = time.time()
                    avance("El respuesta.json que dejó Gemini tiene un error de formato: pídele en Antigravity que lo revise y lo corrija.")
            time.sleep(2)
        raise RuntimeError("Gemini no respondió en 30 minutos. Vuelve a intentarlo.")
    finally:
        ACTUAL.clear()
