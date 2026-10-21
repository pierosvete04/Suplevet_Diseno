# Sala de diseño

Carruseles y posts para redes, con fotos de Google Flow, quitar fondos y Claude. Es parte de una suite de tres
programas que comparten el mismo Drive como base de datos:

| Programa | Hace | Escribe en Drive |
|---|---|---|
| Sala de edición | Videos | sesiones de video y sus `V.FINALES/` |
| **Sala de diseño** | Carruseles y posts | `DISEÑO/` |
| Publicador | Calendario, publicar, métricas | `PUBLICADOR/` |

La sala no trae ninguna marca adentro: la marca de cada proyecto vive en su Drive, en `_MARCA/`.

## Instalar

1. Descarga `SalaDiseno-Instalador-vX.Y.Z.exe` del último release y ábrelo (no pide administrador).
2. Abre **Sala de diseño** → ⚙ Configuración:
   - **Drive:** pega el link de la carpeta del proyecto y toca Conectar (se abre Google una vez). Si la Sala de edición ya
     está conectada en esa PC, toca «Usar la conexión de la Sala de edición».
   - **Claude:** «Iniciar sesión en Claude» (necesita la app de escritorio de Claude).
   - **Tu nombre:** para el aviso «lo está editando…».
3. Las actualizaciones llegan solas: arriba aparece «Hay una versión nueva» → Actualizar ahora.

## Cómo se ordena el Drive del proyecto

```
<carpeta del proyecto>/
├── _MARCA/        marca.json (colores, tipografías, palabras a evitar, frases obligatorias, cierres), logos/, productos/
├── _SEMANAS/      S03 · 19-25 OCT/brief.json  ← lo deja la estrategia; la sala crea las piezas del plan
└── DISEÑO/2026-10 OCTUBRE/S03 · 19-25 OCT · TEMA/
      LUN · C01 · Tema/   pieza.json, Flow/ (fotos), FINAL/ (L01.png… + copy.txt)
```

Cada carpeta tiene un solo programa que escribe; los demás solo leen. Las llaves de acceso (Drive y Claude) quedan en
la PC (`%LOCALAPPDATA%\Salas`), nunca en Drive.

## Desarrollo

```
python servidor.py --puerto 8766
```

Publicar una versión: sube `VERSION`, escribe `NOTAS_VERSION.md`, haz commit y sube el tag `vX.Y.Z`.
GitHub Actions arma el instalador y el release.
