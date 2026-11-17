# Bitácora de experimentos

Registro de cada experimento: fecha, datos, configuración, métricas y decisiones.
(Regla del proyecto: *"Bitácora de cada experimento"*. Sirve para escribir el Capítulo III y IV.)

---

## Resumen de resultados — motor de texto

| # | Fecha | Entrenamiento | Evaluado en | Baseline F1 | **BETO F1** | McNemar | Dónde |
|---|---|---|---|---|---|---|---|
| 1 | 2026-11-12 | 800 sintéticos + 172 reales (corpus viejo) | val 57 | 1.000 | 1.000 | — | ❌ inválido: usó DEMO por orden de celdas |
| 2 | 2026-11-17 | 800 sintéticos + 267 reales (corpus viejo, con gemelos) | val 89 | 0.900 | 0.895 | — | `notebooks/registros/02_texto_run1_corpus_anterior.ipynb` |
| 3 | 2026-11-17 | **267 reales** (corpus nuevo, sin gemelos) | val 89 | 0.827 | **0.895** | p = 0.23 | `resultados/02_texto_val_log_solo_real.txt` |
| 4 | 2026-11-17 | **267 reales + 2000 aumento** | val 89 | 0.816 | **0.949** | p ≈ 0.002 | (Colab) |
| **5** | **2026-11-17** | **267 reales + 2000 aumento** | **TEST 89** | **0.907** | **0.921** | **p = 1.0** | `resultados/03_texto_test_*_aumento.*` |

**Configuración final elegida en validación:** reales + aumento (exp. 4 > exp. 3).

---

## 2026-11-17 — Revisión del corpus, partición sin fuga y test final

### Datos
- `DOC/datos.xlsx`: 913 filas → **445 mensajes reales distintos** tras anonimizar y quitar duplicados
  (232 copias exactas + 206 variantes de monto/número/nombre).
- `DOC/dataset_suplantacion_2041_4040.tsv`: **2000 mensajes de aumento** (1000/1000), 0 repetidos,
  ninguno parecido a un real (similitud máx. 0.31). Se usan **solo en train**.
- Correcciones (`scripts/corregir_datos.py`, respaldo en `DOC/datos_respaldo_2026-11-17.xlsx`):
  - 20 mensajes "fraudulento" que **no pedían nada** → `legitimo` (regla del gancho).
  - 4 ambiguos → hoja `descartados`.
  - 5 fechas futuras → 2026-11-17. `empresa_courier` → `courier`.
- Anonimización: se agregaron reglas para **nombres de persona** (10 nombres encontrados) → `[NOMBRE]`.

### Partición (sin fuga)
- Familias de mensajes casi iguales (similitud ≥ 0.80) enteras en una sola partición (`StratifiedGroupKFold`).
- train 267 reales (+2000 aumento) · val 89 · test 89 (52 legítimo / 37 fraude), **100% reales en val/test**.
- Verificado: 0 textos repetidos, 0 familias partidas, 0 gemelos entre particiones.
- **Efecto:** el baseline bajó de 0.900 a 0.827 en val → antes estaba inflado por los gemelos.

### Experimentos en validación
- **Exp. 3 (solo reales, CPU local, 4 épocas, max_len 64):** BETO 0.895 vs baseline 0.827.
  Val loss 0.283 → 0.255 → 0.297 → 0.247 (sin sobreajuste fuerte).
- **Exp. 4 (reales + aumento, Colab T4, max_len 96):** BETO 0.949 vs baseline 0.816.
  Mejor época 2. Val loss 0.334 → 0.346 → 0.383 → 0.446 (algo de sobreajuste desde la época 2).
  McNemar val: 10 solo-BETO vs 0 solo-baseline.
- **Hallazgo:** el aumento **ayuda a BETO (+0.054)** pero **no al baseline (−0.011)**.
  Un modelo entrenado **solo** con aumento cae a F1 0.67 en reales → el aumento complementa, no reemplaza.

### Evaluación final en TEST (exp. 5) — abierto una sola vez

| Métrica | BETO | Baseline |
|---|---|---|
| Exactitud | 0.933 | 0.921 |
| Precisión | 0.897 | 0.895 |
| Recall | 0.946 | 0.919 |
| **F1** | **0.921** | 0.907 |
| AUC-ROC | 0.992 | 0.986 |

- Matrices: BETO `[[48, 4], [2, 35]]` · baseline `[[48, 4], [3, 34]]` (filas = real legítimo, fraude).
- **McNemar exacta:** solo BETO = 2, solo baseline = 1 → **p = 1.0, no significativo**.
- **Criterio F1 ≥ 0.90:** BETO cumple (0.921). El baseline también (0.907).
- **Análisis de errores:** 3 de los 4 falsos positivos de BETO (Obras Públicas, Entel fibra, YPFB)
  son mensajes **frontera** relabelados ese día de fraude → legítimo: imitan el estilo del fraude
  pero no piden nada. 1 fraude sin gancho claro (Min. Economía, cronograma de rentas) lo fallan ambos.

### Decisiones
- Los mensajes generados se llaman **"aumento"** (aumento de datos) y se **declaran** en la metodología.
  No se presentan como reales.
- El test **ya está usado**: no se cambian etiquetas ni configuración para mejorar ese número.
- Para buscar significancia estadística: **recolectar ≥ 300 mensajes reales nuevos** y formar un
  **test nuevo** con ellos (declarado como segunda colección).

### Redacción sugerida (Capítulo IV)
> *"BETO superó a la línea base en todas las métricas (F1 0.921 vs 0.907; AUC 0.992 vs 0.986) y
> cumplió el criterio F1 ≥ 0.90. Sin embargo, la prueba de McNemar no mostró una diferencia
> estadísticamente significativa (p = 1.0), debido al tamaño reducido del conjunto de prueba
> (89 mensajes, con solo 3 casos discordantes)."*

---

## Pendientes

1. **Corpus:** recolectar ≥ 300 mensajes reales nuevos (`docs/GUIA_RECOLECCION_CORPUS.md`) → test nuevo.
2. **Motor URL:** entrenar la CNN de caracteres (`01b_url_cnn`) en Colab y compararla con el baseline
   (F1 0.935 en test) con McNemar.
3. **QR:** conjunto de QR legítimos/maliciosos → decodificar → motor URL.
4. **Prototipo** (Gradio): texto + URL + QR, con fusión (si el SMS trae enlace, pasa por ambos motores).
5. Guardar el modelo BETO final (en Colab no se descargó; reentrenar y guardar en Drive).
6. Decidir qué hacer con nombres en commits antiguos del repo público (limpiar historial o privatizar).
