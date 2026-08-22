# Manual de código — `01b_url_cnn.ipynb` (CNN de caracteres), línea por línea

Este notebook entrena el **modelo profundo** del motor de enlaces: una red neuronal
convolucional (CNN) sobre la secuencia de caracteres de la URL. Corre en Colab con GPU.

---

## Conceptos base

- **CNN (red convolucional):** red que aprende **patrones locales**. En imágenes detecta
  bordes; aquí detecta **subcadenas sospechosas** en la URL (ej. `-login-`, `.xyz`).
- **Nivel de carácter:** en vez de partir por palabras, tratamos la URL como una secuencia
  de letras/símbolos. La red aprende sola qué combinaciones son sospechosas.
- **Embedding:** convierte cada carácter en un vector de números que la red puede procesar.

---

## Celda 1 — GPU y dispositivo

```python
import torch
print('GPU disponible:', torch.cuda.is_available())
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
```
- `torch.cuda.is_available()` → ¿hay GPU?
- `DEVICE` → dónde correrán los cálculos: `'cuda'` (GPU) o `'cpu'`. Todo se mandará a este dispositivo.

---

## Celda 2 — Configuración y carga

```python
SEED = 42
MAX_FILAS = 80_000     # con GPU puedes subirlo o poner None
MAX_LEN = 200          # longitud fija de la URL en caracteres
np.random.seed(SEED); torch.manual_seed(SEED)
```
- `MAX_LEN = 200` → todas las URLs se recortan/rellenan a 200 caracteres (la red necesita
  entradas del mismo tamaño).

```python
def a_binario(v):
    s = str(v).strip().lower()
    return 'legitimo' if s in ('benign', ...) else 'fraudulento'
```
- Igual que en el baseline: convierte las etiquetas a binario.
- El resto de la celda carga `malicious_phish.csv` (o un DEMO) y quita duplicados.

---

## Celda 3 — Muestra y particiones

```python
if MAX_FILAS and len(df) > MAX_FILAS:
    df, _ = train_test_split(df, train_size=MAX_FILAS, stratify=df['etiqueta'], random_state=SEED)
train, resto = train_test_split(df, test_size=0.30, stratify=df['etiqueta'], random_state=SEED)
val, test = train_test_split(resto, test_size=0.50, stratify=resto['etiqueta'], random_state=SEED)
```
- Muestra estratificada + corte 70/15/15 (igual patrón que en todos los notebooks).

---

## Celda 4 — Codificación a nivel de carácter

```python
chars = sorted({c for u in train['url'] for c in u})
char2idx = {c: i + 1 for i, c in enumerate(chars)}
VOCAB = len(char2idx) + 1
```
- `chars` → el conjunto de todos los caracteres distintos que aparecen en el train.
- `char2idx` → asigna un número a cada carácter (empezando en 1; el 0 se reserva para relleno).
- `VOCAB` → tamaño del vocabulario (cuántos caracteres distintos + 1).

```python
def codificar(url):
    v = [char2idx.get(c, 0) for c in str(url)[:MAX_LEN]]
    return v + [0] * (MAX_LEN - len(v))
```
- Convierte una URL en una lista de números (uno por carácter).
- `char2idx.get(c, 0)` → si el carácter no está en el vocabulario, usa 0.
- `[:MAX_LEN]` → recorta a 200.
- `+ [0] * (...)` → rellena con ceros hasta llegar a 200 (padding).

```python
def a_tensores(part):
    X = torch.tensor([codificar(u) for u in part['url']], dtype=torch.long)
    y = torch.tensor([lab2id[e] for e in part['etiqueta']], dtype=torch.long)
    return X, y
```
- Convierte una partición en **tensores** de PyTorch: `X` (las URLs codificadas) e `y` (las etiquetas 0/1).

🎓 **Cómo explicarlo:** "Traduzco cada URL a una secuencia de 200 números, uno por carácter.
La red aprende sola qué combinaciones de caracteres indican phishing."

---

## Celda 5 — La arquitectura de la red

```python
class CharCNN(nn.Module):
    def __init__(self, vocab, emb_dim=32, n_clases=2):
        super().__init__()
        self.emb = nn.Embedding(vocab, emb_dim, padding_idx=0)
        self.conv1 = nn.Conv1d(emb_dim, 128, kernel_size=7, padding=3)
        self.conv2 = nn.Conv1d(128, 128, kernel_size=5, padding=2)
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.clasificador = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, n_clases))
```
- `nn.Embedding(vocab, 32)` → convierte cada carácter (número) en un vector de 32 valores.
- `nn.Conv1d(..., kernel_size=7)` → primera capa convolucional: mira ventanas de 7 caracteres.
- `nn.Conv1d(..., kernel_size=5)` → segunda capa: ventanas de 5 sobre lo anterior.
- `nn.AdaptiveMaxPool1d(1)` → resume cada patrón quedándose con su valor máximo.
- `nn.Linear(128, 64)` → capa densa que combina la información.
- `nn.ReLU()` → función de activación (introduce no linealidad).
- `nn.Dropout(0.3)` → apaga al azar el 30% de las neuronas en entrenamiento → **evita el sobreajuste**.
- `nn.Linear(64, n_clases)` → capa final: 2 salidas (legítimo/fraudulento).

```python
    def forward(self, x):
        x = self.emb(x).transpose(1, 2)      # (B, emb, L)
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.pool(x).squeeze(-1)         # (B, 128)
        return self.clasificador(x)
```
- `forward` → cómo fluyen los datos por la red (paso adelante).
- `.transpose(1, 2)` → reordena las dimensiones para que Conv1d las acepte.
- `.squeeze(-1)` → quita la dimensión sobrante tras el pooling.
- Devuelve los `logits` (puntajes por clase).

🎓 **Cómo explicarlo:** "Las capas convolucionales detectan patrones de caracteres; el
dropout evita que la red memorice el train; la capa final decide entre dos clases."

---

## Celda 6 — Entrenamiento

```python
EPOCAS = 5
BATCH = 256
cnt = Counter(train['etiqueta']); total = sum(cnt.values())
pesos = torch.tensor([total / (2 * cnt[l]) for l in ['legitimo','fraudulento']], ...).to(DEVICE)
criterio = nn.CrossEntropyLoss(weight=pesos)
optim = torch.optim.Adam(modelo.parameters(), lr=1e-3)
cargador = DataLoader(TensorDataset(X_tr, y_tr), batch_size=BATCH, shuffle=True)
```
- `EPOCAS = 5` → 5 pasadas completas al train.
- `BATCH = 256` → procesa 256 URLs a la vez.
- `pesos` → más peso a la clase minoritaria (desbalance).
- `CrossEntropyLoss(weight=pesos)` → la función de error, ponderada.
- `Adam(..., lr=1e-3)` → el optimizador que ajusta los pesos de la red.
- `DataLoader(..., shuffle=True)` → entrega los datos en lotes barajados.

```python
for ep in range(1, EPOCAS + 1):
    modelo.train(); perdida_tot = 0.0
    for xb, yb in cargador:
        xb, yb = xb.to(DEVICE), yb.to(DEVICE)
        optim.zero_grad()
        loss = criterio(modelo(xb), yb)
        loss.backward(); optim.step()
        perdida_tot += loss.item() * len(xb)
    print(f'época {ep}/{EPOCAS}  pérdida media = {perdida_tot/len(X_tr):.4f}')
```
- El bucle de entrenamiento, paso a paso:
  - `modelo.train()` → pone la red en modo entrenamiento (activa el dropout).
  - `xb.to(DEVICE)` → manda el lote a la GPU.
  - `optim.zero_grad()` → borra los gradientes anteriores.
  - `criterio(modelo(xb), yb)` → predice y calcula el error.
  - `loss.backward()` → calcula los gradientes (cómo ajustar cada peso).
  - `optim.step()` → actualiza los pesos.
- La pérdida media debe **bajar** época a época.

🎓 **Cómo explicarlo:** "En cada lote: predigo, mido el error, calculo gradientes y ajusto
los pesos. Repito 5 épocas; si la pérdida baja, la red está aprendiendo."

---

## Celda 7 — Evaluación

```python
modelo.eval()
with torch.no_grad():
    logits = modelo(X_val.to(DEVICE)).cpu()
pred_idx = logits.argmax(1).numpy()
pred = [id2lab[i] for i in pred_idx]
f1 = f1_score(y_val_lab, pred, pos_label='fraudulento', zero_division=0)
```
- `modelo.eval()` → modo evaluación (apaga el dropout).
- `with torch.no_grad()` → no calcula gradientes (más rápido, no vamos a entrenar).
- `logits.argmax(1)` → elige la clase de mayor puntaje.
- Calcula el F1 de la clase fraudulento sobre validación.

---

## Celda 8-9 — Matriz de confusión y guardado

```python
torch.save(modelo.state_dict(), 'url_cnn.pt')
with open('url_cnn_vocab.json', 'w', ...) as f:
    json.dump({'char2idx': char2idx, 'max_len': MAX_LEN}, f)
```
- `torch.save(modelo.state_dict(), ...)` → guarda los pesos de la red.
- Guarda también el vocabulario de caracteres (`char2idx`) → **necesario** para codificar
  nuevas URLs igual que en el entrenamiento.
- Guarda las predicciones de validación para la Fase 4.

🎓 **Cómo explicarlo:** "Guardo los pesos y el vocabulario; sin el vocabulario no podría
codificar una URL nueva de la misma forma en el prototipo."

---

## Comparación con el baseline

- Compara el **F1 de la CNN** con el del baseline (`01_url.ipynb`).
- El veredicto formal (¿la CNN le gana?) se decide con **McNemar sobre el test** en la Fase 4.
