# Detección y alerta temprana de estafas por suplantación de identidad

Smishing, phishing y quishing mediante aprendizaje profundo.

**Postulante:** Jose Manuel Ortuño Alanoca — UPEA, Ingeniería de Sistemas

## Idea general

El sistema tiene **dos motores** que alimentan un **módulo de decisión**:

1. **Motor de texto (BETO)** — clasifica mensajes (smishing) en español. *Aporte principal.*
2. **Motor de URL** — clasifica enlaces (phishing) por sus características.
3. **QR (quishing)** — se decodifica a una URL y se apoya en el motor de URL.
4. **Módulo de decisión + prototipo** — integra todo y emite: **Seguro / Sospechoso / Peligroso**. *(Al final.)*

## Metodología: CRISP-DM

| Fase | Estado |
|---|---|
| 1. Comprensión del problema | Hecho |
| 2. Comprensión y preparación de datos | **En curso** |
| 3. Modelado | Siguiente |
| 4. Evaluación | Pendiente |
| 5. Despliegue (prototipo) | Pendiente |

## Estructura del repositorio

```
sis/
├── data/
│   ├── raw/          # datasets públicos descargados (NO se suben a Git)
│   ├── processed/    # datos limpios y listos para entrenar
│   └── corpus/       # corpus boliviano propio (nuestro aporte)
├── notebooks/        # exploración y entrenamiento (Colab-compatible)
├── src/
│   ├── text_engine/  # motor de texto (BETO)
│   ├── url_engine/   # motor de URL + baseline
│   └── qr_engine/    # lectura/generación de QR
├── models/           # pesos entrenados (NO se suben a Git)
├── reports/          # métricas, matrices de confusión, figuras
└── requirements.txt
```

## Orden de trabajo

1. **Datos**: descargar datasets de URL y SMS + construir el corpus boliviano.
2. **Baseline**: Regresión Logística y Naive Bayes (para comparar).
3. **Motor de texto (BETO)**: el aporte central.
4. **Motor de URL**, luego **QR**.
5. **Prototipo con alertas** (al final).

## Entorno

- **Datos y baseline**: local (pandas, scikit-learn).
- **Entrenar BETO**: Google Colab (GPU gratuita) o GPU local si está disponible.
