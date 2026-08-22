# Manual de código — `01_url.ipynb` (baseline de URL), línea por línea

Este notebook entrena la **línea base clásica** del motor de enlaces: n-gramas de
caracteres + Regresión Logística y Naive Bayes. Es el rival contra el que se compara el
modelo profundo (la CNN de `01b_url_cnn.ipynb`). Corre en local, no necesita GPU.

---

## Concepto base

- Una **URL no tiene palabras**, tiene subcadenas sospechosas (ej. `secure-login-banco.xyz`).
- Por eso usamos **n-gramas de caracteres**: trozos de 3 a 5 caracteres seguidos.
- **Regresión Logística** y **Naive Bayes** son modelos de machine learning clásico (rápidos, sin GPU).

---

## Celda 1 — Configuración

```python
SEED = 42
MAX_FILAS = 60_000        # muestra para correr rápido en local
np.random.seed(SEED)
```
- `SEED` → reproducibilidad.
- `MAX_FILAS = 60_000` → como el dataset tiene ~651.000 URLs, tomamos una muestra de 60.000
  para que corra rápido en tu PC. En Colab puedes subirlo o poner `None` (todo).

```python
CRUDO = RAIZ / 'data' / 'crudo'
PARTICIONES = RAIZ / 'data' / 'particiones'
MODELOS = RAIZ / 'modelos'
RESULTADOS = RAIZ / 'resultados'
for d in (PARTICIONES, MODELOS, RESULTADOS):
    d.mkdir(exist_ok=True)
```
- Define las rutas y crea las carpetas si faltan.

---

## Celda 2 — Cargar el dataset (o DEMO)

```python
def detectar_columnas(df):
    col_url = next((c for c in df.columns if c.lower() in ('url','urls','link')), df.columns[0])
    col_lab = next((c for c in df.columns if c.lower() in ('type','label','result','class')), df.columns[-1])
    return col_url, col_lab
```
- Detecta automáticamente cuál columna es la URL y cuál la etiqueta (por si el CSV varía).

```python
def a_binario(v):
    s = str(v).strip().lower()
    return 'legitimo' if s in ('benign','legitimate','good','0','legitimo') else 'fraudulento'
```
- Convierte las 4 clases del dataset (`benign`, `phishing`, `malware`, `defacement`) a **binario**:
  `benign` → legítimo; el resto → fraudulento.

```python
archivo = CRUDO / 'malicious_phish.csv'
if not archivo.exists():
    otros = list(CRUDO.glob('*.csv'))
    archivo = otros[0] if otros else None
```
- Busca `malicious_phish.csv`; si no está, toma el primer CSV que haya en `data/crudo/`.
- Si no hay ninguno, más abajo genera un DEMO.

```python
df = df.dropna(subset=['url']).drop_duplicates(subset=['url']).reset_index(drop=True)
```
- `dropna(subset=['url'])` → quita filas sin URL.
- `drop_duplicates(subset=['url'])` → elimina URLs repetidas (evita que el modelo "haga trampa").
- `reset_index(drop=True)` → reordena los índices.

🎓 **Cómo explicarlo:** "Limpio duplicados porque una URL repetida en train y test inflaría
artificialmente las métricas."

---

## Celda 3 — Balance de clases

```python
print(df['etiqueta'].value_counts())
print(df['etiqueta'].value_counts(normalize=True).round(3))
```
- Muestra cuántas URLs hay de cada clase, en conteo y en proporción.

---

## Celda 4 — Muestra y particiones

```python
if MAX_FILAS and len(df) > MAX_FILAS:
    df, _ = train_test_split(df, train_size=MAX_FILAS, stratify=df['etiqueta'], random_state=SEED)
    df = df.reset_index(drop=True)
```
- Si el dataset es más grande que `MAX_FILAS`, toma una **muestra estratificada** (conserva
  la proporción de clases). El `_` descarta el resto.

```python
train, resto = train_test_split(df, test_size=0.30, stratify=df['etiqueta'], random_state=SEED)
val, test = train_test_split(resto, test_size=0.50, stratify=resto['etiqueta'], random_state=SEED)
for nombre, part in [('url_train', train), ('url_val', val), ('url_test', test)]:
    part.to_csv(PARTICIONES / f'{nombre}.csv', index=False)
```
- Corte 70/15/15 estratificado y con semilla fija.
- Guarda cada partición en `data/particiones/` (`url_train.csv`, etc.).

---

## Celda 5 — Entrenar los dos baselines

```python
def vectorizador():
    return TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2)
```
- `analyzer='char_wb'` → analiza **caracteres** dentro de los límites de cada "palabra".
- `ngram_range=(3, 5)` → trozos de 3, 4 y 5 caracteres.
- `min_df=2` → ignora trozos que aparecen en menos de 2 URLs (reduce ruido y memoria).

```python
logreg = make_pipeline(vectorizador(), LogisticRegression(max_iter=1000, class_weight='balanced'))
nb = make_pipeline(vectorizador(), MultinomialNB())
logreg.fit(X_tr, y_tr)
nb.fit(X_tr, y_tr)
```
- Arma dos tuberías: vectorizador + modelo.
- `class_weight='balanced'` (en LogReg) → compensa el desbalance.
- `MultinomialNB` → Naive Bayes, ideal para conteos/frecuencias de texto.
- `.fit(...)` → entrena ambos.

🎓 **Cómo explicarlo:** "Uso n-gramas de caracteres porque capturan patrones de subcadenas
sospechosas en la URL. Entreno dos algoritmos clásicos para comparar."

---

## Celda 6 — Evaluar en validación

```python
for nombre, modelo in [('Regresión Logística', logreg), ('Naive Bayes', nb)]:
    pred = modelo.predict(X_val)
    f1 = f1_score(y_val, pred, pos_label='fraudulento', zero_division=0)
    print(f'===== {nombre}  |  F1 (fraudulento) = {f1:.3f} =====')
    print(classification_report(y_val, pred, digits=3, zero_division=0))
```
- Recorre ambos modelos, predice sobre **validación** (no test) y muestra su F1 y reporte.

---

## Celda 7 — Matriz de confusión

```python
cm = confusion_matrix(y_val, logreg.predict(X_val), labels=clases)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ...)
plt.savefig(RESULTADOS / '01_url_matriz_logreg.png', dpi=120)
```
- Dibuja y guarda la matriz de confusión del mejor baseline (Regresión Logística).

---

## Celda 8 — Guardar modelos y predicciones

```python
import joblib
joblib.dump(logreg, MODELOS / 'url_logreg.joblib')
joblib.dump(nb, MODELOS / 'url_nb.joblib')
pd.DataFrame({...}).to_csv(RESULTADOS / '01_url_val_pred.csv', index=False)
```
- `joblib.dump(...)` → guarda cada modelo entrenado en disco.
- Guarda las predicciones de validación (se reusan en la Fase 4 para McNemar).

---

## Qué sigue

- El modelo profundo (CNN) está en `01b_url_cnn.ipynb` y se compara contra estos baselines.
- El **test** queda intacto hasta la Fase 4.
