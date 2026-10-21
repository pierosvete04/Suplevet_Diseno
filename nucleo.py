"""Lo común de la Sala de diseño: dónde están el código y los datos, la configuración y el corte de trabajos.

  RAIZ   carpeta del código (se reemplaza entera al actualizar)
  DATOS  lo de esta PC: configuración, copia local de Drive, modelos (nunca se toca al actualizar)
  SUITE  lo que comparten las tres salas en esta PC (la conexión a Drive y la de Claude): se conecta una vez
"""
import json
import os
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = Path(os.environ.get("DISENO_DATOS") or RAIZ / "datos")
DATOS.mkdir(parents=True, exist_ok=True)
SUITE = Path(os.environ.get("SALAS_SUITE") or Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Salas")
SUITE.mkdir(parents=True, exist_ok=True)
VERSION = (RAIZ / "VERSION").read_text(encoding="utf-8").strip() if (RAIZ / "VERSION").exists() else "0.0.0"
LOCAL_PATH = DATOS / "config.local.json"


def _leer(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


CONFIG = {**_leer(RAIZ / "config.json"), **_leer(LOCAL_PATH)}


def guardar_config(cambios):
    """Guarda en datos/config.local.json (no se comparte entre PCs)."""
    CONFIG.update(cambios)
    local = _leer(LOCAL_PATH)
    local.update(cambios)
    LOCAL_PATH.write_text(json.dumps(local, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Cancelar el trabajo en curso ----------
CANCELAR = threading.Event()
PROCESOS = set()  # rclone o Claude corriendo ahora: se cortan al cancelar


class Cancelado(Exception):
    pass


def cancelar():
    CANCELAR.set()
    for p in list(PROCESOS):
        try:
            p.kill()
        except OSError:
            pass


def revisar_cancelado():
    if CANCELAR.is_set():
        CANCELAR.clear()
        raise Cancelado("Cancelado")
