"""Sala de diseño: carruseles y posts con fotos de Flow, quitar fondos, la marca del proyecto y exportar al Publicador.

Abrir:  python servidor.py   →   http://localhost:8767   (o SalaDiseno.exe)
"""
import base64
import datetime as dt
import json
import mimetypes
import os
import re
import shutil
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
import gemini
import guiones
import importar_marca
import marca
import nucleo
import piezas
import recorte
import videos as videos_edicion

PUERTO = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else int(os.environ.get("DISENO_PUERTO") or 8767)
FUENTES = nucleo.RAIZ / "fuentes"
LATIDO = {"ultimo": 0.0, "adios": 0.0}
INICIO = time.time()


# ---------- La fila de trabajos de la IA ----------
# Corren de a uno: todos usan la misma IA (Claude o Gemini en Antigravity), el mismo Chrome para Flow y la misma semana.
# Antes el segundo pedido fallaba («Ya hay un trabajo en curso») y todas las esperas de la página leían el mismo trabajo:
# un pedido podía recibir el resultado de otro y «Cancelar» cortaba lo que estuviera corriendo. Ahora cada trabajo tiene
# su número, espera su turno en la fila y la página pregunta por el suyo (/api/trabajo?id=); la tuerca los muestra todos.
TRABAJOS = []
_FNS = {}
_FILA = threading.Condition()
_OBRERO = {"vivo": False}
NOMBRES = {"escribir": "Escribir los textos", "rehacer": "Rehacer el prompt de una foto", "revisar": "Revisar con ojo de IA",
           "fotos": "Generar fotos en Flow", "pedido": "Pedido a la IA"}


def _publico(t):
    return {k: v for k, v in t.items() if k != "clave"}


def _titulo_de(pid):
    try:
        return piezas.leer(pid)[0].get("titulo") or pid
    except Exception:  # noqa: BLE001 — una pieza borrada no corta la lista
        return pid


def lanzar(accion, fn, pid=None, lamina=None, nota=None, titulo=None, clave=None):
    """Pone el trabajo en la fila y devuelve su número. pid, lamina y nota dicen de qué pieza es, para que la página
    lo retome si se recarga a mitad. Si lo mismo ya está en la fila (doble clic), se devuelve ese."""
    clave = clave or f"{accion}|{pid or ''}|{lamina if lamina is not None else ''}"
    titulo = titulo if titulo is not None else (_titulo_de(pid) if pid else "")
    semana = piezas.semana_actual().split("/")[-1]
    with _FILA:
        igual = next((t for t in TRABAJOS if t["clave"] == clave and t["estado"] in ("en cola", "corriendo")), None)
        if igual:
            return igual["id"]
        tid = f"t{int(time.time() * 1000)}"
        while any(t["id"] == tid for t in TRABAJOS):
            tid += "x"
        TRABAJOS.append({"id": tid, "clave": clave, "accion": accion, "nombre": NOMBRES.get(accion, accion), "titulo": titulo,
                         "pieza": pid, "lamina": lamina, "nota": nota, "semana": semana, "estado": "en cola", "activo": True,
                         "mensaje": "En la fila", "error": None, "resultado": None, "creado": time.time(), "empezo": None, "termino": None})
        _FNS[tid] = fn
        terminados = [t for t in TRABAJOS if not t["activo"]]
        for t in terminados[:-20]:  # se guardan los últimos 20 terminados
            TRABAJOS.remove(t)
        _FILA.notify_all()
        if not _OBRERO["vivo"]:
            _OBRERO["vivo"] = True
            threading.Thread(target=_obrero, daemon=True).start()
    return tid


def _obrero():
    while True:
        with _FILA:
            t = next((x for x in TRABAJOS if x["estado"] == "en cola"), None)
            while t is None:
                _FILA.wait()
                t = next((x for x in TRABAJOS if x["estado"] == "en cola"), None)
            t.update(estado="corriendo", mensaje="Empezando…", empezo=time.time())
            fn = _FNS.pop(t["id"])
        nucleo.CANCELAR.clear()  # un «Cancelar» de antes no corta este trabajo

        def avance(m, t=t):
            t["mensaje"] = m
        try:
            t["resultado"] = fn(avance)
            t.update(estado="listo", mensaje="Listo")
        except Exception as e:
            t.update(estado="cancelado" if str(e) == "Cancelado" else "error", error=str(e))
            traceback.print_exc()
        finally:
            t.update(activo=False, termino=time.time())


def trabajo(tid=None):
    """Uno (por número) con su lugar en la fila; sin número, el que está corriendo (o el último)."""
    with _FILA:
        if tid:
            t = next((x for x in TRABAJOS if x["id"] == tid), None)
        else:
            t = next((x for x in TRABAJOS if x["estado"] == "corriendo"), None) or (TRABAJOS[-1] if TRABAJOS else None)
        if not t:
            return {"activo": False, "estado": "no existe", "error": "Ese trabajo ya no está en la lista" if tid else None, "mensaje": ""}
        r = _publico(t)
        if t["estado"] == "en cola":
            antes = [x for x in TRABAJOS if x["activo"] and x["creado"] < t["creado"]]
            ahora = next((x for x in antes if x["estado"] == "corriendo"), None)
            r["delante"] = len(antes)
            r["mensaje"] = ("En la fila: va después de 1 trabajo" if len(antes) == 1 else f"En la fila: hay {len(antes)} trabajos antes") \
                + (f" (ahora: {ahora['nombre'].lower()}{' · ' + ahora['titulo'] if ahora['titulo'] else ''})" if ahora else "")
        r["gemini"] = dict(gemini.ACTUAL) if t["estado"] == "corriendo" and gemini.ACTUAL else None
        return r


def todos_los_trabajos():
    with _FILA:
        ids = [t["id"] for t in reversed(TRABAJOS)]
    return [trabajo(i) for i in ids]


def cancelar_trabajo(tid=None):
    """En la fila: sale de la fila. Corriendo: se corta. Sin número: el que está corriendo."""
    with _FILA:
        if tid:
            t = next((x for x in TRABAJOS if x["id"] == tid), None)
        else:
            t = next((x for x in TRABAJOS if x["estado"] == "corriendo"), None)
        if not t or not t["activo"]:
            return
        if t["estado"] == "en cola":
            _FNS.pop(t["id"], None)
            t.update(estado="cancelado", activo=False, error="Cancelado", termino=time.time())
            return
    nucleo.cancelar()


def hay_trabajo():
    return any(t["activo"] for t in TRABAJOS)


def escribir_y_guardar(pid, idea, avance, rel=None):
    """La IA escribe la pieza y el guion queda guardado en ella aunque la página ya no esté esperando
    (al abrir la pieza, sus textos van a las láminas vacías). rel: la semana donde se pidió."""
    pieza, _ = piezas.leer(pid, rel)
    r = asistente.escribir_pieza(pieza, idea, marca.datos(), avance)
    pieza, _ = piezas.leer(pid, rel)  # la de ahora: pudo cambiar mientras la IA escribía
    pieza["guion"] = r
    if not (pieza.get("copy") or "").strip():
        pieza["copy"] = r.get("copy", "")
    piezas.guardar(pid, pieza, rel)
    piezas.subir(pid, rel)
    return {**r, "guardado": True}


def rehacer_y_guardar(pid, n, nota, foto, avance, rel=None):
    """El prompt nuevo de Flow va a su lámina, con la nota del equipo, aunque la página ya no esté esperando."""
    r = asistente.rehacer_foto(piezas.leer(pid, rel)[0], n, nota, marca.datos(), avance)
    pieza, _ = piezas.leer(pid, rel)
    g = pieza.setdefault("guion", {"laminas": [], "copy": pieza.get("copy", "")})
    while len(g["laminas"]) <= n:
        g["laminas"].append({"rol": "", "titulo": "", "texto": "", "flow": ""})
    g["laminas"][n]["flow"] = r.get("flow", "")
    g["laminas"][n].setdefault("notas", []).append({"fecha": time.strftime("%d/%m/%y %H:%M"), "quien": piezas.quien(), "nota": nota, "foto": foto})
    piezas.guardar(pid, pieza, rel)
    piezas.subir(pid, rel)
    return {**r, "guardado": True}


def guardar_revision(pid, laminas):
    """Las láminas que manda la página (JPG chicos) quedan en datos/revision/<pieza>/L01.jpg… para que la IA las mire.
    Se reemplazan en cada revisión: no se suben a Drive."""
    carpeta = nucleo.DATOS / "revision" / re.sub(r"[^\w\-]+", "_", pid)[:60]
    if carpeta.exists():
        shutil.rmtree(carpeta, ignore_errors=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = []
    for i, x in enumerate(laminas[:12], 1):
        datos = base64.b64decode(str(x).split(",", 1)[-1])
        jpg = datos.startswith(b"\xff\xd8")
        if not jpg and not datos.startswith(b"\x89PNG"):
            raise ValueError(f"La lámina {i} no llegó bien")
        f = carpeta / (f"L{i:02d}" + (".jpg" if jpg else ".png"))
        f.write_bytes(datos)
        rutas.append(str(f))
    if not rutas:
        raise ValueError("No llegó ninguna lámina para revisar")
    return rutas


def generar_fotos(ids, avance):
    """La IA genera en Google Flow las fotos que les faltan a esas piezas (con el prompt de cada lámina), las baja a
    Descargas con su código, y la sala las pasa a Flow/ de cada pieza, las pone en su lámina y las sube a Drive."""
    pedidos = {pid: piezas.fotos_que_faltan(pid) for pid in ids}
    items = [x for lista in pedidos.values() for x in lista]
    if not items:
        return {"hechos": [], "pendientes": [], "piezas": ids, "mensaje": "No falta ninguna foto con prompt de Flow en estas piezas."}
    de_quien = {x["id"]: pid for pid, lista in pedidos.items() for x in lista}
    avance(f"Faltan {len(items)} fotos: la IA las genera en Google Flow…")
    desde = time.time() - 5
    proyecto = "Diseño " + piezas.semana_actual().split("/")[-1].split(" · ")[0]  # «Diseño S03»
    r = asistente.generar_fotos(items, proyecto, piezas.carpeta_descargas(), avance=avance)
    pendientes = [{"id": p.get("codigo") or p.get("id"), "motivo": p.get("motivo", "")} for p in r.get("pendientes") or []]
    llegadas = {}
    for cod, nombre in (r.get("archivos") or {}).items():
        if cod not in de_quien:
            continue
        try:
            llegadas.setdefault(de_quien[cod], {})[cod] = piezas.traer_de_descargas(de_quien[cod], cod, nombre, desde)
        except (ValueError, OSError) as e:
            pendientes.append({"id": cod, "motivo": str(e)})
    hechos = []
    for pid, fotos in llegadas.items():
        piezas.poner_fotos(pid, fotos)
        piezas.subir(pid)
        hechos += list(fotos)
    pendientes += [{"id": x, "motivo": "la IA no la bajó"} for x in de_quien if x not in hechos and x not in {p["id"] for p in pendientes}]
    return {"hechos": hechos, "pendientes": pendientes, "piezas": ids}


def al_cerrar_ventana():
    """La ventana dijo adiós: si no vuelve en unos segundos (no era una recarga), la sala se apaga."""
    if not os.environ.get("DISENO_VENTANA"):
        return

    def esperar():
        marca_t = LATIDO["adios"]
        time.sleep(6)
        while hay_trabajo():
            time.sleep(2)
        if LATIDO["ultimo"] <= marca_t:
            piezas.subir_pendientes()  # lo editado a mano que aún no subió
            os._exit(0)
    threading.Thread(target=esperar, daemon=True).start()


def estado():
    sem = piezas.semana_actual()
    return {"version": nucleo.VERSION, "drive": conexion.estado(), "cuenta": cuenta.estado(), "marca": marca.datos(), "quien": piezas.quien(),
            "semana": sem, "semanas": piezas.semanas(), "piezas": piezas.listar(sem), "formatos": piezas.FORMATOS,
            "tiene_brief": bool(piezas.videos_de_la_semana(sem)),  # sin brief, «Los videos de esta semana» no sirve
            "recortador": {"listo": recorte.modelo_listo(), **recorte.ESTADO_MODELO}}


class Servidor(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return  # la ventana se cerró o se recargó a mitad de una respuesta: no es un error
        super().handle_error(request, client_address)


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
            elif u.path == "/api/marca_importar/ver":  # lo subido para importar, antes de guardarlo (para verlo en la revisión)
                try:
                    f = importar_marca.ruta_staging(q.get("id", [""])[0], q.get("ruta", [""])[0])
                except ValueError:
                    return self.send_error(404)
                self._archivo(f.parent, f.name)
            elif u.path == "/img":
                self._archivo(piezas.ruta_imagen(q["id"][0]), q["f"][0])
            elif u.path == "/api/biblioteca":
                self._json({"piezas": piezas.biblioteca(), "semanas": piezas.semanas(), "pedidos": piezas.pedidos_todos()[:60]})
            elif u.path == "/archivo":  # miniatura o lámina exportada de cualquier semana
                ruta = piezas.archivo(q["rel"][0], q["id"][0], q["f"][0])
                self._archivo(ruta.parent, ruta.name)
            elif u.path == "/api/guiones":  # los cuerpos de los guiones de la Sala de edición (solo lectura)
                self._json({"guiones": guiones.listar(forzar="forzar" in q), "actualizando": guiones.actualizando()})
            elif u.path == "/api/videos":  # los videos terminados de la Sala de edición (solo lectura)
                self._json({"videos": videos_edicion.listar(forzar="forzar" in q), "producciones": videos_edicion.producciones(),
                            "actualizando": videos_edicion.actualizando()})
            elif u.path == "/video_mini":
                ruta = videos_edicion.miniatura(q["ruta"][0])
                self._archivo(ruta.parent, ruta.name)
            elif u.path == "/api/estado":
                piezas.sincronizar()
                videos_edicion.precalentar()  # la lista de videos se pide ya, por detrás, para que la pestaña Videos abra al instante
                guiones.precalentar()  # y los guiones, para «Crear con IA → Cuerpos de los guiones»
                self._json(estado())
            elif u.path == "/api/pieza":
                pid = q["id"][0]
                datos, editando = piezas.leer(pid)
                piezas.marcar_editando(pid)
                self._json({"id": pid, "datos": datos, "imagenes": piezas.imagenes(pid), "editando": editando})
            elif u.path == "/api/trabajo":  # gemini: si se está esperando a Gemini, la carpeta y el mensaje para pegar
                self._json(trabajo(q.get("id", [None])[0]))
            elif u.path == "/api/trabajos":  # la tuerca: lo que corre, lo que espera y lo último que terminó
                self._json({"trabajos": todos_los_trabajos()})
            elif u.path == "/api/semana_nombre":  # cómo se va a llamar la semana de esa fecha (y si ya existe)
                self._json(piezas.semana_de(q.get("fecha", [""])[0], q.get("tema", [""])[0]))
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
            elif u.path == "/api/cuenta/carpetas":  # elegir la carpeta del proyecto (cuenta.js): las carpetas de la cuenta
                self._json({"ok": True, **cuenta.carpetas_para_elegir()})
            else:
                self.send_error(404)
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def do_POST(self):
        if self.client_address[0] not in ("127.0.0.1", "::1"):
            return self.send_error(403)
        # Una página de internet abierta en el navegador podría mandar órdenes a la app: el navegador siempre dice
        # de qué página viene el pedido (Origin) y tiene que ser la app misma.
        origen = self.headers.get("Origin")
        if origen and origen != "null" and urlparse(origen).netloc.lower() != (self.headers.get("Host") or "").lower():
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
                    fecha = str(b.get("fecha") or "").strip()
                    if not fecha:
                        raise ValueError("Elige una fecha de la semana")
                    try:
                        dt.date.fromisoformat(fecha)
                    except ValueError:
                        raise ValueError("Esa fecha no es válida. Elígela en el calendario.") from None
                    rel = piezas.crear_semana(fecha, str(b.get("tema") or "")[:40], plan)
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
                rel = b.get("rel") or None
                try:
                    datos = piezas.guardar(b["id"], b["datos"], rel=rel, rev=None if b.get("forzar") else b.get("rev"), de_la_pagina=True)
                except piezas.Choque as ch:  # la página pregunta: cargar la de afuera o dejar la suya encima
                    return self._json({"ok": False, "choque": True, "error": str(ch), "por": ch.datos.get("por", ""),
                                       "actualizado": ch.datos.get("actualizado", "")}, 409)
                if not rel or rel == piezas.semana_actual():
                    piezas.marcar_editando(b["id"])
                piezas.subir_luego(b["id"], rel)
                self._json({"ok": True, "rev": datos["rev"]})
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
                elif b.get("accion") == "modo":  # qué IA usar: auto (Claude y si no, Gemini), claude o gemini
                    asistente.elegir_modo(str(b.get("modo", "")))
                    return self._json({"ok": True, **asistente.estado()})
                elif b.get("accion") == "gemini_abrir":  # volver a abrir Antigravity con el pedido y copiar el mensaje
                    return self._json({"ok": True, "abierto": gemini.abrir(), "copiado": gemini.copiar_mensaje()})
                elif b.get("accion") == "escribir":  # la pieza se lee cuando le toca (puede esperar en la fila)
                    pid, idea = b["id"], str(b.get("idea", ""))[:2000]
                    tid = lanzar("escribir", lambda av, rel=piezas.semana_actual(): escribir_y_guardar(pid, idea, av, rel), pid=pid)
                elif b.get("accion") == "rehacer":  # la nota del equipo sobre una foto -> el prompt de Flow nuevo de esa lámina
                    nota = str(b.get("nota", "")).strip()[:1000]
                    if len(nota) < 3:
                        raise ValueError("Escribe qué hay que cambiar en la foto")
                    pid, n, foto = b["id"], int(b.get("lamina", 0)), str(b.get("foto", ""))[:200]
                    tid = lanzar("rehacer", lambda av, rel=piezas.semana_actual(): rehacer_y_guardar(pid, n, nota, foto, av, rel), pid=pid, lamina=n, nota=nota)
                elif b.get("accion") == "revisar":  # «✦ Revisar con ojo de IA»: la IA mira las láminas armadas y propone cambios
                    pid = b["id"]
                    imagenes = guardar_revision(pid, b.get("laminas") or [])
                    capas, avisos = b.get("capas") or [], [str(a)[:200] for a in (b.get("avisos") or [])][:30]
                    tid = lanzar("revisar", lambda av: asistente.revisar_pieza(piezas.leer(pid)[0], imagenes, capas, avisos, marca.datos(), av), pid=pid)
                elif b.get("accion") == "fotos":  # «✦ Generar fotos con IA» de una o varias piezas de la semana
                    ids = [str(x) for x in (b.get("ids") or [])][:20]
                    if not ids:
                        raise ValueError("Elige al menos una pieza")
                    tid = lanzar("fotos", lambda av: generar_fotos(ids, av), pid=ids[0] if len(ids) == 1 else None,
                                 titulo=None if len(ids) == 1 else f"{len(ids)} piezas", clave="fotos|" + ",".join(sorted(ids)))
                else:
                    raise ValueError("Acción no válida")
                self._json({"ok": True, "trabajo": tid})
            elif u.path == "/api/pedido":  # un pedido libre: Claude decide las piezas y la sala las crea en la semana
                b = self._cuerpo()
                texto = str(b.get("texto", "")).strip()[:8000]
                cuerpos = guiones.elegidos(b.get("cuerpos") or [])[:12]  # «Cuerpos de los guiones»: un carrusel por cada uno
                if b.get("cuerpos") and not cuerpos:
                    raise ValueError("No encontré esos cuerpos en los guiones de Drive. Toca «Actualizar» en la lista y vuelve a elegirlos.")
                if cuerpos and len(texto) < 5:
                    texto = f"Un carrusel por cada uno de los {len(cuerpos)} cuerpos elegidos de los guiones."
                if len(texto) < 5:
                    raise ValueError("Escribe qué quieres que se haga")
                videos = piezas.videos_de_la_semana() if b.get("videos") else None
                if b.get("videos") and not videos:
                    raise ValueError("Esta semana no tiene brief con sus videos. Elige «Nada» o un video de la Sala de edición.")
                semana, datos_marca = piezas.semana_actual(), marca.datos()
                ruta_video = str(b.get("video") or "")
                disenos = b.get("disenos") if isinstance(b.get("disenos"), dict) else {}  # los que se marcaron en «Diseños»

                def hacer(av):
                    referencia = None
                    if ruta_video:
                        av("Leyendo el video de referencia y su guion…")
                        referencia = videos_edicion.contexto(ruta_video)
                    r = asistente.resolver_pedido(texto, datos_marca, semana, videos, av, referencia=referencia, disenos=disenos, cuerpos=cuerpos)
                    hechas = piezas.crear_desde_pedido(texto, r, semana, video=ruta_video)
                    piezas.subir()
                    return {"piezas": hechas}
                corto = texto if len(texto) <= 60 else texto[:60].rsplit(" ", 1)[0] + "…"
                tid = lanzar("pedido", hacer, titulo=corto, clave="pedido|" + texto)
                self._json({"ok": True, "trabajo": tid})
            elif u.path == "/api/entrar":  # entrar con Google (se abre el navegador una vez)
                e = cuenta.entrar(str(self._cuerpo().get("link", "")))
                piezas.sincronizar(forzar=True)
                self._json({"ok": True, "cuenta": e})
            elif u.path == "/api/cuenta/primera":  # entrar y elegir (o crear) la carpeta del proyecto (cuenta.js)
                r = cuenta.primera(self._cuerpo())
                if "editor" in r:  # ya eligió carpeta
                    conexion.tras_elegir_carpeta(r)
                self._json({"ok": True, **r})
            elif u.path == "/api/salir":
                cuenta.cerrar_sesion()
                self._json({"ok": True})
            elif u.path == "/api/cerrar_dispositivo":
                cuenta.cerrar_en(str(self._cuerpo()["id"]))
                self._json({"ok": True})
            elif u.path == "/api/cerrar_otros":
                self._json({"ok": True, "cerrados": cuenta.cerrar_en_todas_menos_esta()})
            elif u.path == "/api/marca_plantilla":  # importar la marca sin Claude (importar_marca.py, común con la Sala de edición)
                self._json({"ok": True, "ruta": str(importar_marca.guardar_plantilla())})
            elif u.path == "/api/marca_importar":
                acc = q.get("accion", [""])[0]
                if acc == "nuevo":
                    self._json({"ok": True, "id": importar_marca.nuevo()})
                elif acc == "subir":
                    n = int(self.headers.get("Content-Length") or 0)
                    if n > 400 * 1024 * 1024:
                        raise ValueError("El archivo es muy grande (máximo 400 MB)")
                    self._json({"ok": True, "archivos": importar_marca.recibir(q["id"][0], q["ruta"][0], self.rfile.read, n)})
                elif acc == "analizar":
                    self._json({"ok": True, **importar_marca.analizar(self._cuerpo().get("id"))})
                elif acc == "aplicar":
                    b = self._cuerpo()
                    self._json({"ok": True, **importar_marca.aplicar(b.get("id"), b.get("propuesta") or {})})
                else:
                    raise ValueError("Acción no válida")
            elif u.path == "/api/marca_base":
                creada = marca.crear_base(str(self._cuerpo().get("nombre", ""))[:60])
                self._json({"ok": True, "creada": creada, "marca": marca.datos()})
            elif u.path == "/api/miniatura":  # la lámina 1 en chico, para la biblioteca (?id=&rel=)
                piezas.guardar_miniatura(q["id"][0], self._crudo(4 * 1024 * 1024), q.get("rel", [None])[0])
                self._json({"ok": True})
            elif u.path == "/api/nombre":
                nucleo.guardar_config({"nombre": str(self._cuerpo().get("nombre", "")).strip()[:40]})
                self._json({"ok": True})
            elif u.path == "/api/cancelar":  # {id}: ese trabajo (sale de la fila o se corta); sin id, el que está corriendo
                cancelar_trabajo(str(self._cuerpo().get("id") or "") or None)
                self._json({"ok": True})
            elif u.path == "/api/refrescar":  # ↻: trae todo de Drive de nuevo (piezas, marca, briefs, videos y guiones)
                piezas.sincronizar(forzar=True, esperar=True)
                for m in (videos_edicion, guiones):
                    threading.Thread(target=m.listar, kwargs={"forzar": True}, daemon=True).start()
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
    try:  # al abrir, la sala va a la semana de hoy (si no existe, la crea; con el brief, sus piezas)
        piezas.crear_semana(time.strftime("%Y-%m-%d"))
    except Exception as e:
        print("Semana:", e, flush=True)
    cuenta.latido(forzar=True)
    srv = Servidor(("127.0.0.1", PUERTO), H)
    print(f"Lista para usar en {time.time() - INICIO:.1f} s", flush=True)
    srv.serve_forever()
