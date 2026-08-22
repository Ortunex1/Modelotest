# Manual de código — `00_exploracion.ipynb` (baseline tonto), línea por línea

El objetivo de este notebook es la **primera evaluación** con un clasificador
*deliberadamente tonto*, para entender qué significan los números antes de entrenar
nada de verdad. Es la Fase 0.

---

## Concepto base

- **Clasificador tonto (baseline):** responde siempre la clase mayoritaria (ej. siempre
  "legítimo"). No aprende nada.
- ¿Para qué sirve? Para tener un **piso**: si tu modelo real no le gana a esto, algo está mal.
- Enseña por qué la **exactitud engaña** cuando las clases están desbalanceadas.

---

## Celda 1 — Preparación

```python
from pathlib import Path
import numpy as np
import pandas as pd
SEED = 42
np.random.seed(SEED)
```
- `Path` → manejar rutas de archivos de forma ordenada.
- `numpy` (np) → cálculos numéricos; `pandas` (pd) → tablas de datos.
- `SEED = 42` y `np.random.seed(SEED)` → fijan el azar para que los resultados sean reproducibles.

```python
RAIZ = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
PARTICIONES = RAIZ / 'data' / 'particiones'
RESULTADOS = RAIZ / 'resultados'
RESULTADOS.mkdir(exist_ok=True)
```
- `Path.cwd()` → carpeta actual. Si es `notebooks/`, sube un nivel para llegar a la raíz del proyecto.
- Define las rutas de particiones y resultados.
- `.mkdir(exist_ok=True)` → crea la carpeta `resultados/` si no existe (sin error si ya existe).

🎓 **Cómo explicarlo:** "Fijo la semilla y ordeno las rutas del proyecto; así el notebook
funciona igual desde cualquier lado."

---

## Celda 2 — Cargar datos o generar DEMO

```python
def cargar_o_demo():
    tr = PARTICIONES / 'train.csv'
    va = PARTICIONES / 'val.csv'
    if tr.exists() and va.exists():
        return pd.read_csv(tr), pd.read_csv(va), True
```
- Si existen las particiones reales, las carga.

```python
    def hacer(n):
        n_fraude = int(n * 0.15)
        etiquetas = ['fraudulento'] * n_fraude + ['legitimo'] * (n - n_fraude)
        ...
        return df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return hacer(200), hacer(60), False
```
- Si no hay datos, crea un DEMO **desbalanceado a propósito**: 15% fraude, 85% legítimo.
- Ese desbalance es clave para demostrar el problema de la exactitud.
- `df.sample(frac=1, ...)` → baraja las filas.

🎓 **Cómo explicarlo:** "Genero datos con 85% legítimos y 15% fraude para simular el
desbalance real del problema."

---

## Celda 3 — Ver el balance de clases

```python
print(train['etiqueta'].value_counts(normalize=True).round(3))
```
- `value_counts(normalize=True)` → muestra la **proporción** de cada clase (no el conteo).
- Confirma que hay desbalance (0.85 vs 0.15).

---

## Celda 4 — El clasificador tonto

```python
from sklearn.dummy import DummyClassifier
tonto = DummyClassifier(strategy='most_frequent', random_state=SEED).fit(X_tr, y_tr)
pred = tonto.predict(X_val)
print(classification_report(y_val, pred, digits=3, zero_division=0))
```
- `DummyClassifier(strategy='most_frequent')` → siempre predice la clase más frecuente.
- `.fit(X_tr, y_tr)` → "aprende" (solo memoriza cuál es la mayoritaria).
- `.predict(X_val)` → predice sobre validación.
- `classification_report(...)` → tabla con precisión, recall y F1 por clase.
- `zero_division=0` → evita error cuando una clase tiene F1 = 0.

---

## Celda 5 — El contraste clave

```python
acc = accuracy_score(y_val, pred)
f1_fraude = f1_score(y_val, pred, pos_label='fraudulento', zero_division=0)
print(f'Exactitud (accuracy): {acc:.3f}')
print(f'F1 de la clase fraudulento: {f1_fraude:.3f}')
```
- La exactitud sale ~0.85 (parece buena), pero el **F1 de fraude es 0.000**.
- Es decir: el modelo no detectó **ni un solo fraude**, y aun así la exactitud "engaña".

🎓 **Cómo explicarlo:** "Con este ejemplo demuestro por qué no uso la exactitud como
métrica principal: un modelo inútil logra 85% de exactitud pero no detecta ningún fraude."

---

## Celda 6 — Matriz de confusión

```python
cm = confusion_matrix(y_val, pred, labels=clases)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ...)
plt.savefig(RESULTADOS / '00_matriz_baseline_tonto.png', dpi=120)
```
- `confusion_matrix(...)` → las 4 casillas (aciertos y errores por clase).
- `sns.heatmap(..., annot=True, fmt='d')` → dibuja la matriz con los números dentro.
- `plt.savefig(...)` → guarda la figura para el Capítulo IV.

---

## Qué demuestra este notebook

1. La exactitud engaña con clases desbalanceadas.
2. El **F1 de la clase minoritaria (fraude)** es lo que importa.
3. El **falso negativo** (fraude no detectado) es el error caro.
4. Todas las métricas salen de las 4 casillas de la matriz de confusión.
