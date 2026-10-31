"""Los guiones de la Sala de edición, para crear piezas a partir de sus cuerpos («Crear con IA → Cuerpos de los guiones»).

Se leen directo del Drive del proyecto (solo lectura: esta sala no toca las carpetas de video):
  <producción>/Guion/produccion.json  o  <producción>/<día>/Guion/produccion.json
De cada guion se toman sus cuerpos (C1, C2…), los hooks de cada cuerpo (C1_H1…) y sus CTA.
La lista queda guardada en esta PC, como la de videos: sale al instante y, si es vieja, se renueva por detrás.
"""
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cuenta
import nucleo

GUARDADA = nucleo.DATOS / "videos" / "guiones.json"
FRESCA = 600
_lista = {"t": 0, "datos": [], "pidiendo": False}
_candado = threading.Lock()


def _texto(t):
    """El texto de una pieza del guion: viene como texto o como lista de partes."""
    if isinstance(t, list):
        t = " ".join(x if isinstance(x, str) else str(x.get("texto") or "") for x in t)
    return re.sub(r"\s+", " ", str(t or "")).strip()


def resumir(ruta, guion):
    """{produccion, ruta, publico, cuerpos: [{id, texto, hooks: [...], ctas: [...]}]} de un produccion.json."""
    piezas = guion.get("piezas") or {}
    if isinstance(piezas, list):  # algunos guiones viejos traen la lista en vez del diccionario
        piezas = {str(p.get("id") or i): p for i, p in enumerate(piezas) if isinstance(p, dict)}
    def es_cta(k, p):
        return "CTA" in k.upper() or str(p.get("tipo", "")).lower() in ("cta", "anuncio")
    ctas_generales = [_texto(p.get("texto") or p.get("dicho")) for k, p in piezas.items()
                      if isinstance(p, dict) and es_cta(k, p) and not re.match(r"^C\d+_", k)]
    cuerpos = []
    for k, p in piezas.items():
        if not isinstance(p, dict) or str(p.get("tipo", "")).lower() != "cuerpo":
            continue
        hooks = [_texto(h.get("texto") or h.get("dicho")) for kk, h in piezas.items()
                 if isinstance(h, dict) and re.match(rf"^{re.escape(k)}_H\d+$", kk)]
        ctas = [_texto(h.get("texto") or h.get("dicho")) for kk, h in piezas.items()
                if isinstance(h, dict) and kk.startswith(k + "_") and es_cta(kk, h)]
        cuerpos.append({"id": k, "texto": _texto(p.get("texto") or p.get("dicho")), "hooks": [h for h in hooks if h],
                        "ctas": [c for c in (ctas or ctas_generales) if c][:3]})
    cuerpos.sort(key=lambda c: int(re.sub(r"\D", "", c["id"]) or 0))
    partes = ruta.split("/")
    return {"produccion": partes[0], "sesion": "/".join(partes[:-2]), "ruta": ruta,
            "publico": str(guion.get("publico") or ""), "cuerpos": cuerpos}


def olvidar():
    """La copia local cambió de carpeta (otra cuenta): la lista de la otra no se muestra más (conexion.revisar_copia_local)."""
    _lista.update(t=0, datos=[])


def listar(forzar=False):
    """Las producciones con guion y sus cuerpos. Como la lista de videos: guardada en la PC y renovada por detrás."""
    if not _lista["datos"] and GUARDADA.is_file():
        try:
            g = json.loads(GUARDADA.read_text(encoding="utf-8"))
            _lista.update(t=g.get("t", 0), datos=g.get("guiones", []))
        except (OSError, ValueError):
            pass
    if forzar or not _lista["datos"]:
        return _pedir()
    if time.time() - _lista["t"] > FRESCA and not _lista["pidiendo"]:
        _lista["pidiendo"] = True
        threading.Thread(target=_pedir_por_detras, daemon=True).start()
    return _lista["datos"]


def precalentar():
    """Al abrir la sala: si falta la lista o es vieja, se pide por detrás (para que «Cuerpos de los guiones» abra al instante)."""
    if not _lista["datos"] and GUARDADA.is_file():
        listar()  # carga la guardada (y si es vieja, la renueva por detrás)
        return
    if time.time() - _lista["t"] > FRESCA and not _lista["pidiendo"]:
        _lista["pidiendo"] = True
        threading.Thread(target=_pedir_por_detras, daemon=True).start()


def actualizando():
    return _lista["pidiendo"]


def _pedir_por_detras():
    try:
        _pedir()
    except Exception:  # noqa: BLE001 — sin Drive: queda la lista guardada
        _lista["pidiendo"] = False


def _pedir():
    with _candado:
        if _lista["datos"] and time.time() - _lista["t"] < 5:
            return _lista["datos"]
        _lista["pidiendo"] = True
        try:
            if not cuenta.estado()["conectado"]:
                return _lista["datos"]
            rutas = [r for r in cuenta.rc("lsf", f"{cuenta.REMOTO}:", "-R", "--fast-list", "--files-only", "--max-depth", "4",
                                          "--include", "**/Guion/produccion.json", timeout=180).splitlines()
                     if r.strip() and not r.startswith(("_", "DISEÑO/"))]
            def leer(r):
                try:
                    return resumir(r, json.loads(cuenta.rc("cat", f"{cuenta.REMOTO}:{r}", timeout=60) or "{}"))
                except (RuntimeError, ValueError):
                    return None
            with ThreadPoolExecutor(max_workers=6) as hilos:  # todos a la vez: uno tras otro tardaba más de 20 s
                leidos = [g for g in hilos.map(leer, rutas) if g and g["cuerpos"]]
            # una copia suelta del mismo guion (por ejemplo «11／10 SESIÓN» en la raíz y dentro de P02) sale una sola vez:
            # queda la que está dentro de su producción (P0X …)
            datos, vistos = [], set()
            for g in sorted(leidos, key=lambda x: (not x["produccion"][:1].upper() == "P", x["ruta"])):
                firma = tuple(c["texto"] for c in g["cuerpos"])
                if firma not in vistos:
                    vistos.add(firma)
                    datos.append(g)
            datos.sort(key=lambda x: x["ruta"])
        finally:
            _lista["pidiendo"] = False
        _lista.update(t=time.time(), datos=datos)
        try:
            GUARDADA.parent.mkdir(parents=True, exist_ok=True)
            GUARDADA.write_text(json.dumps({"t": _lista["t"], "guiones": datos}, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        return datos


def elegidos(pedidos):
    """[{ruta, id}] que mandó la página -> los cuerpos completos (con su producción, público, hooks y CTA), en ese orden."""
    por_ruta = {g["ruta"]: g for g in listar()}
    out = []
    for p in pedidos or []:
        g = por_ruta.get(str(p.get("ruta", "")))
        c = next((c for c in (g or {}).get("cuerpos", []) if c["id"] == p.get("id")), None)
        if c:
            out.append({"produccion": g["produccion"], "ruta": g["ruta"], "publico": g["publico"], **c})
    return out
