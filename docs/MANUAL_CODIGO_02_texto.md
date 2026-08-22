# Manual de código — `02_texto.ipynb` (BETO), línea por línea

Explicación detallada de cada celda del notebook de BETO, pensada para que **entiendas
y puedas explicar** cada línea en la defensa. Al final de los bloques clave hay una nota
**"🎓 Cómo explicarlo"**.

---

## Conceptos base (léelos primero)

- **BETO** = un BERT ya entrenado en millones de textos en español. No lo entrenamos
  desde cero: le hacemos **ajuste fino (fine-tuning)** para nuestra tarea (fraude/no fraude).
- **Ajuste fino:** partir de un modelo que ya "sabe español" y solo enseñarle tu tarea.
  Es lo que permite trabajar con cientos de mensajes en vez de millones.
- **Tokenizer:** convierte el texto en números (tokens) que el modelo entiende.
- **Trainer:** la clase de Hugging Face que se encarga del bucle de entrenamiento.

---

## Celda 1 — Comprobar la GPU

```python
import torch
print('GPU disponible:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
```

- `import torch` → carga PyTorch, la librería de deep learning.
- `torch.cuda.is_available()` → devuelve `True` si hay GPU NVIDIA disponible (en Colab, tras activarla).
- `torch.cuda.get_device_name(0)` → nombre de la GPU (ej. "Tesla T4").

🎓 **Cómo explicarlo:** "Verifico que haya GPU porque afinar BETO en CPU sería inviable;
la GPU acelera las operaciones matriciales de la red."

---

## Celda 2 — Cargar el corpus (o DEMO)

```python
SEED = 42
np.random.seed(SEED); torch.manual_seed(SEED)
```
- `SEED = 42` → un número fijo para el azar.
- `np.random.seed` y `torch.manual_seed` → hacen que todo lo aleatorio (mezclas,
  inicialización) sea **reproducible**: si corres dos veces, obtienes lo mismo.

```python
candidatos = [ Path.cwd().parent/'data'/'anonimizado'/'corpus.csv', ... ]
ruta = next((p for p in candidatos if p.exists()), None)
```
- Arma una lista de rutas posibles del corpus (local o Colab).
- `next((p for p in candidatos if p.exists()), None)` → toma la **primera ruta que exista**;
  si ninguna existe, devuelve `None`.

```python
if ruta is not None:
    df = pd.read_csv(ruta)
    df = df[['texto', 'etiqueta']].dropna()
```
- `pd.read_csv(ruta)` → carga el CSV en una tabla (DataFrame).
- `df[['texto','etiqueta']]` → se queda solo con esas dos columnas.
- `.dropna()` → elimina filas con valores vacíos.

```python
if ruta is None or len(df) < 40:
    # ... genera un DEMO en español ...
```
- Si no hay corpus o tiene menos de 40 filas, crea datos de ejemplo para poder probar.
- `df.sample(frac=1, random_state=SEED)` → **baraja** todas las filas (frac=1 = el 100%).

🎓 **Cómo explicarlo:** "El notebook detecta automáticamente mi corpus; si aún no está,
usa un demo para validar que la tubería de código funciona."

---

## Celda 3 — Partición train/val/test

```python
train, resto = train_test_split(df, test_size=0.30, stratify=df['etiqueta'], random_state=SEED)
val, test = train_test_split(resto, test_size=0.50, stratify=resto['etiqueta'], random_state=SEED)
```
- Primer corte: 70% `train`, 30% `resto`.
- Segundo corte: el `resto` se parte a la mitad → 15% `val`, 15% `test`.
- `stratify=...` → mantiene la proporción de clases en cada parte.
- `random_state=SEED` → el corte es siempre idéntico.

🎓 **Cómo explicarlo:** "Divido en tres: entreno con train, ajusto con val y reservo test
para el final. Uso estratificación para que las tres partes tengan la misma proporción de fraude."

---

## Celda 4 — Línea base clásica en español (el rival)

```python
base = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), min_df=1),
    LogisticRegression(max_iter=1000, class_weight='balanced'),
)
base.fit(train['texto'], train['etiqueta'])
```
- `TfidfVectorizer(ngram_range=(1,2))` → convierte el texto en números contando palabras
  y pares de palabras (1-gramas y 2-gramas), pesados por TF-IDF (importancia relativa).
- `LogisticRegression(class_weight='balanced')` → modelo clásico; `balanced` compensa el
  desbalance dando más peso a la clase minoritaria.
- `make_pipeline(...)` → encadena vectorizador + modelo en un solo objeto.
- `.fit(...)` → entrena.

```python
f1_base = f1_score(val['etiqueta'], pred_base, pos_label='fraudulento', zero_division=0)
```
- Calcula el F1 sobre validación, tomando **'fraudulento' como la clase positiva**.

🎓 **Cómo explicarlo:** "Este es el modelo tradicional contra el que comparo BETO. Si mi
modelo profundo no le gana, no hay aporte. Es el mismo enfoque del antecedente local."

---

## Celda 5 — Tokenizer y preparación de datos para BETO

```python
CKPT = 'dccuchile/bert-base-spanish-wwm-cased'   # BETO
tok = AutoTokenizer.from_pretrained(CKPT)
```
- `CKPT` → el identificador del modelo BETO en Hugging Face.
- `AutoTokenizer.from_pretrained(CKPT)` → descarga el tokenizer de BETO (cómo parte el texto).

```python
class DatasetTexto(Dataset):
    def __init__(self, textos, etiquetas):
        self.enc = tok(list(textos), truncation=True, padding=True, max_length=128)
        self.labels = [lab2id[e] for e in etiquetas]
```
- Es una clase que empaqueta los datos como PyTorch los pide.
- `tok(...)` → convierte cada mensaje en tokens numéricos.
  - `truncation=True` → corta mensajes muy largos.
  - `padding=True` → rellena los cortos para que todos midan igual.
  - `max_length=128` → tope de 128 tokens (suficiente para SMS/WhatsApp).
- `lab2id[e]` → convierte 'legitimo'→0, 'fraudulento'→1 (el modelo trabaja con números).

```python
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, i):
        item = {k: torch.tensor(v[i]) for k, v in self.enc.items()}
        item['labels'] = torch.tensor(self.labels[i])
        return item
```
- `__len__` → cuántos ejemplos hay.
- `__getitem__` → cómo entregar el ejemplo `i` como tensores (los tensores son los "arreglos"
  que PyTorch procesa). Devuelve las entradas + la etiqueta.

🎓 **Cómo explicarlo:** "El tokenizer traduce el texto a números; el `Dataset` empaqueta
cada mensaje con su etiqueta en el formato que el entrenador de PyTorch espera."

---

## Celda 6 — Pesos por clase y entrenador ponderado

```python
cnt = Counter(train['etiqueta']); total = sum(cnt.values())
pesos = torch.tensor([total / (2 * cnt[l]) for l in ETIQUETAS], dtype=torch.float)
```
- `Counter(...)` → cuenta cuántos hay de cada clase.
- La fórmula `total / (2 * cnt[l])` → da **más peso a la clase con menos ejemplos**.
  Ejemplo: si hay muchos legítimos y pocos fraudes, el fraude pesa más en el error.

```python
class TrainerPonderado(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop('labels')
        outputs = model(**inputs)
        loss_fct = torch.nn.CrossEntropyLoss(weight=pesos.to(model.device))
        loss = loss_fct(outputs.logits, labels)
        return (loss, outputs) if return_outputs else loss
```
- Personaliza el `Trainer` para usar una **pérdida ponderada**.
- `inputs.pop('labels')` → separa las etiquetas reales.
- `model(**inputs)` → el modelo predice (produce `logits`, puntajes por clase).
- `CrossEntropyLoss(weight=pesos)` → la función de error, con los pesos por clase.
- `loss_fct(outputs.logits, labels)` → mide cuánto se equivocó el modelo.

🎓 **Cómo explicarlo:** "En vez de descartar ejemplos para balancear, pondero la función
de pérdida: penalizo más los errores en la clase fraudulento, que es la minoritaria y la
importante." (Esto es exactamente el Paso 3 del PDF.)

---

## Celda 7 — Función de métricas

```python
def metricas(pred):
    logits = pred.predictions[0] if isinstance(pred.predictions, tuple) else pred.predictions
    labels = pred.label_ids
    preds = np.argmax(logits, axis=1)
    p, r, f1, _ = precision_recall_fscore_support(labels, preds, labels=[0,1], average=None, zero_division=0)
    return {'accuracy': accuracy_score(labels, preds),
            'f1_fraudulento': f1[1], 'recall_fraudulento': r[1], 'precision_fraudulento': p[1]}
```
- `np.argmax(logits, axis=1)` → convierte los puntajes en la clase predicha (la de mayor puntaje).
- `precision_recall_fscore_support(...)` → calcula precisión, recall y F1 por clase.
- Devuelve un diccionario con las métricas; **`f1_fraudulento` (índice [1]) es la que nos importa.**

🎓 **Cómo explicarlo:** "Reporto el F1 de la clase fraudulento porque es el error caro;
la exactitud global no sirve con clases desbalanceadas."

---

## Celda 8 — Configurar y entrenar BETO

```python
modelo = AutoModelForSequenceClassification.from_pretrained(
    CKPT, num_labels=2, id2label=..., label2id=lab2id)
```
- Carga BETO y le añade una **cabeza de clasificación** con 2 salidas (legítimo/fraudulento).

```python
args = TrainingArguments(
    output_dir='../modelos/beto_ckpt',
    num_train_epochs=4,          # 4 pasadas completas al corpus
    learning_rate=2e-5,          # tasa de aprendizaje pequeña (típica en fine-tuning)
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    eval_strategy='epoch',       # evalúa al final de cada época
    save_strategy='epoch',       # guarda al final de cada época
    load_best_model_at_end=True, # se queda con el mejor modelo, no el último
    metric_for_best_model='f1_fraudulento',
    seed=SEED,
)
```
- `num_train_epochs=4` → recorre el corpus 4 veces (el PDF sugiere 3–4).
- `learning_rate=2e-5` → cuánto ajusta los pesos en cada paso; pequeño para no "romper"
  lo que BETO ya sabe.
- `batch_size` → cuántos ejemplos procesa a la vez.
- `load_best_model_at_end=True` + `metric_for_best_model='f1_fraudulento'` → conserva la
  época con mejor F1 de fraude, no necesariamente la última (evita quedarse con un modelo sobreajustado).

```python
trainer = TrainerPonderado(model=modelo, args=args,
                           train_dataset=ds_tr, eval_dataset=ds_val,
                           compute_metrics=metricas)
trainer.train()
```
- Crea el entrenador (con nuestra pérdida ponderada) y lo pone a entrenar.
- Durante `train()` verás la pérdida bajar y las métricas de validación por época.

🎓 **Cómo explicarlo:** "Uso 4 épocas y tasa 2e-5, valores estándar de fine-tuning.
Guardo el mejor modelo según el F1 de fraude para no quedarme con uno sobreajustado."

---

## Celda 9 — Evaluar y comparar

```python
res = trainer.evaluate()
f1_beto = res['eval_f1_fraudulento']
print('BETO gana al baseline' if f1_beto > f1_base else 'Revisar...')
```
- `trainer.evaluate()` → mide BETO sobre validación.
- Compara el F1 de BETO contra el del baseline clásico.

> Ojo: esta comparación es en **validación**. El veredicto formal (con McNemar sobre
> **test**) se hace en la Fase 4. Aquí solo verificamos que vamos bien.

---

## Celda 10 — Guardar modelo y predicciones

```python
trainer.save_model('../modelos/beto_final')
tok.save_pretrained('../modelos/beto_final')
```
- Guarda los pesos del modelo y el tokenizer para reusarlos después (Fase 4, prototipo).

```python
logits = trainer.predict(ds_val).predictions
pred_beto = [ETIQUETAS[i] for i in np.argmax(logits, axis=1)]
pd.DataFrame({...}).to_csv('../resultados/02_texto_val_pred.csv', index=False)
```
- Genera las predicciones sobre validación y las guarda en CSV.
- **Guardar las predicciones (no solo las métricas) es obligatorio:** la prueba de McNemar
  las necesita fila por fila.

🎓 **Cómo explicarlo:** "Guardo el modelo para el prototipo y las predicciones para McNemar;
si solo guardara el F1 tendría que volver a evaluar todo."

---

## Errores comunes y cómo resolverlos

| Síntoma | Causa | Solución |
|---|---|---|
| `GPU disponible: False` | No activaste la GPU en Colab | Entorno de ejecución → Cambiar tipo → GPU |
| Error en `eval_strategy` | Versión vieja de `transformers` | Cámbialo por `evaluation_strategy='epoch'` |
| F1 alto en train, bajo en val | **Sobreajuste** (corpus chico) | Menos épocas, más datos, o más regularización |
| Se pierde `beto_final` al cerrar Colab | Colab borra archivos | Copiar la carpeta a Google Drive |
| Muy lento | Está corriendo en CPU | Verifica que la GPU esté activa |
