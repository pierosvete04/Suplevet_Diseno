"""Los videos que terminó la Sala de edición, para usarlos de referencia al crear posts y carruseles.

Se leen directo del Drive del proyecto (solo lectura: esta sala no toca las carpetas de video):
  <producción>/<día>/V.FINALES/*.mp4  (o VIDEOS FINALES), con su portada .jpg y su copy .txt si los hay.
La miniatura sale de la portada; si el video no tiene, de la que Google Drive genera para cada video.
Para que Claude entienda el video se le pasa el copy y el guion de la producción (carpeta Guion).
"""
import hashlib
import json
import re
import threading
import time
import urllib.request
from pathlib import Path

import cuenta
import nucleo

EXT_VIDEO = (".mp4", ".mov")
FINALES = ("V.FINALES", "VIDEOS FINALES", "listos")
CACHE = nucleo.DATOS / "videos"
GUARDADA = CACHE / "lista.json"  # la última lista, para mostrarla al instante al abrir la sala
FRESCA = 600  # 10 minutos: después se vuelve a pedir a Drive, por detrás
_lista = {"t": 0, "datos": [], "prods": [], "pidiendo": False}
_candado = threading.Lock()


def _cargar_guardada():
    if _lista["datos"] or not GUARDADA.is_file():
        return
    try:
        g = json.loads(GUARDADA.read_text(encoding="utf-8"))
        _lista.update(t=g.get("t", 0), datos=g.get("videos", []), prods=g.get("producciones", []))
    except (OSError, ValueError):
        pass


def listar(forzar=False):
    """[{ruta, id, nombre, produccion, sesion, fecha, mb, portada, copy}] del más nuevo al más viejo.
    Antes tardaba unos 15 s cada vez que se abría la sala: recorría el Drive carpeta por carpeta. Ahora la lista se pide
    de una vez (--fast-list, la mitad del tiempo) y queda guardada en el disco: se muestra al instante y, si tiene más
    de 10 minutos, se vuelve a pedir por detrás. «Actualizar lista» (forzar) espera la lista nueva."""
    _cargar_guardada()
    vieja = time.time() - _lista["t"] > FRESCA
    if forzar or not _lista["datos"]:
        return _pedir()
    if vieja and not _lista["pidiendo"]:
        _lista["pidiendo"] = True  # ya cuenta como pedida: otra llamada mientras tanto no lanza otra
        threading.Thread(target=_pedir_por_detras, daemon=True).start()
    return _lista["datos"]


def precalentar():
    """Al abrir la sala: si la lista guardada falta o es vieja, se pide por detrás (para cuando se entre a Videos)."""
    _cargar_guardada()
    if time.time() - _lista["t"] > FRESCA and not _lista["pidiendo"]:
        _lista["pidiendo"] = True
        threading.Thread(target=_pedir_por_detras, daemon=True).start()


def actualizando():
    """True mientras se está pidiendo la lista nueva a Drive (la página lo dice)."""
    return _lista["pidiendo"]


def _pedir_por_detras():
    try:
        _pedir()
    except Exception:  # noqa: BLE001 — sin Drive o sin internet: queda la lista guardada, se intenta de nuevo en la próxima
        _lista["pidiendo"] = False


def _pedir():
    with _candado:  # una sola lista a la vez: si ya la pidió otro, se usa esa
        if _lista["datos"] and time.time() - _lista["t"] < 5:
            return _lista["datos"]
        _lista["pidiendo"] = True
        try:
            datos = _listar_drive()
            prods = _producciones_drive() if datos is not None else []
        finally:
            _lista["pidiendo"] = False
        if datos is None:
            return _lista["datos"]
        _lista.update(t=time.time(), datos=datos, prods=prods)
        try:
            CACHE.mkdir(parents=True, exist_ok=True)
            GUARDADA.write_text(json.dumps({"t": _lista["t"], "videos": datos, "producciones": prods}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        return datos


def _listar_drive():
    if not cuenta.estado()["conectado"]:
        return None
    filtros = []
    for f in FINALES:
        filtros += ["--include", f"**/{f}/**"]   # también los que la Sala exporta por día (V.FINALES/DIA_1/…)
    archivos = json.loads(cuenta.rc("lsjson", f"{cuenta.REMOTO}:", "-R", "--fast-list", "--files-only", *filtros, timeout=180) or "[]")
    por_ruta = {a["Path"]: a for a in archivos}
    out = []
    for a in archivos:
        ruta = a["Path"]
        if Path(ruta).suffix.lower() not in EXT_VIDEO or "POR_PARTES" in ruta.split("/"):
            continue
        base = ruta.rsplit(".", 1)[0]
        partes = ruta.split("/")
        i = next(k for k, p in enumerate(partes) if p in FINALES)
        out.append({"ruta": ruta, "id": a.get("ID", ""), "nombre": Path(ruta).stem.strip(), "produccion": partes[0],
                    "sesion": "/".join(partes[:i]), "fecha": a.get("ModTime", "")[:16].replace("T", " "),
                    "mb": round(a.get("Size", 0) / 1048576, 1),
                    "portada": next((base + e for e in (".jpg", ".jpeg", ".png") if base + e in por_ruta), ""),
                    "copy": base + ".txt" if base + ".txt" in por_ruta else "",
                    "ver": f"https://drive.google.com/file/d/{a.get('ID', '')}/view"})
    out.sort(key=lambda v: v["fecha"], reverse=True)
    return out


def _video(ruta):
    v = next((x for x in listar() if x["ruta"] == ruta), None)
    if not v:
        raise ValueError("Ese video no está en las carpetas de videos terminados")
    return v


def miniatura(ruta):
    """Archivo local con la miniatura del video (se baja una vez y queda guardada)."""
    v = _video(ruta)
    CACHE.mkdir(parents=True, exist_ok=True)
    destino = CACHE / (hashlib.sha1(ruta.encode()).hexdigest()[:16] + ".jpg")
    if destino.exists():
        return destino
    if v["portada"]:
        cuenta.rc("copyto", f"{cuenta.REMOTO}:{v['portada']}", destino, timeout=120)
    else:
        link = cuenta.api_drive(f"files/{v['id']}?fields=thumbnailLink").get("thumbnailLink", "")
        if not link:
            raise FileNotFoundError("Google Drive aún no tiene miniatura de este video")
        link = re.sub(r"=s\d+$", "=s640", link)
        with urllib.request.urlopen(urllib.request.Request(link, headers={"Authorization": f"Bearer {cuenta.token()}"}), timeout=30) as r:
            destino.write_bytes(r.read())
    return destino


def _leer(ruta, maximo=20000):
    try:
        return (cuenta.rc("cat", f"{cuenta.REMOTO}:{ruta}", timeout=60) or "")[:maximo]
    except RuntimeError:
        return ""


def contexto(ruta):
    """Lo que Claude necesita para entender el video: nombre, producción, copy y guion de la producción."""
    v = _video(ruta)
    guion = ""
    try:  # el guion puede estar en otro día de la misma producción (P02 …/11 10 SESIÓN/Guion)
        hay = cuenta.rc("lsf", f"{cuenta.REMOTO}:{v['produccion']}", "-R", "--max-depth", "3", "--files-only",
                        "--include", "Guion/*", "--include", "*/Guion/*", "--include", "Guiones/*", "--include", "*/Guiones/*",
                        timeout=90).splitlines()
    except RuntimeError:
        hay = []
    orden = lambda n: (0 if n.lower().endswith(("guion_produccion.md", "guiones.md")) else 1 if n.lower().endswith(".md")
                       else 2 if n.lower().endswith("produccion.json") else 9)
    elegidos = sorted((n for n in hay if orden(n) < 9), key=orden)
    if elegidos:
        guion = _leer(f"{v['produccion']}/{elegidos[0]}")
    return {"video": v["nombre"], "produccion": v["produccion"], "sesion": v["sesion"],
            "copy": _leer(v["copy"], 4000) if v["copy"] else "", "guion_de_la_produccion": guion}


def ver_en_drive(ruta):
    return f"https://drive.google.com/file/d/{_video(ruta)['id']}/view"


def producciones():
    """Todas las carpetas de producción del Drive (P01 …, «DD MM SESIÓN»), tengan o no videos terminados.
    Se piden junto con la lista de videos y se guardan con ella."""
    _cargar_guardada()
    return _lista["prods"]


def _producciones_drive():
    nombres = [n.rstrip("/") for n in cuenta.rc("lsf", f"{cuenta.REMOTO}:", "--dirs-only", timeout=60).splitlines()]
    return sorted(n for n in nombres if re.match(r"^P\d+", n, re.I) or "SESI" in n.upper())
