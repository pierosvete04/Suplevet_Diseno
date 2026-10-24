"""Google Drive como base de datos de la Sala de diseño, con rclone (sin Google Drive para escritorio y sin APIs de pago).

La sesión (entrar con Google, la llave, el proyecto) es la de cuenta.py, común a las tres salas.
Esta sala trabaja sobre su copia local (datos/drive) y sincroniza con Drive:
  - sube solo lo suyo (cada carpeta de Drive tiene un solo programa que escribe),
  - baja con --update: nunca pisa algo más nuevo de esta PC.
"""
import threading
import time

import cuenta
import nucleo

REMOTO = cuenta.REMOTO
CACHE = nucleo.DATOS / "drive"
_candado = threading.Lock()


def estado():
    e = cuenta.estado()
    return {**e, "activo": e["conectado"]}


def bajar(rel, excluir=(), timeout=900):
    """Trae de Drive la carpeta rel a la copia local, sin pisar lo más nuevo de esta PC."""
    if not estado()["activo"]:
        return False
    ex = [a for e in ("desktop.ini", *excluir) for a in ("--exclude", e)]
    with _candado:
        cuenta.rc("copy", f"{REMOTO}:{rel}", CACHE / rel, "--update", *ex, timeout=timeout)
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
            cuenta.rc("copy", local, f"{REMOTO}:{rel}", "--update", "--exclude", "desktop.ini", timeout=900)
        else:
            cuenta.rc("copyto", local, f"{REMOTO}:{rel}", timeout=300)
    return True


def tras_elegir_carpeta(r):
    """Después de elegir (o crear) la carpeta del proyecto en la pantalla de la cuenta (cuenta.primera).
    Si es otra carpeta que la de antes, la copia local vieja se aparta: si no, se subiría a la carpeta nueva."""
    cid = cuenta.estado()["carpeta_id"]
    antes = nucleo.CONFIG.get("carpeta_id")
    if antes and antes != cid and CACHE.exists():
        with _candado:
            CACHE.rename(nucleo.DATOS / f"drive_anterior_{antes}_{int(time.time())}")
    nucleo.guardar_config({"carpeta_id": cid})
    import marca
    import piezas
    if r.get("nueva"):
        marca.crear_base(r.get("marca", ""))
    piezas.sincronizar(forzar=True)


def en_segundo_plano(fn, *args):
    def tarea():
        try:
            fn(*args)
        except Exception as e:  # sin internet o sin permiso: se reintenta la próxima vez
            print("Drive:", e, flush=True)
    threading.Thread(target=tarea, daemon=True).start()
