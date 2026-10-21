"""Sala de diseño: carruseles y posts con fotos de Flow, quitar fondos, la marca del proyecto y exportar al Publicador.

Abrir:  python servidor.py   →   http://localhost:8766   (o SalaDiseno.exe)
"""
import base64
import json
import mimetypes
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import actualizador
import asistente
import conexion
import cuenta
import marca
import nucleo
import piezas
import recorte
import videos as videos_edicion

PUERTO = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else int(os.environ.get("DISENO_PUERTO") or 8766)
FUENTES = nucleo.RAIZ / "fuentes"
TRABAJO = {"activo": False, "accion": None, "mensaje": "", "error": None, "resultado": None}
LATIDO = {"ultimo": 0.0, "adios": 0.0}


def lanzar(accion, fn):
    """Corre algo largo (Claude) en segundo plano; la página pregunta por /api/trabajo."""
    if TRABAJO["activo"]:
        raise RuntimeError("Ya hay un trabajo en curso. Espera a que termine.")
    TRABAJO.update(activo=True, accion=accion, mensaje="Empezando…", error=None, resultado=None)

    def avance(m):
        TRABAJO["mensaje"] = m

    def correr():
        try:
            TRABAJO["resultado"] = fn(avance)
            TRABAJO["mensaje"] = "Listo"
        except Exception as e:
            TRABAJO["error"] = str(e)
            traceback.print_exc()
        finally:
            TRABAJO["activo"] = False
    threading.Thread(target=correr, daemon=True).start()


def al_cerrar_ventana():
    """La ventana dijo adiós: si no vuelve en unos segundos (no era una recarga), la sala se apaga."""
    if not os.environ.get("DISENO_VENTANA"):
        return

    def esperar():
        marca_t = LATIDO["adios"]
        time.sleep(6)
        while TRABAJO["activo"]:
            time.sleep(2)
        if LATIDO["ultimo"] <= marca_t:
            os._exit(0)
    threading.Thread(target=esperar, daemon=True).start()


def estado():
    sem = piezas.semana_actual()
    return {"version": nucleo.VERSION, "drive": conexion.estado(), "cuenta": cuenta.estado(), "marca": marca.datos(), "quien": piezas.quien(),
            "semana": sem, "semanas": piezas.semanas(), "piezas": piezas.listar(sem), "formatos": piezas.FORMATOS,
            "recortador": {"listo": recorte.modelo_listo(), **recorte.ESTADO_MODELO}}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _bytes(self, b, tipo):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(b)

    def _cuerpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _crudo(self, maximo):
        n = int(self.headers.get("Content-Length") or 0)
        if n > maximo:
            raise ValueError("El archivo es muy grande")
        return self.rfile.read(n)

    def _archivo(self, base, rel):
        base = Path(base).resolve()
        ruta = (base / rel).resolve()
        if base not in ruta.parents or not ruta.is_file():
            return self.send_error(404)
        self._bytes(ruta.read_bytes(), mimetypes.guess_type(ruta.name)[0] or "application/octet-stream")

    def do_GET(self):
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            return self.send_error(403)
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/":
                self._bytes((nucleo.RAIZ / "app.html").read_bytes(), "text/html; charset=utf-8")
            elif u.path == "/cuenta.js":
                self._bytes((nucleo.RAIZ / "cuenta.js").read_bytes(), "text/javascript; charset=utf-8")
            elif u.path.startswith("/fuentes/"):
                self._archivo(FUENTES, unquote(u.path[len("/fuentes/"):]))
            elif u.path.startswith("/marca/"):
                ruta = marca.ruta_archivo(unquote(u.path[len("/marca/"):]))
                self._archivo(ruta.parent, ruta.name)
            elif u.path == "/img":
                self._archivo(piezas.ruta_imagen(q["id"][0]), q["f"][0])
            elif u.path == "/api/biblioteca":
                self._json({"piezas": piezas.biblioteca(), "semanas": piezas.semanas(), "pedidos": piezas.pedidos_todos()[:60]})
            elif u.path == "/archivo":  # miniatura o lámina exportada de cualquier semana
                ruta = piezas.archivo(q["rel"][0], q["id"][0], q["f"][0])
                self._archivo(ruta.parent, ruta.name)
            elif u.path == "/api/videos":  # los videos terminados de la Sala de edición (solo lectura)
                self._json({"videos": videos_edicion.listar(forzar="forzar" in q)})
            elif u.path == "/video_mini":
                ruta = videos_edicion.miniatura(q["ruta"][0])
                self._archivo(ruta.parent, ruta.name)
            elif u.path == "/api/estado":
                piezas.sincronizar()
                self._json(estado())
            elif u.path == "/api/pieza":
                pid = q["id"][0]
                datos, editando = piezas.leer(pid)
                piezas.marcar_editando(pid)
                self._json({"id": pid, "datos": datos, "imagenes": piezas.imagenes(pid), "editando": editando})
            elif u.path == "/api/trabajo":
                self._json(TRABAJO)
            elif u.path == "/api/claude":
                self._json(asistente.estado())
            elif u.path == "/api/version":
                self._json(actualizador.revisar(forzar="forzar" in q))
            elif u.path == "/api/latido":
                LATIDO["ultimo"] = time.time()
                cuenta.latido()
                self._json({"ok": True, "cuenta": cuenta.estado()})
            elif u.path == "/api/cuenta":
                self._json(cuenta.estado())
            elif u.path == "/api/dispositivos":
                self._json({"dispositivos": cuenta.dispositivos(), "dias_nuevo": cuenta.DIAS_NUEVO})
            else:
                self.send_error(404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def do_POST(self):
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            return self.send_error(403)
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/api/adios":
                LATIDO["adios"] = time.time()
                al_cerrar_ventana()
                return self._json({"ok": True})
            if u.path == "/api/semana":  # elegir una semana o crearla (con el brief de _SEMANAS, si lo hay)
                b = self._cuerpo()
                if b.get("accion") == "crear":
                    plan = b.get("plan") if isinstance(b.get("plan"), list) else None
                    rel = piezas.crear_semana(str(b["fecha"]), str(b.get("tema") or "")[:40], plan)
                    piezas.subir()
                else:
                    piezas.elegir_semana(str(b["rel"]))
                    rel = b["rel"]
                self._json({"ok": True, "semana": rel})
            elif u.path == "/api/pieza_nueva":
                b = self._cuerpo()
                pid, datos = piezas.nueva(str(b.get("titulo") or "Pieza")[:120], tipo=b.get("tipo", "carrusel"),
                                          dia=str(b.get("dia") or ""), formato=b.get("formato", "4:5"))
                piezas.subir(pid)
                self._json({"ok": True, "id": pid, "datos": datos})
            elif u.path == "/api/pieza":
                b = self._cuerpo()
                datos = piezas.guardar(b["id"], b["datos"])
                piezas.marcar_editando(b["id"])
                self._json({"ok": True, "datos": datos})
            elif u.path == "/api/imagen":  # cuerpo: la foto tal cual (?id=&nombre=)
                archivo = piezas.guardar_imagen(q["id"][0], q["nombre"][0], self._crudo(40 * 1024 * 1024))
                piezas.subir(q["id"][0])
                self._json({"ok": True, "archivo": archivo})
            elif u.path == "/api/mascara":  # cuerpo: 1024×1024 RGB; respuesta: 1024×1024 de máscara
                datos = self._crudo(4 * 1024 * 1024)
                if not recorte.preparar_modelo():
                    return self._json({"ok": False, "bajando": True, **recorte.ESTADO_MODELO}, 202)
                self._bytes(recorte.mascara(datos), "application/octet-stream")
            elif u.path == "/api/exportar":
                b = self._cuerpo()
                pngs = [base64.b64decode(x.split(",", 1)[-1]) for x in b["laminas"]]
                destino = piezas.exportar(b["id"], pngs, b.get("copy", ""))
                piezas.subir(b["id"])
                self._json({"ok": True, "carpeta": destino})
            elif u.path == "/api/abrir_carpeta":
                os.startfile(str(piezas.carpeta(self._cuerpo()["id"])))
                self._json({"ok": True})
            elif u.path == "/api/claude":
                b = self._cuerpo()
                if b.get("accion") == "login":
                    asistente.iniciar_sesion()
                elif b.get("accion") == "escribir":
                    pieza, _ = piezas.leer(b["id"])
                    datos_marca = marca.datos()
                    lanzar("escribir", lambda av: asistente.escribir_pieza(pieza, str(b.get("idea", ""))[:2000], datos_marca, av))
                else:
                    raise ValueError("Acción no válida")
                self._json({"ok": True})
            elif u.path == "/api/pedido":  # un pedido libre: Claude decide las piezas y la sala las crea en la semana
                b = self._cuerpo()
                texto = str(b.get("texto", "")).strip()[:8000]
                if len(texto) < 5:
                    raise ValueError("Escribe qué quieres que se haga")
                videos = piezas.videos_de_la_semana() if b.get("videos") else None
                semana, datos_marca = piezas.semana_actual(), marca.datos()
                ruta_video = str(b.get("video") or "")

                def hacer(av):
                    referencia = None
                    if ruta_video:
                        av("Leyendo el video de referencia y su guion…")
                        referencia = videos_edicion.contexto(ruta_video)
                    r = asistente.resolver_pedido(texto, datos_marca, semana, videos, av, referencia=referencia)
                    hechas = piezas.crear_desde_pedido(texto, r, semana)
                    piezas.subir()
                    return {"piezas": hechas}
                lanzar("pedido", hacer)
                self._json({"ok": True})
            elif u.path == "/api/entrar":  # entrar con Google (se abre el navegador una vez)
                e = cuenta.entrar(str(self._cuerpo().get("link", "")))
                piezas.sincronizar(forzar=True)
                self._json({"ok": True, "cuenta": e})
            elif u.path == "/api/salir":
                cuenta.cerrar_sesion()
                self._json({"ok": True})
            elif u.path == "/api/cerrar_dispositivo":
                cuenta.cerrar_en(str(self._cuerpo()["id"]))
                self._json({"ok": True})
            elif u.path == "/api/cerrar_otros":
                self._json({"ok": True, "cerrados": cuenta.cerrar_en_todas_menos_esta()})
            elif u.path == "/api/marca_base":
                marca.crear_base(str(self._cuerpo().get("nombre", ""))[:60])
                self._json({"ok": True, "marca": marca.datos()})
            elif u.path == "/api/miniatura":  # la lámina 1 en chico, para la biblioteca (?id=&rel=)
                piezas.guardar_miniatura(q["id"][0], self._crudo(4 * 1024 * 1024), q.get("rel", [None])[0])
                self._json({"ok": True})
            elif u.path == "/api/nombre":
                nucleo.guardar_config({"nombre": str(self._cuerpo().get("nombre", "")).strip()[:40]})
                self._json({"ok": True})
            elif u.path == "/api/cancelar":
                nucleo.cancelar()
                self._json({"ok": True})
            elif u.path == "/api/actualizar":
                version = actualizador.aplicar()
                self._json({"ok": True, "version": version})
                actualizador.reiniciar_luego()
            else:
                self.send_error(404)
        except Exception as e:
            traceback.print_exc()
            self._json({"ok": False, "error": str(e)}, 500)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Sala de diseño en http://localhost:{PUERTO}", flush=True)
    cuenta.iniciar("Sala de diseño", nucleo.VERSION)
    cuenta.latido(forzar=True)
    ThreadingHTTPServer(("127.0.0.1", PUERTO), H).serve_forever()
