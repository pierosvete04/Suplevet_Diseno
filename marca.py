"""La marca del proyecto: la sala no trae ninguna marca adentro, la lee del Drive del proyecto.

  _MARCA/
    marca.json     nombre, colores, tipografías, palabras a evitar, frases obligatorias, cierres
    logos/         logos en PNG con fondo transparente
    productos/     fotos reales del producto sin fondo (se ponen tal cual, nunca generadas)

Sin _MARCA (proyecto nuevo) la sala funciona igual con una paleta neutra; desde Configuración se puede
crear el marca.json de base, o importar la marca desde la plantilla (importar_marca.py, común con la Sala de edición).
marca.json se guarda con la misma forma que en la Sala de edición: logos {archivo: {nombre, uso, fondo}}, colores con «uso».
"""
import json
import os
import threading
import time
from pathlib import Path

import conexion

CARPETA = "_MARCA"
NEUTRA = {
    "nombre": "",
    "colores": [{"nombre": "Tinta", "hex": "#1F2933"}, {"nombre": "Claro", "hex": "#F4F4F5"}, {"nombre": "Blanco", "hex": "#FFFFFF"},
                {"nombre": "Acento", "hex": "#2563EB"}, {"nombre": "Cálido", "hex": "#F59E0B"}],
    "texto_oscuro": "#1F2933",
    "texto_claro": "#FFFFFF",
    "fuentes": {"titulo": "Bebas", "cuerpo": "DM Sans"},
    "evitar": [],
    "obligatorio": [],
    "cierres": ["Guárdalo y compártelo"],
    "cta": {"titulo": "¿Te interesa?", "texto": "Escríbenos y te asesoramos", "boton": "Escríbenos"},
    "notas_para_claude": "",
}
EXT = (".png", ".webp", ".jpg", ".jpeg")


def carpeta():
    return conexion.CACHE / CARPETA


def datos():
    try:
        propia = json.loads((carpeta() / "marca.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        propia = {}
    out = {**NEUTRA, **propia}
    out["logos"] = _archivos("logos")
    out["productos"] = _archivos("productos")
    out["tiene_marca"] = bool(propia)
    return out


def _archivos(sub):
    d = carpeta() / sub
    return sorted(f"{sub}/{f.name}" for f in d.iterdir() if f.suffix.lower() in EXT) if d.is_dir() else []


def ruta_archivo(rel):
    """logos/x.png o productos/x.png, sin salir de _MARCA."""
    base = carpeta().resolve()
    ruta = (base / rel).resolve()
    if base not in ruta.parents:
        raise ValueError("Archivo de marca no válido")
    return ruta


def crear_base(nombre):
    """marca.json de partida para un proyecto nuevo (se completa a mano o con Claude).
    Devuelve True si lo creó y False si ya existía (no se pisa)."""
    d = carpeta()
    (d / "logos").mkdir(parents=True, exist_ok=True)
    (d / "productos").mkdir(exist_ok=True)
    creada = not (d / "marca.json").exists()
    if creada:
        (d / "marca.json").write_text(json.dumps({**NEUTRA, "nombre": nombre}, ensure_ascii=False, indent=1), encoding="utf-8")
    conexion.en_segundo_plano(conexion.subir, CARPETA)
    return creada


def bajar():
    conexion.bajar(CARPETA)


# ---------- Guardar (lo usa importar_marca, igual que en la Sala de edición) ----------
TIPOS = {"logos": (".png", ".webp", ".jpg", ".jpeg"), "productos": (".png", ".webp", ".jpg", ".jpeg"), "fuentes": (".ttf", ".otf")}
USOS_COLOR = ("principal", "secundario", "acento", "fondo", "texto", "otro")
USOS_LOGO = ("principal", "horizontal", "icono", "otro")
FONDOS_LOGO = ("oscuro", "claro", "cualquiera")  # sobre qué fondo se ve bien
# un logo sin datos: por su nombre se sabe casi siempre cuál es (logo_blanco va sobre fondo oscuro)
USO_POR_NOMBRE = (("icono", ("icono", "ícono", "icon", "isotipo", "simbolo", "símbolo")), ("horizontal", ("horizontal", "horiz")))
FONDO_POR_NOMBRE = (("oscuro", ("blanco", "white", "claro", "light", "negativo")), ("claro", ("negro", "black", "oscuro", "dark", "azul", "color")))
_cerrojo = threading.Lock()


def raiz():
    return carpeta()


def _adivinar(archivo, tabla, sino):
    n = Path(archivo).stem.lower()
    return next((valor for valor, palabras in tabla if any(p in n for p in palabras)), sino)


def _leer_json():
    try:
        return json.loads((carpeta() / "marca.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def _nombres(sub):
    d = carpeta() / sub
    return sorted(f.name for f in d.iterdir() if f.is_file() and f.suffix.lower() in TIPOS[sub]) if d.is_dir() else []


def logos_info():
    """{archivo: {archivo, nombre, uso, fondo}} de los logos que hay."""
    info = _leer_json().get("logos")
    info = info if isinstance(info, dict) else {}
    return {a: {"archivo": a, "nombre": (info.get(a) or {}).get("nombre") or Path(a).stem,
                "uso": (info.get(a) or {}).get("uso") or _adivinar(a, USO_POR_NOMBRE, "principal"),
                "fondo": (info.get(a) or {}).get("fondo") or _adivinar(a, FONDO_POR_NOMBRE, "cualquiera")}
            for a in _nombres("logos")}


def _limpio(d):
    out = {"nombre": str(d.get("nombre") or "")[:80]}
    colores = []
    for c in (d.get("colores") or [])[:24]:
        h = str((c or {}).get("hex") or "").strip()
        if len(h) == 7 and h.startswith("#"):
            colores.append({"nombre": str(c.get("nombre") or "")[:40], "hex": h.upper(),
                            "uso": c.get("uso") if c.get("uso") in USOS_COLOR else "otro"})
    out["colores"] = colores
    for k in ("texto_oscuro", "texto_claro"):
        if d.get(k):
            out[k] = str(d[k])[:7]
    out["fuentes"] = {k: v for k, v in (d.get("fuentes") or {}).items() if k in ("titulo", "cuerpo", "subtitulos") and isinstance(v, str) and v}
    hay = _nombres("logos")
    out["logos"] = {l["archivo"]: {"nombre": str(l.get("nombre") or "")[:40], "uso": l.get("uso") if l.get("uso") in USOS_LOGO else "otro",
                                   "fondo": l.get("fondo") if l.get("fondo") in FONDOS_LOGO else "cualquiera"}
                    for l in d.get("logos") or [] if isinstance(l, dict) and l.get("archivo") in hay}
    for k in ("evitar", "obligatorio", "cierres"):
        out[k] = [str(x).strip()[:200] for x in (d.get(k) or []) if str(x).strip()][:60]
    cta = d.get("cta") or {}
    out["cta"] = {k: str(cta.get(k) or "")[:200] for k in ("titulo", "texto", "boton")}
    out["notas_para_claude"] = str(d.get("notas_para_claude") or "")[:4000]
    return out


def guardar(d):
    """Guarda marca.json (lo que no se toca aquí, como la dirección visual, se conserva) y lo sube a Drive."""
    with _cerrojo:
        r = carpeta()
        r.mkdir(parents=True, exist_ok=True)
        nuevo = {**_leer_json(), **_limpio(d), "cambio": time.time()}
        tmp = r / ".marca.json.part"
        tmp.write_text(json.dumps(nuevo, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, r / "marca.json")
    conexion.en_segundo_plano(conexion.subir, CARPETA)
    return datos()


def guardar_archivo(tipo, nombre, contenido, subir=True):
    """Un logo, una foto de producto o una tipografía. Devuelve el nombre con que quedó."""
    if tipo not in TIPOS:
        raise ValueError("Tipo de archivo de marca no válido")
    nombre = "".join(c if c.isalnum() or c in "._- " else "_" for c in Path(nombre).name).strip()[:80]
    if not nombre or Path(nombre).suffix.lower() not in TIPOS[tipo]:
        raise ValueError({"logos": "Sube el logo en PNG (mejor con fondo transparente), WEBP o JPG",
                          "productos": "Sube la foto en PNG (sin fondo), WEBP o JPG",
                          "fuentes": "Sube la tipografía en .ttf u .otf"}[tipo])
    if not contenido:
        raise ValueError("El archivo llegó vacío")
    if tipo == "fuentes" and contenido[:4] not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        raise ValueError("Ese archivo no es una tipografía que se pueda leer")
    d = carpeta() / tipo
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{nombre}.part"
    tmp.write_bytes(contenido)
    os.replace(tmp, d / nombre)
    if subir:
        conexion.en_segundo_plano(conexion.subir, CARPETA)
    return nombre


def copiar_fuentes():
    """La Sala de diseño dibuja con sus propias tipografías: las de la marca quedan en _MARCA/fuentes para la Sala de edición."""
