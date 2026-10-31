"""Google Drive como base de datos de la Sala de diseño, con rclone (sin Google Drive para escritorio y sin APIs de pago).

La sesión (entrar con Google, la llave, el proyecto) es la de cuenta.py, común a las tres salas.
Esta sala trabaja sobre su copia local (datos/drive) y sincroniza con Drive:
  - sube solo lo suyo (cada carpeta de Drive tiene un solo programa que escribe),
  - baja con --update: nunca pisa algo más nuevo de esta PC.
La copia local es de una sola carpeta de Drive (dice cuál en .sala/carpeta.txt): ver revisar_copia_local.
"""
import threading
import time

import cuenta
import nucleo

REMOTO = cuenta.REMOTO
CACHE = nucleo.DATOS / "drive"
VIDEOS = nucleo.DATOS / "videos"  # las listas guardadas de videos y guiones (videos.py, guiones.py): también son de la carpeta
DE_QUE_CARPETA = ".sala/carpeta.txt"  # dentro de la copia local: de qué carpeta de Drive es (viaja con ella al apartarla)
_candado = threading.Lock()


def estado():
    e = cuenta.estado()
    return {**e, "activo": e["conectado"]}


def _carpeta_de_la_copia():
    try:
        return (CACHE / DE_QUE_CARPETA).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _anotar_carpeta_de_la_copia(cid):
    try:
        (CACHE / ".sala").mkdir(parents=True, exist_ok=True)
        (CACHE / DE_QUE_CARPETA).write_text(cid, encoding="utf-8")
    except OSError:
        pass


def revisar_copia_local():
    """La llave y la copia local (datos/drive) tienen que ser de la carpeta que eligió la cuenta. Si la copia es de
    otra (otra cuenta, otro proyecto), se aparta en datos/drive_<id> y vuelve la de la carpeta nueva si ya se había
    usado: la marca y las piezas de la otra no se ven ni se suben a la nueva (pasó el 30/10 con la Sala de edición: con
    la cuenta de Mr Peanut se veían las sesiones de Suplevet). Se mira antes de cada bajada y subida, y es barato:
    solo lee drive.json, la llave y la marca. Devuelve True si cambió la copia."""
    c = cuenta.estado()
    if not c["conectado"] or not c["carpeta_id"]:
        return False
    ahora = c["carpeta_id"]
    # una copia sin anotar (de antes de la 0.21) es de la carpeta con la que trabajaba rclone, o si no de la que se
    # eligió aquí la última vez; no de la que está elegida ahora
    apuntaba = cuenta.reparar_llave() or cuenta._leer(cuenta.INFO).get("llave_apuntaba")
    with _candado:
        hay_copia = CACHE.exists() or VIDEOS.exists()
        de_la_copia = _carpeta_de_la_copia() or ((apuntaba or nucleo.CONFIG.get("carpeta_id")) if hay_copia else "") or ahora
        if de_la_copia != ahora:
            _cambiar_copia_local(de_la_copia, ahora)
        _anotar_carpeta_de_la_copia(ahora)
    if nucleo.CONFIG.get("carpeta_id") != ahora:
        nucleo.guardar_config({"carpeta_id": ahora})
    if de_la_copia == ahora:
        return False
    import guiones
    import videos
    videos.olvidar()
    guiones.olvidar()
    print(f"Drive: la copia local era de otra carpeta ({de_la_copia}): quedó aparte en drive_{de_la_copia}", flush=True)
    return True


def _cambiar_copia_local(antes, ahora):
    """La copia de antes (con sus listas de videos y guiones, en .sala/videos) se aparta en datos/drive_<antes> y
    vuelve la de datos/drive_<ahora> si existe."""
    try:
        aparte = nucleo.DATOS / f"drive_{antes}"
        if CACHE.exists() or VIDEOS.exists():
            if aparte.exists():  # una copia vieja de esa carpeta que quedó de antes: se guarda con otro nombre
                aparte.rename(nucleo.DATOS / f"drive_{antes}_{int(time.time())}")
            if CACHE.exists():
                CACHE.rename(aparte)
            if VIDEOS.exists():
                (aparte / ".sala").mkdir(parents=True, exist_ok=True)
                VIDEOS.rename(aparte / ".sala" / "videos")
        vuelve = nucleo.DATOS / f"drive_{ahora}"
        if vuelve.exists() and not CACHE.exists():
            vuelve.rename(CACHE)
            if (CACHE / ".sala" / "videos").exists() and not VIDEOS.exists():
                (CACHE / ".sala" / "videos").rename(VIDEOS)
    except OSError as e:  # un archivo abierto (una lámina que se está exportando): se reintenta en la próxima bajada
        raise RuntimeError("No pude apartar los archivos de la carpeta anterior: hay alguno abierto. Cierra la sala "
                           "y vuelve a abrirla.") from e


def bajar(rel, excluir=(), timeout=900):
    """Trae de Drive la carpeta rel a la copia local, sin pisar lo más nuevo de esta PC."""
    if not estado()["activo"]:
        return False
    revisar_copia_local()
    ex = [a for e in ("desktop.ini", *excluir) for a in ("--exclude", e)]
    with _candado:
        cuenta.rc("copy", f"{REMOTO}:{rel}", CACHE / rel, "--update", *ex, timeout=timeout)
    return True


def subir(rel):
    """Sube a Drive la carpeta (o archivo) rel de la copia local. No borra nada en Drive."""
    if not estado()["activo"]:
        return False
    if revisar_copia_local():  # lo que se iba a subir era de la carpeta de antes: quedó aparte, no se sube
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
    revisar_copia_local()
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
