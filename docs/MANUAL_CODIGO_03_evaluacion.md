# Manual de código — `03_evaluacion.ipynb` (Fase 4), línea por línea

Este notebook es la **evaluación final**: aquí se abre el conjunto de **test** por primera
y única vez, se comparan el modelo profundo y el baseline, y se decide la **hipótesis** con
la prueba de McNemar. Todo lo que sale de aquí es el **Capítulo IV** de la tesis.

---

## Conceptos base

- **Test:** la partición que se reserva para el final. Se abre **una sola vez**.
- **McNemar:** prueba estadística que compara dos modelos sobre las **mismas** observaciones.
  Da un **valor p**; si p < 0.05, la diferencia entre modelos es significativa (no es azar).
- **AUC-ROC:** mide la capacidad de separar clases en todos los umbrales (1.0 = perfecto).
- **Criterio del PDF:** el modelo profundo debe alcanzar **F1 ≥ 0.90**.

---

## Celda 1 — Configuración

```python
from statsmodels.stats.contingency_tables import mcnemar
SEED = 42
rng = np.random.default_rng(SEED)
CLASES = ['legitimo', 'fraudulento']
F1_MINIMO = 0.90
```
- Importa la prueba de McNemar de `statsmodels`.
- `rng = np.random.default_rng(SEED)` → generador de azar reproducible (para el DEMO).
- `F1_MINIMO = 0.90` → el criterio técnico de aceptación.

---

## Celda 2 — Función de matriz de confusión

```python
def matriz(y, pred, titulo, archivo=None):
    cm = confusion_matrix(y, pred, labels=CLASES)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ...)
    if archivo:
        plt.savefig(RESULTADOS / archivo, dpi=120)
```
- Dibuja la matriz de confusión y, si se le da nombre de archivo, la guarda en `resultados/`.

---

## Celda 2 (cont.) — La prueba de McNemar

```python
def prueba_mcnemar(y, pred_a, pred_b):
    a_ok = pred_a == y
    b_ok = pred_b == y
    tabla = [[int(np.sum(a_ok & b_ok)),  int(np.sum(a_ok & ~b_ok))],
             [int(np.sum(~a_ok & b_ok)), int(np.sum(~a_ok & ~b_ok))]]
    res = mcnemar(tabla, exact=False, correction=True)
    return tabla, res.pvalue
```
- `a_ok = pred_a == y` → arreglo de True/False: ¿acertó el modelo A en cada caso?
- La **tabla de contingencia** tiene 4 casillas:
  - `[ambos aciertan, solo A acierta]`
  - `[solo B acierta, ambos fallan]`
- `mcnemar(tabla, ...)` → aplica la prueba y devuelve el **valor p**.
- McNemar solo mira los casos donde los modelos **discrepan** (las casillas cruzadas).

🎓 **Cómo explicarlo:** "McNemar compara los dos modelos sobre los mismos mensajes. Se fija
en dónde uno acierta y el otro falla. Si esa diferencia es sistemática, el valor p es bajo
y la mejora es significativa."

---

## Celda 3 — Función maestra de comparación

```python
def comparar(y, pred_prof, pred_base, score_prof=None, score_base=None, nombre='motor'):
```
Recibe: etiquetas reales, predicciones del profundo y del baseline, y (opcional) sus puntajes.

```python
    for etiqueta, pred in [('MODELO PROFUNDO', pred_prof), ('LÍNEA BASE', pred_base)]:
        print(classification_report(y, pred, digits=3, zero_division=0))
```
- Imprime el reporte completo (precisión, recall, F1) de cada modelo.

```python
    f1_prof = f1_score(y, pred_prof, pos_label='fraudulento', zero_division=0)
    f1_base = f1_score(y, pred_base, pos_label='fraudulento', zero_division=0)
```
- Calcula el F1 de la clase fraudulento para cada modelo.

```python
    y_bin = (y == 'fraudulento').astype(int)
    if score_prof is not None:
        print(roc_auc_score(y_bin, score_prof))
```
- Para el AUC-ROC se necesita el **puntaje de probabilidad** (no la etiqueta).
- `y_bin` → convierte las etiquetas a 0/1 (fraudulento = 1).

```python
    tabla, p = prueba_mcnemar(y, pred_prof, pred_base)
    ... 'SIGNIFICATIVA' if p < 0.05 else 'NO significativa'
    ... 'CUMPLE' if f1_prof >= F1_MINIMO else 'NO cumple'
    gana = f1_prof > f1_base and p < 0.05
```
- Corre McNemar, evalúa el criterio F1 ≥ 0.90 y emite el **veredicto**:
  el profundo "gana" si tiene mejor F1 **y** la diferencia es significativa.

🎓 **Cómo explicarlo:** "No me basta con que el F1 sea mayor; exijo que McNemar confirme
que la diferencia es significativa. Eso es lo que valida mi hipótesis."

---

## Celda 4 — Generador de DEMO

```python
def demo(nombre, n, acc_prof, acc_base, nit_prof, nit_base):\n    y_bin = rng.choice([0, 1], size=n, p=[0.7, 0.3])
    ...
    def preds(acc):
        flip = rng.random(n) > acc
        return ... np.where(flip, 1 - y_bin, y_bin)
```
- Genera un test sintético para **probar el flujo** sin datos reales.
- `preds(acc)` → produce predicciones con una exactitud dada (voltea etiquetas al azar según `acc`).
- El modelo "profundo" se genera con mayor exactitud que el "baseline".

> Con datos reales, esta celda se reemplaza: cargas los modelos guardados y predices sobre test.

---

## Celdas 5 y 6 — Aplicar a cada motor

```python
y_url, pred_cnn, pred_url_base, sc_cnn, sc_url_base = demo('url', n=400, acc_prof=0.93, acc_base=0.85, ...)
res_url = comparar(y_url, pred_cnn, pred_url_base, sc_cnn, sc_url_base, nombre='url')
```
- Motor de URL: compara la CNN contra el baseline.

```python
y_txt, pred_beto, pred_txt_base, ... = demo('texto', n=300, acc_prof=0.92, acc_base=0.83, ...)
res_txt = comparar(y_txt, pred_beto, pred_txt_base, ..., nombre='texto')
```
- Motor de texto: compara BETO contra el baseline en español.

### Cómo cargar predicciones REALES (en lugar del demo)

```python
import joblib
logreg = joblib.load(MODELOS / 'url_logreg.joblib')
test = pd.read_csv(PARTICIONES / 'url_test.csv')
pred_base = logreg.predict(test['url'])
score_base = logreg.predict_proba(test['url'])[:, list(logreg.classes_).index('fraudulento')]
```
- Cargas el modelo, lees el test, predices **una sola vez** y pasas todo a `comparar(...)`.
- Para la CNN y BETO se hace igual pero cargando con torch/transformers (en Colab).

---

## Celda 7 — Revisión de errores

```python
errores = pd.DataFrame({'y_real': y_txt, 'pred_beto': pred_beto})
errores = errores[errores['y_real'] != errores['pred_beto']].head(20)
```
- Filtra los casos donde el modelo se equivocó y muestra 20.
- `y_real != pred` → selecciona solo los errores.
- Leer estos 20 errores a mano es el **material de la discusión de resultados** (Capítulo IV).

🎓 **Cómo explicarlo:** "Reviso 20 errores del modelo para entender qué tipo de mensajes lo
confunden; eso alimenta la discusión de resultados de la tesis."

---

## Resumen del veredicto

Para cada motor obtienes: reporte completo, F1, AUC-ROC, matriz de confusión, valor p de
McNemar y el chequeo F1 ≥ 0.90. La combinación **(mejor F1 + p < 0.05)** es lo que respalda
la hipótesis de que el aprendizaje profundo supera al enfoque clásico.
