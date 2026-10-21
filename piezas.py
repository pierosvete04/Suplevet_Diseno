"""Las piezas de diseño (carruseles y posts), ordenadas por mes y semana de lunes a domingo, en el Drive del proyecto.

  DISEÑO/2026-10 OCTUBRE/S03 · 19-25 OCT · PICAZÓN/
    semana.json                              plan de la semana (sale del brief de _SEMANAS)
    LUN · C01 · Se rasca y no tiene pulgas/  un carrusel (C) o un post (P)
      pieza.json                             láminas y capas (lo que se edita)
      Flow/                                  fotos de Flow tal cual y sus recortes sin fondo
      FINAL/L01.png… + copy.txt              lo exportado: el Publicador lo toma de aquí
      editando.json                          quién la tiene abierta (aviso para no pisarse)

Esta sala es la única que escribe en DISEÑO/. Lee _SEMANAS/ (brief de la estrategia) y _MARCA/.
El número de semana sigue a la estrategia: la del lunes 19/10/2026 es la S03 (ver config.json → semana_base).
"""
import datetime as dt
import os
import json
import re
import time
from pathlib import Path

import conexion
import nucleo

CARPETA = "DISEÑO"
SEMANAS_ESTRATEGIA = "_SEMANAS"
MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]
EXT = (".png", ".jpg", ".jpeg", ".webp")
PROHIBIDOS = '\\/:*?"<>|'  # no van en nombres de carpeta de Windows
TIPOS = {"carrusel": "C", "post": "P"}
FORMATOS = {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920)}


def raiz():
    return conexion.CACHE / CARPETA


def _limpio(texto, largo=60):
    """Nombre de carpeta válido en Windows y en Drive."""
    t = "".join(c for c in texto if c not in PROHIBIDOS)
    t = re.sub(r"\s+", " ", t).strip(" .")
    if len(t) > largo:  # se corta en una palabra entera y sin signos sueltos al final
        t = t[:largo].rsplit(" ", 1)[0]
        t = t.rstrip(" .,;:-–(«¿¡")
    return t.strip(" .") or "Pieza"


def quien():
    import cuenta
    c = cuenta.estado()
    return nucleo.CONFIG.get("nombre") or c.get("nombre") or c.get("email") or os.environ.get("USERNAME") or "equipo"


# ---------- Semanas ----------
def _base():
    b = nucleo.CONFIG.get("semana_base", {})
    return int(b.get("numero", 1)), dt.date.fromisoformat(b.get("lunes", "2026-10-05"))


def lunes_de(fecha):
    return fecha - dt.timedelta(days=fecha.weekday())


def codigo_semana(lunes):
    num, lunes_base = _base()
    return f"S{num + (lunes - lunes_base).days // 7:02d}"


def nombre_semana(lunes, tema=""):
    """(«2026-10 OCTUBRE», «S03 · 19-25 OCT · PICAZÓN»)."""
    dom = lunes + dt.timedelta(days=6)
    if lunes.month == dom.month:
        rango = f"{lunes.day}-{dom.day} {MESES[dom.month - 1][:3]}"
    else:
        rango = f"{lunes.day} {MESES[lunes.month - 1][:3]}-{dom.day} {MESES[dom.month - 1][:3]}"
    mes = f"{lunes.year}-{lunes.month:02d} {MESES[lunes.month - 1]}"
    return mes, f"{codigo_semana(lunes)} · {rango}" + (f" · {_limpio(tema, 30).upper()}" if tema.strip() else "")


def semanas():
    """[{rel, mes, semana, piezas}] de la más nueva a la más vieja."""
    out = []
    if raiz().is_dir():
        for mes in sorted((m for m in raiz().iterdir() if m.is_dir()), key=lambda m: m.name, reverse=True):
            for sem in sorted((x for x in mes.iterdir() if x.is_dir()), key=lambda x: x.name, reverse=True):
                n = sum(1 for c in sem.iterdir() if (c / "pieza.json").is_file())
                out.append({"rel": f"{mes.name}/{sem.name}", "mes": mes.name, "semana": sem.name, "piezas": n})
    return out


def _misma(a, b):
    return a.split(" · ")[:2] == b.split(" · ")[:2]  # «S03 · 19-25 OCT», con o sin tema


def semana_actual():
    rel = nucleo.CONFIG.get("semana")
    if rel and (raiz() / rel).is_dir():
        return rel
    return crear_semana(dt.date.today().isoformat())


def elegir_semana(rel):
    if not (raiz() / _rel_seguro(rel)).is_dir():
        raise ValueError("Esa semana no existe")
    nucleo.guardar_config({"semana": rel})


def brief_de(codigo):
    """El brief que dejó la estrategia en _SEMANAS/<S03 …>/brief.json (si lo hay)."""
    d = conexion.CACHE / SEMANAS_ESTRATEGIA
    for sem in sorted(d.iterdir()) if d.is_dir() else []:
        if sem.is_dir() and sem.name.split(" ")[0].split("_")[0].upper() == codigo and (sem / "brief.json").is_file():
            try:
                return json.loads((sem / "brief.json").read_text(encoding="utf-8"))
            except ValueError:
                return None
    return None


def crear_semana(fecha_iso, tema="", plan=None, elegir=True):
    """Crea (o reusa) la semana de esa fecha. Con plan (o con brief en _SEMANAS) crea una pieza por día que falte."""
    lunes = lunes_de(dt.date.fromisoformat(fecha_iso))
    if plan is None:
        brief = brief_de(codigo_semana(lunes))
        if brief:
            plan = brief.get("carruseles") or []
            tema = tema or brief.get("tema", "")
    mes, nombre = nombre_semana(lunes, tema)
    previa = next((s for s in semanas() if s["mes"] == mes and _misma(s["semana"], nombre)), None)
    rel = previa["rel"] if previa else f"{mes}/{nombre}"
    d = raiz() / rel
    d.mkdir(parents=True, exist_ok=True)
    if plan:
        (d / "semana.json").write_text(json.dumps({"lunes": lunes.isoformat(), "tema": tema, "plan": plan},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
        hechos = {p["dia"] for p in listar(rel)}
        for c in plan:
            dia = _dia(c.get("dia"))
            if dia and dia not in hechos:
                nueva(c.get("tema") or "Carrusel", tipo=c.get("tipo", "carrusel"), dia=dia, rel=rel, nivel=c.get("nivel", ""),
                      publico=c.get("publico", ""), estilo=c.get("estilo", ""))
    if elegir:
        nucleo.guardar_config({"semana": rel})
    return rel


def _dia(texto):
    t = (texto or "").strip()[:3].upper().replace("É", "E").replace("Á", "A")
    return t if t in DIAS else ""


def _rel_seguro(rel):
    partes = Path(rel).parts
    if len(partes) != 2 or any(p in ("", ".", "..") or p.startswith(".") for p in partes):
        raise ValueError("Semana no válida")
    return rel


def semana_dir(rel=None):
    return raiz() / _rel_seguro(rel or semana_actual())


def _id_seguro(pid):
    if not pid or pid in (".", "..") or any(c in pid for c in PROHIBIDOS):
        raise ValueError("Pieza no válida")
    return pid


def carpeta(pid, rel=None):
    return semana_dir(rel) / _id_seguro(pid)


def rel_drive(pid=None):
    """Ruta dentro de Drive de la semana actual (o de una pieza), para subirla."""
    rel = f"{CARPETA}/{semana_actual()}"
    return f"{rel}/{pid}" if pid else rel


# ---------- Piezas ----------
def listar(rel=None):
    out, d = [], semana_dir(rel)
    for c in sorted(x for x in d.iterdir() if x.is_dir()) if d.is_dir() else []:
        try:
            p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError):
            continue
        out.append({"id": c.name, "titulo": p.get("titulo", c.name), "tipo": p.get("tipo", "carrusel"), "dia": p.get("dia", ""),
                    "laminas": len(p.get("laminas", [])), "formato": p.get("formato", "4:5"), "estilo": p.get("estilo", ""), "nivel": p.get("nivel", ""),
                    "publico": p.get("publico", ""), "exportado": any((c / "FINAL").glob("L*.png")),
                    "editando": _editando(c)})
    orden = {d: i for i, d in enumerate(DIAS)}
    return sorted(out, key=lambda x: (orden.get(x["dia"], 9), x["id"]))


def _editando(c):
    """Quién más la tiene abierta (en los últimos 10 minutos); None si nadie o si soy yo."""
    try:
        e = json.loads((c / "editando.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None
    return e if e.get("quien") != quien() and time.time() - e.get("t", 0) < 600 else None


def leer(pid):
    c = carpeta(pid)
    p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
    return p, _editando(c)


def marcar_editando(pid):
    c = carpeta(pid)
    (c / "editando.json").write_text(json.dumps({"quien": quien(), "t": time.time(), "hora": time.strftime("%H:%M")}), encoding="utf-8")


def guardar(pid, datos):
    c = carpeta(pid)
    c.mkdir(parents=True, exist_ok=True)
    datos["actualizado"] = time.strftime("%Y-%m-%d %H:%M")
    datos["por"] = quien()
    tmp = c / "pieza.json.tmp"
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(c / "pieza.json")
    return datos


def nueva(titulo, tipo="carrusel", laminas=None, dia="", rel=None, nivel="", publico="", estilo="", formato="4:5"):
    """Carpeta «LUN · C01 · Tema» (carrusel) o «LUN · P02 · Tema» (post). El número sigue dentro de la semana."""
    rel = rel or semana_actual()
    tipo = tipo if tipo in TIPOS else "carrusel"
    nums = [int(m.group(1)) for m in (re.search(r"\b[CP](\d+)\b", x["id"]) for x in listar(rel)) if m]
    num = (max(nums) + 1) if nums else 1
    dia = _dia(dia)
    pid = " · ".join(([dia] if dia else []) + [f"{TIPOS[tipo]}{num:02d}", _limpio(titulo.replace("*", ""), 50)])
    n = laminas or (4 if tipo == "carrusel" else 1)
    vacia = lambda: {"fondo": {"tipo": "color", "color": ""}, "capas": []}
    datos = {"titulo": titulo, "tipo": tipo, "formato": formato if formato in FORMATOS else "4:5", "dia": dia, "nivel": nivel,
             "publico": publico, "estilo": estilo, "copy": "", "laminas": [vacia() for _ in range(n)]}
    c = semana_dir(rel) / pid
    (c / "Flow").mkdir(parents=True, exist_ok=True)
    (c / "pieza.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return pid, datos


def crear_desde_pedido(texto, resultado, rel=None):
    """Crea las piezas que propuso Claude (con sus textos y prompts de Flow) y anota el pedido en pedidos.json."""
    rel = rel or semana_actual()
    hechas = []
    for p in resultado.get("piezas", []):
        laminas = p.get("laminas") or []
        tipo = "post" if p.get("tipo") == "post" or len(laminas) == 1 else "carrusel"
        pid, datos = nueva(p.get("titulo") or "Pieza", tipo=tipo, laminas=max(1, len(laminas)), dia=p.get("dia", ""), rel=rel,
                           nivel=p.get("nivel", ""), publico=p.get("publico", ""), estilo=p.get("estilo", ""), formato=p.get("formato", "4:5"))
        datos["guion"] = {"laminas": laminas, "copy": p.get("copy", "")}
        datos["copy"] = p.get("copy", "")
        datos["pedido"] = texto.strip()[:500]
        (semana_dir(rel) / pid / "pieza.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        hechas.append(pid)
    registro = semana_dir(rel) / "pedidos.json"
    try:
        lista = json.loads(registro.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        lista = []
    lista.append({"fecha": time.strftime("%Y-%m-%d %H:%M"), "quien": quien(), "pedido": texto.strip(), "piezas": hechas})
    registro.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    return hechas


def videos_de_la_semana(rel=None):
    """Los ángulos de los videos que trae el brief de la semana (para piezas que acompañen a los videos)."""
    codigo = Path(rel or semana_actual()).name.split(" ")[0]
    brief = brief_de(codigo) or {}
    return [{k: c.get(k) for k in ("id", "nivel", "publico", "angulo")} for c in brief.get("cuerpos", [])]


def ruta_imagen(pid):
    return carpeta(pid) / "Flow"


def guardar_imagen(pid, nombre, datos):
    d = ruta_imagen(pid)
    d.mkdir(parents=True, exist_ok=True)
    tallo, ext = Path(nombre).stem, (Path(nombre).suffix.lower() or ".png")
    if ext not in EXT:
        raise ValueError("Solo fotos PNG, JPG o WEBP")
    tallo = re.sub(r"[^\w\-]+", "_", tallo)[:50] or "foto"
    destino, n = d / f"{tallo}{ext}", 2
    while destino.exists():
        destino, n = d / f"{tallo}_{n}{ext}", n + 1
    destino.write_bytes(datos)
    return destino.name


def imagenes(pid):
    d = ruta_imagen(pid)
    if not d.is_dir():
        return []
    return sorted((f.name for f in d.iterdir() if f.suffix.lower() in EXT), key=lambda n: (d / n).stat().st_mtime)


def exportar(pid, pngs, copy=""):
    """pngs: bytes de cada lámina, en orden. Reemplaza lo exportado antes. Deja todo en <pieza>/FINAL."""
    destino = carpeta(pid) / "FINAL"
    destino.mkdir(parents=True, exist_ok=True)
    for viejo in destino.glob("L*.png"):
        viejo.unlink()
    for i, b in enumerate(pngs, 1):
        if not b.startswith(b"\x89PNG"):
            raise ValueError(f"La lámina {i} no llegó bien")
        (destino / f"L{i:02d}.png").write_bytes(b)
    if copy.strip():
        (destino / "copy.txt").write_text(f"INSTAGRAM\n{copy.strip()}\n\nTIKTOK\n{copy.strip()}\n", encoding="utf-8")
    return str(destino)


# ---------- Drive ----------
_ultima = {"t": 0}


def sincronizar(forzar=False):
    """Trae de Drive lo que hicieron otras PCs (marca, briefs y diseño). Como mucho cada 2 minutos."""
    if not forzar and time.time() - _ultima["t"] < 120:
        return
    _ultima["t"] = time.time()
    import marca

    def tarea():
        marca.bajar()
        conexion.bajar(SEMANAS_ESTRATEGIA)
        conexion.bajar(CARPETA)
        # si llegó el brief de esta semana, se crean las piezas que falten (sin cambiar la semana que se está viendo)
        crear_semana(dt.date.today().isoformat(), elegir=False)
    conexion.en_segundo_plano(tarea)


def subir(pid=None):
    conexion.en_segundo_plano(conexion.subir, rel_drive(pid))


# ---------- Biblioteca: todas las piezas de todas las semanas ----------
def _lunes_de_semana(nombre):
    """«S03 · 19-25 OCT» -> fecha del lunes, con la misma cuenta de semanas de la estrategia."""
    m = re.match(r"S(\d+)", nombre)
    if not m:
        return None
    num, lunes_base = _base()
    return lunes_base + dt.timedelta(days=7 * (int(m.group(1)) - num))


def biblioteca():
    """Cada pieza con su semana, su fecha (el día que sale) y su miniatura, de la más nueva a la más vieja."""
    out = []
    for s in semanas():
        d = raiz() / s["rel"]
        lunes = _lunes_de_semana(s["semana"])
        for c in sorted(x for x in d.iterdir() if x.is_dir()):
            try:
                p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
            except (FileNotFoundError, ValueError):
                continue
            dia = p.get("dia", "")
            fecha = (lunes + dt.timedelta(days=DIAS.index(dia))).isoformat() if lunes and dia in DIAS else (lunes.isoformat() if lunes else "")
            finales = sorted((c / "FINAL").glob("L*.png")) if (c / "FINAL").is_dir() else []
            mini = "miniatura.png" if (c / "miniatura.png").exists() else (f"FINAL/{finales[0].name}" if finales else "")
            out.append({"rel": s["rel"], "mes": s["mes"], "semana": s["semana"], "id": c.name, "titulo": p.get("titulo", c.name),
                        "tipo": p.get("tipo", "carrusel"), "formato": p.get("formato", "4:5"), "dia": dia, "fecha": fecha,
                        "nivel": p.get("nivel", ""), "publico": p.get("publico", ""), "estilo": p.get("estilo", ""),
                        "laminas": len(p.get("laminas", [])), "exportado": bool(finales), "miniatura": mini,
                        "actualizado": p.get("actualizado", ""), "por": p.get("por", ""), "pedido": p.get("pedido", ""),
                        "con_fotos": any(c2.get("tipo") == "imagen" for l in p.get("laminas", []) for c2 in l.get("capas", []))
                        or any(l.get("fondo", {}).get("tipo") == "imagen" for l in p.get("laminas", []))})
    return sorted(out, key=lambda x: (x["fecha"], x["id"]), reverse=True)


def pedidos_todos():
    out = []
    for s in semanas():
        try:
            for p in json.loads((raiz() / s["rel"] / "pedidos.json").read_text(encoding="utf-8")):
                out.append({**p, "semana": s["semana"], "rel": s["rel"]})
        except (FileNotFoundError, ValueError):
            pass
    return sorted(out, key=lambda x: x.get("fecha", ""), reverse=True)


def archivo(rel, pid, nombre):
    """La miniatura o una lámina exportada de cualquier semana (para la biblioteca)."""
    if not re.fullmatch(r"miniatura\.png|FINAL/L\d+\.png", nombre or ""):
        raise ValueError("Archivo no válido")
    return carpeta(pid, rel) / nombre


def guardar_miniatura(pid, png, rel=None):
    if not png.startswith(b"\x89PNG"):
        raise ValueError("La miniatura no llegó bien")
    (carpeta(pid, rel) / "miniatura.png").write_bytes(png)
