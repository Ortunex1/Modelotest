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
| 1. El corpus (aporte principal) | 1–12, en paralelo | En curso |
| 2. Motor de enlaces (URL) | 3–8 | Siguiente |
| 3. Motor de texto (BETO) | 9–16 | Pendiente |
| 4. Evaluación y contraste | 17–21 | Notebook listo (`03_evaluacion`) |
| 5. Prototipo de alerta | 20–24 | Pendiente |

## Estructura del repositorio

```
sis/
├── data/
│   ├── crudo/          # lo que llega de la ficha + datasets públicos (NO a Git)
│   ├── anonimizado/    # corpus.csv + ficha + manual de etiquetado (SÍ a Git)
│   └── particiones/    # train.csv, val.csv, test.csv (NO a Git)
├── notebooks/
│   ├── 00_exploracion.ipynb   # baseline tonto (Fase 0) ✔
│   ├── 01_url.ipynb           # motor de enlaces (Fase 2)
│   ├── 02_texto.ipynb         # BETO (Fase 3)
│   └── 03_evaluacion.ipynb    # McNemar, F1, matriz (Fase 4)
├── modelos/            # pesos entrenados (NO a Git)
├── resultados/         # métricas y figuras del Capítulo IV
├── scripts/
│   ├── ocr.py          # imagen (captura) -> texto, con Tesseract (Fase 1)
│   ├── anonimizar.py   # quita datos personales del corpus (Fase 1)
│   └── kappa.py        # acuerdo entre etiquetadores, kappa de Cohen (Fase 1)
├── docs/
│   ├── MANUAL_DATOS_Y_PRUEBAS.md   # cómo cargar datos, correr y probar cada punto
│   └── MANUAL_CODIGO_02_texto.md   # BETO explicado línea por línea (para estudiar/defender)
├── requirements.txt
└── .gitignore
```

## Manuales de estudio

- [Manual de datos y pruebas](docs/MANUAL_DATOS_Y_PRUEBAS.md) — flujo de datos, cómo correr y evaluar.

Código explicado **línea por línea** (para estudiar y defender):
- [`00_exploracion`](docs/MANUAL_CODIGO_00_exploracion.md) — baseline tonto.
- [`01_url`](docs/MANUAL_CODIGO_01_url.md) — baseline de URL (LogReg / Naive Bayes).
- [`01b_url_cnn`](docs/MANUAL_CODIGO_01b_url_cnn.md) — CNN de caracteres (deep learning).
- [`02_texto`](docs/MANUAL_CODIGO_02_texto.md) — BETO (deep learning, texto).
- [`03_evaluacion`](docs/MANUAL_CODIGO_03_evaluacion.md) — McNemar, métricas y veredicto (Fase 4).
- [`scripts`](docs/MANUAL_CODIGO_scripts.md) — anonimización y kappa de Cohen.

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
