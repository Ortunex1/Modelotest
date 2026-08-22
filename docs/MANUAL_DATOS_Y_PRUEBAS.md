# Manual de datos y pruebas

Guía práctica de **cómo cargar los datos, cómo fluyen por el proyecto, cómo correr
cada notebook y cómo verificar los resultados**. Pensado para que puedas estudiarlo
y explicarlo en la defensa.

---

## 1. Panorama: qué datos usa cada motor

Tu sistema tiene tres vectores. Cada uno usa datos distintos:

| Motor | Dato que necesita | De dónde sale | ¿Necesita GPU? |
|---|---|---|---|
| **URL** (enlaces) | URLs etiquetadas (phishing/benignas) | Dataset público de Kaggle | Baseline no; CNN sí |
| **Texto** (BETO) | Mensajes en español etiquetados | **Tu corpus boliviano** | Sí (Colab) |
| **QR** | (no tiene datos propios) | Se decodifica a URL → usa el motor de URL | — |

> Idea central para la defensa: el motor de URL se entrena con datos **públicos**
> (las URL no tienen idioma); el motor de texto necesita **tu corpus en español**,
> y ese es tu aporte. El QR **no es un modelo nuevo**: la foto se convierte en URL.

---

## 2. El recorrido de los datos (flujo)

```
      ┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────┐
      │  DESCARGA   │ →   │   LIMPIEZA   │ →   │   PARTICIÓN      │ →   │  MODELO  │
      │ (o corpus)  │     │ (duplicados, │     │ train/val/test   │     │ entrena  │
      │             │     │ anonimizar)  │     │ (semilla fija)   │     │ y evalúa │
      └─────────────┘     └──────────────┘     └──────────────────┘     └──────────┘
        data/crudo/         (en el código)      data/particiones/       modelos/ + resultados/
```

Carpetas involucradas:

- `data/crudo/` — el dato tal cual llega (CSV de Kaggle, respuestas de la ficha). **No se sube a Git.**
- `data/anonimizado/` — el corpus ya sin datos personales (`corpus.csv`). **Sí se versiona.**
- `data/particiones/` — los cortes train/val/test que consume el modelo. **No se sube a Git.**
- `modelos/` — pesos entrenados. **No se sube a Git.**
- `resultados/` — métricas y figuras del Capítulo IV.

---

## 3. Las tres particiones (concepto clave)

El corpus se corta en tres y **cada una tiene un rol distinto**:

| Partición | Para qué sirve | ¿Cuántas veces la miras? |
|---|---|---|
| **train** (entrenamiento) | El modelo *aprende* de aquí | Todas las que quieras |
| **val** (validación) | Decides configuración: épocas, umbrales, qué modelo es mejor | Muchas veces |
| **test** (prueba) | El número final que reportas en la tesis | **UNA sola vez, al final (Fase 4)** |

> **Regla que no se rompe:** si miras el *test* para tomar decisiones y luego lo usas
> para reportar, tus números quedan contaminados y la tesis pierde validez. Por eso en
> los notebooks de modelado (`01`, `01b`, `02`) solo se evalúa en **val**; el *test*
> se abre recién en `03_evaluacion.ipynb`.

En el código, el corte se hace así (mismo patrón en todos los notebooks):

```python
train, resto = train_test_split(df, test_size=0.30, stratify=df['etiqueta'], random_state=SEED)
val, test    = train_test_split(resto, test_size=0.50, stratify=resto['etiqueta'], random_state=SEED)
# Resultado: 70% train, 15% val, 15% test
```

- `stratify=df['etiqueta']` → conserva la proporción de clases en cada corte (importante con desbalance).
- `random_state=SEED` → el corte es **siempre el mismo** (reproducible ante el tribunal).

---

## 4. Motor de URL — cargar los datos

### 4.1 Descargar el dataset

1. Entra a **https://www.kaggle.com/datasets/sid321axn/malicious-urls-dataset**
2. Inicia sesión → botón **Download**.
3. Descomprime y saca **`malicious_phish.csv`**.
4. Colócalo en:
   ```
   data/crudo/malicious_phish.csv
   ```

El archivo tiene dos columnas: `url` (la dirección) y `type` (benign / phishing / malware / defacement).

### 4.2 Cómo lo carga el código

En `01_url.ipynb` y `01b_url_cnn.ipynb`, el dato se convierte a **binario**:

```python
def a_binario(v):
    s = str(v).strip().lower()
    return 'legitimo' if s in ('benign', ...) else 'fraudulento'
```

- `benign` → **legitimo**
- `phishing`, `malware`, `defacement` → **fraudulento**

Así ambos motores (URL y texto) hablan el mismo idioma de etiquetas: `legitimo` / `fraudulento`.

### 4.3 Correr y probar (baseline ML — local)

1. Abre `01_url.ipynb` con el kernel **Python (tesis)**.
2. **Kernel → Restart & Run All**.
3. Qué mirar:
   - El conteo de clases (¿está muy desbalanceado?).
   - El **F1 (fraudulento)** de Regresión Logística y Naive Bayes.
   - La matriz de confusión en `resultados/01_url_matriz_logreg.png`.
4. Se guardan los modelos en `modelos/` y las predicciones en `resultados/`.

### 4.4 Correr y probar (CNN — Colab)

1. Sube `01b_url_cnn.ipynb` a Colab y activa **GPU**.
2. Sube `malicious_phish.csv` a Colab (icono de carpeta → subir) **o** usa la API de Kaggle.
3. Ejecuta todo. Mira el **F1 de la CNN** y compáralo con el del baseline.

---

## 5. Motor de texto (BETO) — cargar los datos

### 5.1 Construir el corpus (tu aporte)

A diferencia de las URL, **este dato no se descarga: se recolecta**. Pasos (Fase 1):

1. **Ficha de Google** (ver `data/anonimizado/FICHA_RECOLECCION.md`): 6 campos + consentimiento. Difúndela.
2. **OCR** de las capturas → texto (`pytesseract`).
3. **Anonimizar** (regla ética):
   ```bash
   python scripts/anonimizar.py data/crudo/mensajes.csv data/anonimizado/corpus.csv
   ```
4. **Etiquetado doble** + kappa de Cohen (acuerdo entre etiquetadores):
   ```bash
   python scripts/kappa.py etiquetados.csv etiqueta_a etiqueta_b
   ```

El resultado es `data/anonimizado/corpus.csv` con columnas `texto` y `etiqueta`.

### 5.2 Cómo lo carga el código

`02_texto.ipynb` busca el corpus automáticamente (local o clonado en Colab):

```python
candidatos = [
    Path.cwd().parent / 'data' / 'anonimizado' / 'corpus.csv',   # local
    Path('Modelotest/data/anonimizado/corpus.csv'),              # Colab tras git clone
    Path('data/anonimizado/corpus.csv'),
]
ruta = next((p for p in candidatos if p.exists()), None)
```

Si no encuentra corpus (o tiene menos de 40 filas), usa un **DEMO en español** para
que el notebook corra igual y puedas estudiar el flujo. Cuando tengas tu corpus real,
lo detecta solo.

### 5.3 Correr y probar (Colab)

1. Abre `02_texto.ipynb` en Colab → activa **GPU**.
2. Descomenta la celda de preparación (instala `transformers`, clona el repo).
3. **Ejecutar todo**. Qué mirar, en orden:
   - `GPU disponible: True` (si es False, activa la GPU).
   - El **F1 del baseline** clásico en español.
   - El entrenamiento de BETO época por época (la pérdida debe bajar).
   - La comparación final: **¿F1 de BETO > F1 del baseline?**
4. Copia `modelos/beto_final` a tu **Google Drive** (Colab borra archivos al cerrar).

---

## 6. Cómo se hacen las pruebas (evaluación)

### 6.1 Qué métricas mirar y por qué

Todas salen de la **matriz de confusión** (4 casillas):

|  | Predijo legítimo | Predijo fraudulento |
|---|---|---|
| **Es legítimo** | ✅ Verdadero Negativo | ❌ Falso Positivo (asusta de más) |
| **Es fraudulento** | ❌ **Falso Negativo (el error caro)** | ✅ Verdadero Positivo |

- **Exactitud (accuracy):** % de aciertos. **Engaña con clases desbalanceadas** (por eso el baseline tonto de la Fase 0).
- **Precisión:** de lo que marcó como fraude, cuánto era fraude de verdad.
- **Exhaustividad (recall):** de todos los fraudes reales, cuántos detectó. *Clave: un fraude no detectado es peligroso.*
- **F1:** equilibrio entre precisión y recall. **La métrica principal.**
- **AUC-ROC:** capacidad de separar clases en todos los umbrales.

> El **falso negativo** (fraude que se cuela) es el error caro en tu problema. Por eso
> miramos el **F1 de la clase fraudulento**, no la exactitud global.

### 6.2 La prueba de McNemar (Fase 4)

Compara **dos modelos sobre las MISMAS URLs/mensajes** de test:

```python
from statsmodels.stats.contingency_tables import mcnemar
# tabla = [[ambos aciertan, solo A acierta],
#          [solo B acierta, ambos fallan]]
print(mcnemar(tabla, exact=False, correction=True))
```

- Da un **valor p**. Si p < 0.05, la diferencia entre el modelo profundo y el baseline
  es **estadísticamente significativa** (no es casualidad).
- **Ese valor p decide tu hipótesis**, no la simple diferencia de F1.
- Criterio técnico adicional del PDF: **F1 ≥ 0.90**.

### 6.3 Checklist de una prueba bien hecha

- [ ] Semilla fija en particiones y entrenamiento.
- [ ] El *test* se abrió una sola vez.
- [ ] Se guardaron las **predicciones** (no solo las métricas) — McNemar las necesita.
- [ ] Se revisaron a mano ~20 errores del modelo (material para la discusión).

---

## 7. Resumen: orden en que se corre todo

| Paso | Notebook / script | Dónde | Necesita |
|---|---|---|---|
| 1 | `00_exploracion.ipynb` | Local | nada (ya corre) |
| 2 | `01_url.ipynb` (baseline) | Local | `malicious_phish.csv` en `data/crudo/` |
| 3 | `01b_url_cnn.ipynb` (CNN) | Colab | dataset URL + GPU |
| 4 | `scripts/anonimizar.py` + `kappa.py` | Local | tu corpus recolectado |
| 5 | `02_texto.ipynb` (BETO) | Colab | `corpus.csv` + GPU |
| 6 | `03_evaluacion.ipynb` (McNemar) | Local | las predicciones guardadas |

> Consejo del PDF: **escribe la tesis mientras construyes.** Cada notebook cerrado es
> una sección del Capítulo IV.
