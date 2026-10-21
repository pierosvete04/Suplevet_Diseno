"""La marca del proyecto: la sala no trae ninguna marca adentro, la lee del Drive del proyecto.

  _MARCA/
    marca.json     nombre, colores, tipografías, palabras a evitar, frases obligatorias, cierres
    logos/         logos en PNG con fondo transparente
    productos/     fotos reales del producto sin fondo (se ponen tal cual, nunca generadas)

Sin _MARCA (proyecto nuevo) la sala funciona igual con una paleta neutra; desde Configuración se puede
crear el marca.json de base.
"""
import json

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
    """marca.json de partida para un proyecto nuevo (se completa a mano o con Claude)."""
    d = carpeta()
    (d / "logos").mkdir(parents=True, exist_ok=True)
    (d / "productos").mkdir(exist_ok=True)
    if not (d / "marca.json").exists():
        (d / "marca.json").write_text(json.dumps({**NEUTRA, "nombre": nombre}, ensure_ascii=False, indent=1), encoding="utf-8")
    conexion.en_segundo_plano(conexion.subir, CARPETA)


def bajar():
    conexion.bajar(CARPETA)
