"""Google Drive como base de datos de las salas, con rclone (sin Google Drive para escritorio y sin APIs de pago).

La llave es una sola para las tres salas de esta PC: vive en %LOCALAPPDATA%/Salas (nucleo.SUITE):
  rclone.conf   la llave de acceso (no se comparte entre PCs)
  drive.json    el link de la carpeta del proyecto y si está activa
  herramientas/rclone.exe

Cada sala trabaja sobre su copia local (datos/drive) y sincroniza con Drive:
  - sube solo lo suyo (cada carpeta de Drive tiene un solo programa que escribe),
  - baja con --update: nunca pisa algo más nuevo de esta PC.
Si la Sala de edición ya estaba conectada en esta PC, su llave se reusa (no hay que entrar de nuevo).
"""
import io
import json
import os
import re
import subprocess
import threading
import urllib.request
import zipfile
from pathlib import Path

import nucleo

REMOTO = "proyecto"
CONF = nucleo.SUITE / "rclone.conf"
INFO = nucleo.SUITE / "drive.json"
CACHE = nucleo.DATOS / "drive"
_candado = threading.Lock()


def rclone():
    """Ruta de rclone.exe; si no está, lo baja de la página oficial (una sola vez, ~30 MB)."""
    destino = nucleo.SUITE / "herramientas" / "rclone.exe"
    otras = [nucleo.RAIZ.parent / "rclone" / "rclone.exe",
             Path(os.environ.get("LOCALAPPDATA", "")) / "SalaSuplevet" / "datos" / "herramientas" / "rclone.exe"]
    for c in [destino, *otras]:
        if c.exists():
            return c
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request("https://downloads.rclone.org/rclone-current-windows-amd64.zip",
                                 headers={"User-Agent": "Mozilla/5.0 Salas"})
    with urllib.request.urlopen(req, timeout=300) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    destino.write_bytes(z.read(next(n for n in z.namelist() if n.endswith("rclone.exe"))))
    return destino


def _rc(*args, timeout=None):
    cmd = [str(rclone()), *map(str, args), "--config", str(CONF)]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                         creationflags=0x08000000 if os.name == "nt" else 0)
    nucleo.PROCESOS.add(p)
    try:
        out, err = p.communicate(timeout=timeout)
    finally:
        nucleo.PROCESOS.discard(p)
    if p.returncode != 0:
        raise RuntimeError("Drive: " + ((err or "").strip().splitlines() or ["error desconocido"])[-1])
    return out


def _info():
    try:
        return json.loads(INFO.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def carpeta_id(link):
    m = re.search(r"/folders/([\w-]{10,})", link) or re.search(r"[?&]id=([\w-]{10,})", link) or re.fullmatch(r"([\w-]{20,})", link.strip())
    if not m:
        raise ValueError("No reconozco el link. Copia el enlace de la carpeta desde Drive (Compartir → Copiar enlace).")
    return m.group(1)


def _llave_de_la_sala():
    """La conexión que ya hizo la Sala de edición en esta PC (si la hay): {conf, link, carpeta_id}."""
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "SalaSuplevet" / "datos"
    conf = base / "rclone.conf"
    try:
        cfg = json.loads((base / "config.local.json").read_text(encoding="utf-8")).get("drive", {})
        texto = conf.read_text(encoding="utf-8")
    except (FileNotFoundError, ValueError):
        return None
    if "token" not in texto or not cfg.get("carpeta_id"):
        return None
    return {"conf": texto, "link": cfg.get("link", ""), "carpeta_id": cfg["carpeta_id"]}


def estado():
    i = _info()
    conectado = CONF.exists() and f"[{REMOTO}]" in CONF.read_text(encoding="utf-8", errors="ignore")
    return {"activo": bool(i.get("activo")) and conectado, "conectado": conectado, "link": i.get("link", ""),
            "proyecto": i.get("nombre", ""), "de_la_sala": bool(_llave_de_la_sala()) and not conectado}


def usar_llave_de_la_sala():
    """Copia la llave de la Sala de edición a la suite: las tres salas quedan con la misma conexión."""
    s = _llave_de_la_sala()
    if not s:
        raise RuntimeError("La Sala de edición no está conectada a Drive en esta PC.")
    texto = re.sub(r"^\[[^\]]+\]", f"[{REMOTO}]", s["conf"].strip(), count=1, flags=re.M)
    CONF.write_text(texto + "\n", encoding="utf-8")
    _rc("lsjson", f"{REMOTO}:", "--max-depth", "1", timeout=60)
    INFO.write_text(json.dumps({"activo": True, "link": s["link"], "carpeta_id": s["carpeta_id"]}, ensure_ascii=False), encoding="utf-8")


def conectar(link):
    """Abre Google en el navegador (una sola vez) para dar acceso a la carpeta del proyecto."""
    cid = carpeta_id(link)
    if CONF.exists():
        try:
            _rc("config", "delete", REMOTO)
        except RuntimeError:
            pass
    _rc("config", "create", REMOTO, "drive", "scope=drive", f"root_folder_id={cid}", timeout=600)
    _rc("lsjson", f"{REMOTO}:", "--max-depth", "1", timeout=60)  # comprueba que la carpeta se ve
    INFO.write_text(json.dumps({"activo": True, "link": link, "carpeta_id": cid}, ensure_ascii=False), encoding="utf-8")


def desconectar():
    INFO.write_text(json.dumps({**_info(), "activo": False}, ensure_ascii=False), encoding="utf-8")


def bajar(rel, excluir=(), timeout=900):
    """Trae de Drive la carpeta rel a la copia local, sin pisar lo más nuevo de esta PC."""
    if not estado()["activo"]:
        return False
    ex = [a for e in ("desktop.ini", *excluir) for a in ("--exclude", e)]
    with _candado:
        _rc("copy", f"{REMOTO}:{rel}", CACHE / rel, "--update", *ex, timeout=timeout)
    return True


def subir(rel):
    """Sube a Drive la carpeta (o archivo) rel de la copia local. No borra nada en Drive."""
    if not estado()["activo"]:
        return False
    local = CACHE / rel
    if not local.exists():
        return False
    with _candado:
        if local.is_dir():
            _rc("copy", local, f"{REMOTO}:{rel}", "--update", "--exclude", "desktop.ini", timeout=900)
        else:
            _rc("copyto", local, f"{REMOTO}:{rel}", timeout=300)
    return True


def en_segundo_plano(fn, *args):
    def tarea():
        try:
            fn(*args)
        except Exception as e:  # sin internet o sin permiso: se reintenta la próxima vez
            print("Drive:", e, flush=True)
    threading.Thread(target=tarea, daemon=True).start()
