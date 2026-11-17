# Detección y alerta temprana de estafas por suplantación de identidad

Smishing, phishing y quishing mediante aprendizaje profundo.

**Postulante:** Jose Manuel Ortuño Alanoca — UPEA, Ingeniería de Sistemas
**Documento guía oficial:** *Ruta al Detector Multicanal* (perfil de tesis).

## Idea general

Dos **motores** que alimentan un **módulo de decisión** con tres niveles:
**Seguro / Sospechoso / Peligroso**.

1. **Motor de texto (BETO)** — mensajes (smishing) en español. *Aporte principal.*
2. **Motor de enlaces (URL)** — phishing por características de la URL.
3. **QR (quishing)** — se decodifica a URL y entra al motor de enlaces (no es un modelo aparte).

## Las 6 fases (CRISP-DM)

| Fase | Semanas | Estado |
|---|---|---|
| 0. Entorno y esqueleto | 1 | **Hecho** |
| 1. El corpus (aporte principal) | 1–12, en paralelo | **En curso** — 445 reales + 2000 de aumento; falta recolectar ≥ 300 reales nuevos |
| 2. Motor de enlaces (URL) | 3–8 | Baseline **hecho** (F1 0.935 en test); falta la CNN |
| 3. Motor de texto (BETO) | 9–16 | **Hecho** — test: BETO F1 0.921 vs baseline 0.907 (McNemar p = 1.0) |
| 4. Evaluación y contraste | 17–21 | Texto evaluado; URL y QR pendientes |
| 5. Prototipo de alerta | 20–24 | Pendiente |

👉 **Estado detallado, resultados y decisiones:** [`docs/BITACORA.md`](docs/BITACORA.md)

## Estructura del repositorio

```
sis/
├── data/
│   ├── crudo/                 # datasets públicos y archivos locales (NO a Git)
│   ├── anonimizado/
│   │   └── particiones/       # corpus de TEXTO: train / train_solo_real / val / test (SÍ a Git)
│   └── particiones/           # cortes del motor de URL (NO a Git)
├── notebooks/
│   ├── 00_exploracion.ipynb   # baseline tonto (Fase 0) ✔
│   ├── 01_url.ipynb           # baseline de URL ✔
│   ├── 01b_url_cnn.ipynb      # CNN de caracteres (URL) — pendiente de correr
│   ├── 02_texto.ipynb         # BETO + evaluación final en TEST (Colab) ✔
│   ├── 03_evaluacion.ipynb    # McNemar, F1, matriz (Fase 4)
│   └── registros/             # corridas antiguas guardadas como evidencia
├── scripts/
│   ├── revisar_datos.py       # diagnostica el Excel: útiles / repetidos / alertas
│   ├── corregir_datos.py      # aplica las correcciones de etiquetas (con respaldo)
│   ├── armar_corpus.py        # anonimiza y particiona sin fuga (familias)
│   ├── entrenar_beto_local.py # BETO en la PC (sin GPU) [--aumento]
│   ├── evaluar_test_texto.py  # examen final en TEST + McNemar
│   ├── anonimizar.py          # quita datos personales ([MONTO], [TELEFONO], [NOMBRE]...)
│   ├── ocr.py                 # imagen (captura) -> texto, con Tesseract
│   ├── kappa.py               # acuerdo entre etiquetadores
│   └── generar_corpus_sintetico.py  # (histórico, ya no se usa)
├── modelos/                   # pesos entrenados (NO a Git)
├── resultados/                # predicciones y métricas del Capítulo IV
├── docs/                      # manuales, guías y bitácora
└── requirements.txt
```

Fuera del repo, en `../DOC/` (nunca se sube, tiene datos sin anonimizar):
`datos.xlsx` (tus reales), `dataset_suplantacion_2041_4040.tsv` (aumento),
`datos_revisados.xlsx`, `corpus_completo.xlsx` y el respaldo `datos_respaldo_2026-11-17.xlsx`.

## Manuales de estudio

Para estudiar y defender:
- [**Bitácora de experimentos**](docs/BITACORA.md) — qué se hizo, resultados y decisiones.
- [Guía de recolección del corpus](docs/GUIA_RECOLECCION_CORPUS.md) — qué mensajes buscar (casos difíciles, regla del gancho).
- [Justificación y metodología](docs/JUSTIFICACION_Y_METODOLOGIA.md) — por qué deep learning y CRISP-DM.
- [Glosario de conceptos](docs/GLOSARIO_CONCEPTOS.md) — los términos clave explicados a fondo.
- [Guía de defensa](docs/GUIA_DEFENSA.md) — preguntas típicas del tribunal y cómo responderlas.
- [Manual de datos y pruebas](docs/MANUAL_DATOS_Y_PRUEBAS.md) — flujo de datos, cómo correr y evaluar.

Código explicado **línea por línea** (para estudiar y defender):
- [`00_exploracion`](docs/MANUAL_CODIGO_00_exploracion.md) — baseline tonto.
- [`01_url`](docs/MANUAL_CODIGO_01_url.md) — baseline de URL (LogReg / Naive Bayes).
- [`01b_url_cnn`](docs/MANUAL_CODIGO_01b_url_cnn.md) — CNN de caracteres (deep learning).
- [`02_texto`](docs/MANUAL_CODIGO_02_texto.md) — BETO (deep learning, texto).
- [`03_evaluacion`](docs/MANUAL_CODIGO_03_evaluacion.md) — McNemar, métricas y veredicto (Fase 4).
- [`scripts`](docs/MANUAL_CODIGO_scripts.md) — anonimización, kappa, OCR y la cadena del corpus (revisar → corregir → armar → evaluar).

## Reglas que no se rompen (disciplina)

- El conjunto de **prueba** se abre **una sola vez**, al final.
- **Semilla aleatoria fija** en cada partición y entrenamiento (reproducibilidad).
- **Bitácora** de cada experimento: fecha, configuración, métricas.
- **Nunca** subir datos sin anonimizar a GitHub ni a ningún servicio público.
- Guardar las **predicciones**, no solo las métricas (McNemar las necesita fila por fila).
- **Escribir mientras se construye**: cada fase cerrada es una sección de la tesis.

## Entorno

- **Datos y baseline**: local (pandas, scikit-learn).
- **Entrenar BETO**: Google Colab con GPU (o GPU local si está disponible).
- Instalar dependencias: `pip install -r requirements.txt`
  (para OCR, además instalar Tesseract-OCR con idioma `spa`).
