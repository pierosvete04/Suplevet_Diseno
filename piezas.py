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


def semana_de(fecha_iso, tema=""):
    """Para «+ Nueva semana»: cómo se va a llamar la semana de esa fecha y si ya existe."""
    try:
        lunes = lunes_de(dt.date.fromisoformat(fecha_iso))
    except ValueError:
        raise ValueError("Esa fecha no es válida") from None
    mes, nombre = nombre_semana(lunes, tema)
    previa = next((s for s in semanas() if s["mes"] == mes and _misma(s["semana"], nombre)), None)
    brief = brief_de(codigo_semana(lunes))
    return {"nombre": nombre, "mes": mes, "lunes": lunes.isoformat(), "existe": previa["rel"] if previa else None,
            "brief": bool(brief), "tema_brief": (brief or {}).get("tema", ""), "piezas_brief": len((brief or {}).get("carruseles") or [])}


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
                      publico=c.get("publico", ""), estilo=c.get("estilo", ""), origen="brief")
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
                    "con_textos": _con_textos(p), "laminas_con_foto": sum(1 for l in p.get("laminas", []) if _con_foto(l, c)),
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


def _con_semana(datos, c):
    """Anota en pieza.json la semana de la estrategia (S03) y un código fijo (S03-D-C01): con eso el Publicador
    la pone en la semana correcta y la junta con su brief."""
    semana = c.parent.name.split(" · ")[0]
    num = next((x for x in c.name.split(" · ") if re.fullmatch(r"[CP]\d+", x)), c.name)
    if re.fullmatch(r"S\d+", semana):
        datos["semana"], datos["codigo"] = semana, f"{semana}-D-{num}"
    return datos


def guardar(pid, datos):
    c = carpeta(pid)
    _con_semana(datos, c)
    try:  # con qué video va el post: la pantalla no lo manda de vuelta, que no se pierda al guardar
        antes = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
        if antes.get("video") and not datos.get("video"):
            datos["video"] = antes["video"]
    except (FileNotFoundError, ValueError):
        pass
    c.mkdir(parents=True, exist_ok=True)
    datos["actualizado"] = time.strftime("%Y-%m-%d %H:%M")
    datos["por"] = quien()
    tmp = c / "pieza.json.tmp"
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(c / "pieza.json")
    return datos


def nueva(titulo, tipo="carrusel", laminas=None, dia="", rel=None, nivel="", publico="", estilo="", formato="4:5", origen="mano"):
    """Carpeta «LUN · C01 · Tema» (carrusel) o «LUN · P02 · Tema» (post). El número sigue dentro de la semana.
    origen: de dónde salió (brief, pedido, video o mano), para decirlo en la biblioteca."""
    rel = rel or semana_actual()
    tipo = tipo if tipo in TIPOS else "carrusel"
    nums = [int(m.group(1)) for m in (re.search(r"\b[CP](\d+)\b", x["id"]) for x in listar(rel)) if m]
    num = (max(nums) + 1) if nums else 1
    dia = _dia(dia)
    pid = " · ".join(([dia] if dia else []) + [f"{TIPOS[tipo]}{num:02d}", _limpio(titulo.replace("*", ""), 50)])
    n = laminas or (4 if tipo == "carrusel" else 1)
    vacia = lambda: {"fondo": {"tipo": "color", "color": ""}, "capas": []}
    datos = {"titulo": titulo, "tipo": tipo, "formato": formato if formato in FORMATOS else "4:5", "dia": dia, "nivel": nivel,
             "publico": publico, "estilo": estilo, "origen": origen, "copy": "", "laminas": [vacia() for _ in range(n)]}
    c = semana_dir(rel) / pid
    (c / "Flow").mkdir(parents=True, exist_ok=True)
    _con_semana(datos, c)
    (c / "pieza.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return pid, datos


def crear_desde_pedido(texto, resultado, rel=None, video=""):
    """Crea las piezas que propuso Claude (con sus textos y prompts de Flow) y anota el pedido en pedidos.json.
    video: la ruta en Drive del video de la Sala de edición que se usó de referencia; queda en pieza.json («video»)
    para que el Publicador sepa con qué video va el post."""
    rel = rel or semana_actual()
    hechas = []
    for p in resultado.get("piezas", []):
        laminas = p.get("laminas") or []
        tipo = "post" if p.get("tipo") == "post" or len(laminas) == 1 else "carrusel"
        pid, datos = nueva(p.get("titulo") or "Pieza", tipo=tipo, laminas=max(1, len(laminas)), dia=p.get("dia", ""), rel=rel,
                           nivel=p.get("nivel", ""), publico=p.get("publico", ""), estilo=p.get("estilo", ""), formato=p.get("formato", "4:5"),
                           origen="guion" if p.get("fuente") else "video" if video else "pedido")
        if p.get("fuente"):  # de qué guion y cuerpo de la Sala de edición salió («Cuerpos de los guiones»)
            datos["fuente"] = p["fuente"]
        datos["guion"] = {"laminas": laminas, "copy": p.get("copy", "")}
        datos["copy"] = p.get("copy", "")
        datos["pedido"] = texto.strip()[:500]
        if video:
            datos["video"] = video
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


# ---------- «✦ Generar fotos con IA»: las fotos de Flow que faltan, y ponerlas en su lámina cuando llegan ----------
def _foto_de(lam):
    """La foto que la lámina ya tiene anotada (de fondo o como capa), aunque el archivo todavía no exista."""
    f = lam.get("fondo", {})
    if f.get("tipo") == "imagen" and (f.get("src") or {}).get("tipo") == "img":
        return f["src"]
    return next((c["src"] for c in lam.get("capas", []) if c.get("tipo") == "imagen" and (c.get("src") or {}).get("tipo") == "img"), None)


def fotos_que_faltan(pid):
    """[{id, prompt, formato, lamina}] de las láminas sin foto que tienen prompt de Flow. El id es el nombre que la lámina
    ya espera (C05_N1 de «C05_N1.jpg» o de «C05_N2_sinfondo.png») o uno nuevo (C07_L3)."""
    c = carpeta(pid)
    p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
    guion = (p.get("guion") or {}).get("laminas") or []
    num = next((x for x in c.name.split(" · ") if re.fullmatch(r"[CP]\d+", x)), "P")
    out = []
    for i, lam in enumerate(p.get("laminas", [])):
        prompt = (guion[i].get("flow") or "").strip() if i < len(guion) else ""
        if not prompt or _con_foto(lam, c):
            continue
        src = _faltante(lam, c) or _foto_de(lam)
        cod = re.sub(r"_sinfondo$", "", Path(src["f"]).stem) if src else f"{num}_L{i + 1}"
        out.append({"id": re.sub(r"[^\w-]", "_", cod), "prompt": prompt, "formato": p.get("formato", "4:5"), "lamina": i})
    return out


def poner_fotos(pid, llegadas):
    """llegadas: {id: archivo ya guardado en Flow/}. Cada foto va a la lámina que la esperaba:
    - si la lámina ya tenía anotada esa foto, se corrige el nombre (la IA anotó .jpg y llegó .png, por ejemplo); si la
      esperaba sin fondo («_sinfondo.png»), se deja así: el editor la recorta solo al abrir la pieza;
    - si no tenía ninguna, va de fondo a toda la lámina, o recortada encima del color si el guion pidió fondo «color».
    Devuelve las láminas (1, 2…) que recibieron foto."""
    c = carpeta(pid)
    p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
    guion = (p.get("guion") or {}).get("laminas") or []
    pedidas = {x["id"]: x["lamina"] for x in fotos_que_faltan(pid)}
    puestas = []
    for cod, archivo in llegadas.items():
        i = pedidas.get(cod)
        if i is None:
            continue
        lam = p["laminas"][i]
        src = _faltante(lam, c) or _foto_de(lam)
        if src:
            if not src["f"].endswith("_sinfondo.png"):
                src["f"] = archivo
        elif i < len(guion) and guion[i].get("fondo") == "color":
            w, h = FORMATOS.get(p.get("formato"), FORMATOS["4:5"])  # debajo de los textos, como «ponerEnLamina» del editor
            lam.setdefault("capas", []).insert(0, {"id": f"f{int(time.time() * 1000) % 10**9}{i}", "tipo": "imagen",
                                                   "src": {"tipo": "img", "f": f"{Path(archivo).stem}_sinfondo.png"},
                                                   "x": w // 2, "y": round(h * 0.62), "w": 760, "sombra": 0.4})
        else:
            lam["fondo"] = {**lam.get("fondo", {}), "tipo": "imagen", "src": {"tipo": "img", "f": archivo}}
        puestas.append(i + 1)
    if puestas:
        guardar(pid, p)
    return puestas


def carpeta_descargas():
    """La carpeta de Descargas de esta PC (la de verdad, aunque Windows la haya movido a otro disco u OneDrive),
    igual que en la Sala de edición. Se puede fijar otra en config.local.json → carpeta_descargas."""
    c = nucleo.CONFIG.get("carpeta_descargas")
    if c and Path(c).is_dir():
        return Path(c)
    if os.name == "nt":
        import ctypes
        try:
            class GUID(ctypes.Structure):
                _fields_ = [("a", ctypes.c_uint32), ("b", ctypes.c_uint16), ("c", ctypes.c_uint16), ("d", ctypes.c_ubyte * 8)]
            descargas = GUID(0x374DE290, 0x123F, 0x4565, (ctypes.c_ubyte * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
            p = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(descargas), 0, None, ctypes.byref(p)) == 0:
                ruta = Path(p.value)
                ctypes.windll.ole32.CoTaskMemFree(p)
                if ruta.is_dir():
                    return ruta
        except Exception:  # noqa: BLE001
            pass
    return Path.home() / "Downloads"


def traer_de_descargas(pid, cod, nombre, desde):
    """El archivo que la IA bajó a Descargas pasa a Flow/ de la pieza como «<código>.<ext>». Solo si se bajó ahora
    (desde: hora en que empezó el pedido), nunca uno viejo con el mismo nombre. Devuelve el nombre en Flow/."""
    base = carpeta_descargas().resolve()
    f = (base / Path(str(nombre)).name).resolve()
    if f.parent != base or not f.is_file() or f.suffix.lower() not in EXT:
        raise ValueError(f"no encontré «{nombre}» en Descargas")
    if f.stat().st_mtime < desde:
        raise ValueError(f"«{nombre}» en Descargas es de antes: no se bajó ahora")
    destino = ruta_imagen(pid) / f"{cod}{f.suffix.lower()}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():  # la de antes queda guardada aparte, no se pisa
        destino.rename(destino.with_name(f"{cod}_antes_{time.strftime('%Y%m%d-%H%M%S')}{destino.suffix}"))
    destino.write_bytes(f.read_bytes())
    return destino.name


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


def sincronizar(forzar=False, esperar=False):
    """Trae de Drive lo que hicieron otras PCs (marca, briefs y diseño). Como mucho cada 2 minutos.
    esperar: no por detrás (el botón ↻ espera a que llegue todo)."""
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
    if esperar:
        tarea()
    else:
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


def _foto_existe(src, c):
    """La foto está de verdad: en Flow/ de la pieza o en _MARCA. Una pieza escrita por la IA ya trae el nombre
    de cada foto (C05_N1.jpg) antes de que se genere en Flow: eso todavía no cuenta."""
    import marca
    try:
        return (marca.ruta_archivo(src.get("f", "")) if src.get("tipo") == "marca" else c / "Flow" / Path(src.get("f", "")).name).is_file()
    except ValueError:
        return False


def _fotos_de(lam):
    """Todas las fotos que la lámina tiene anotadas: la de fondo y las de sus capas."""
    f = lam.get("fondo", {})
    return ([f["src"]] if f.get("tipo") == "imagen" and f.get("src") else []) + \
        [x.get("src") or {} for x in lam.get("capas", []) if x.get("tipo") == "imagen"]


def _faltante(lam, c):
    """La primera foto de Flow que la lámina espera y que todavía no existe, o None."""
    return next((s for s in _fotos_de(lam) if s.get("tipo") == "img" and not _foto_existe(s, c)), None)


def _con_foto(lam, c):
    """La lámina tiene su foto: al menos una puesta (de Flow o del producto) y ninguna que espere y no esté.
    «Foto de fondo» sin foto elegida no cuenta."""
    return any(_foto_existe(s, c) for s in _fotos_de(lam)) and not _faltante(lam, c)


def _con_textos(p):
    """La IA ya la escribió (aunque los textos aún no estén en las láminas) o alguien le puso textos a mano."""
    return bool((p.get("guion") or {}).get("laminas")) or any(
        c.get("tipo") == "texto" and (c.get("texto") or "").strip() for l in p.get("laminas", []) for c in l.get("capas", []))


def _resumen(p):
    """Lo que la revisión compara entre las piezas de la semana: el diseño de la portada y del CTA, el texto del CTA y el título."""
    g = (p.get("guion") or {}).get("laminas") or []
    cta = next((l for l in reversed(g) if l.get("rol") == "cta"), {})
    ultima = (p.get("laminas") or [{}])[-1]
    textos = [c for c in ultima.get("capas", []) if c.get("tipo") == "texto" and (c.get("texto") or "").strip()]
    # el texto del CTA: el que armó la sala («accion»/«cta») o, en piezas hechas a mano, el que invita a hacer algo
    accion = next((c["texto"] for c in textos if c.get("rol") in ("accion", "cta")), "") or next(
        (c["texto"] for c in textos if re.search(r"coment|escr[ií]be|whatsapp|pide|p[ií]delo|link|guarda|agenda", c["texto"], re.I)), "")
    return {"portada": (g[0].get("diseno") if g else "") or "", "cta": cta.get("diseno") or "", "cta_texto": accion or cta.get("accion") or "",
            "titulo": (g[0].get("titulo") if g else "") or p.get("titulo", "")}


def _del_plan(d):
    """Los (día, tema) del plan de la semana: así se reconocen las piezas del brief creadas antes de guardar su origen."""
    try:
        plan = json.loads((d / "semana.json").read_text(encoding="utf-8")).get("plan") or []
    except (FileNotFoundError, ValueError):
        return set()
    return {(_dia(c.get("dia")), (c.get("tema") or "").strip()) for c in plan}


def biblioteca():
    """Cada pieza con su semana, su fecha (el día que sale) y su miniatura, de la más nueva a la más vieja."""
    out = []
    for s in semanas():
        d = raiz() / s["rel"]
        lunes = _lunes_de_semana(s["semana"])
        plan = _del_plan(d)
        for c in sorted(x for x in d.iterdir() if x.is_dir()):
            try:
                p = json.loads((c / "pieza.json").read_text(encoding="utf-8"))
            except (FileNotFoundError, ValueError):
                continue
            dia = p.get("dia", "")
            fecha = (lunes + dt.timedelta(days=DIAS.index(dia))).isoformat() if lunes and dia in DIAS else (lunes.isoformat() if lunes else "")
            finales = sorted((c / "FINAL").glob("L*.png")) if (c / "FINAL").is_dir() else []
            mini = "miniatura.png" if (c / "miniatura.png").exists() else (f"FINAL/{finales[0].name}" if finales else "")
            laminas, guion = p.get("laminas", []), (p.get("guion") or {}).get("laminas") or []
            origen =p.get("origen") or ("brief" if (dia, (p.get("titulo") or "").strip()) in plan
                                         else "video" if p.get("video") else "pedido" if p.get("pedido") else "mano")
            out.append({"rel": s["rel"], "mes": s["mes"], "semana": s["semana"], "id": c.name, "titulo": p.get("titulo", c.name),
                        "tipo": p.get("tipo", "carrusel"), "formato": p.get("formato", "4:5"), "dia": dia, "fecha": fecha,
                        "nivel": p.get("nivel", ""), "publico": p.get("publico", ""), "estilo": p.get("estilo", ""),
                        "laminas": len(laminas), "exportado": bool(finales), "miniatura": mini, "origen": origen, "fuente": p.get("fuente"), "resumen": _resumen(p),
                        "actualizado": p.get("actualizado", ""), "por": p.get("por", ""), "pedido": p.get("pedido", ""),
                        "con_textos": _con_textos(p), "con_fotos": any(_con_foto(l, c) for l in laminas),
                        "laminas_con_foto": sum(1 for l in laminas if _con_foto(l, c)),
                        # las que la IA puede generar en Flow: sin foto y con su prompt (si es 0, se suben a mano)
                        "faltan_con_prompt": sum(1 for l, g in zip(laminas, guion) if (g.get("flow") or "").strip() and not _con_foto(l, c))})
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
