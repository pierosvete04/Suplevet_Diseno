"""Quitar el fondo de una foto con el modelo ISNet («isnet-general-use», el mismo de rembg) y onnxruntime.

La página manda la foto achicada a 1024×1024 en bytes RGB y recibe la máscara: así no hace falta Pillow.
El modelo (170 MB) se baja una sola vez y lo comparten las salas de esta PC (nucleo.SUITE/modelos).
"""
import threading
from pathlib import Path

import nucleo

MODELO_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"
MODELO = nucleo.SUITE / "modelos" / "isnet-general-use.onnx"
MODELO_REMBG = Path.home() / ".rembg" / "models" / "isnet-general-use" / "isnet-general-use.onnx"  # si ya se usó rembg en esta PC
LADO = 1024
_sesion = {"s": None}
_candado = threading.Lock()
ESTADO_MODELO = {"bajando": False, "avance": 0, "error": None}


def modelo_listo():
    return MODELO.is_file() or MODELO_REMBG.is_file()


def _bajar_modelo():
    import requests
    MODELO.parent.mkdir(parents=True, exist_ok=True)
    tmp = MODELO.with_suffix(".parte")
    ESTADO_MODELO.update(bajando=True, avance=0, error=None)
    try:
        with requests.get(MODELO_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            total, hecho = int(r.headers.get("Content-Length") or 0), 0
            with open(tmp, "wb") as f:
                for trozo in r.iter_content(1 << 20):
                    f.write(trozo)
                    hecho += len(trozo)
                    ESTADO_MODELO["avance"] = round(hecho * 100 / total) if total else 0
        tmp.replace(MODELO)
    except Exception as e:
        ESTADO_MODELO["error"] = f"No pude bajar el recortador: {e}"
        tmp.unlink(missing_ok=True)
    finally:
        ESTADO_MODELO["bajando"] = False


def preparar_modelo():
    """Si falta el modelo, empieza a bajarlo (una vez) y devuelve False; la página vuelve a preguntar."""
    if modelo_listo():
        return True
    if not ESTADO_MODELO["bajando"]:
        threading.Thread(target=_bajar_modelo, daemon=True).start()
    return False


def _sesion_onnx():
    if _sesion["s"] is None:
        import onnxruntime as ort
        ruta = MODELO if MODELO.is_file() else MODELO_REMBG
        _sesion["s"] = ort.InferenceSession(str(ruta), providers=["CPUExecutionProvider"])
    return _sesion["s"]


def mascara(rgb):
    """rgb: bytes de una foto de 1024×1024 (R, G, B por píxel). Devuelve 1024×1024 bytes: 255 = se queda, 0 = fondo."""
    import numpy as np
    if len(rgb) != LADO * LADO * 3:
        raise ValueError("La foto no llegó en 1024×1024")
    im = np.frombuffer(rgb, dtype=np.uint8).reshape(LADO, LADO, 3).astype(np.float32)
    im = im / max(float(im.max()), 1e-6)            # igual que rembg: se divide por el píxel más claro
    im = (im - 0.5) / 1.0
    x = im.transpose(2, 0, 1)[None].astype(np.float32)
    with _candado:
        s = _sesion_onnx()
        pred = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
    mi, ma = float(pred.min()), float(pred.max())
    pred = (pred - mi) / max(ma - mi, 1e-6)
    return (pred * 255).clip(0, 255).astype(np.uint8).tobytes()
