# Manual de código — scripts del proyecto, línea por línea

Estas dos herramientas son de la **Fase 1 (el corpus)**: una limpia los datos personales
de los mensajes (obligación ética) y la otra mide el acuerdo entre etiquetadores.

---

# Parte A — `anonimizar.py`

## Concepto base

- **Anonimizar** = quitar datos personales (nombres, teléfonos, cuentas, montos) **antes**
  de guardar el mensaje.
- Se reemplazan por etiquetas (`[TELEFONO]`, `[MONTO]`, ...) para **conservar el patrón del
  fraude** sin exponer datos reales.
- Se hace con **expresiones regulares (regex)**: patrones que describen texto a buscar.

## Los patrones (regex)

```python
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
```
- Detecta correos: `algo@dominio.com`. `re.compile(...)` prepara el patrón para usarlo.

```python
_MONTO = re.compile(
    r"(?:(?:bs\.?|\$us|\$|usd|bolivianos?)\s*\.?\s*\d[\d.,]*)"
    r"|(?:\d[\d.,]*\s*(?:bs\.?|bolivianos?|\$us|usd))",
    re.IGNORECASE)
```
- Detecta montos: `Bs. 1.500`, `$us 200`, `50 bolivianos`.
- `re.IGNORECASE` → no distingue mayúsculas/minúsculas.
- `\d` → un dígito; `[\d.,]*` → más dígitos, puntos o comas.

```python
_TEL_INTL = re.compile(r"\+?591[\s\-]?\d{4}[\s\-]?\d{4}")
_TEL_MOVIL = re.compile(r"\b[67]\d{7}\b")
```
- `_TEL_INTL` → teléfonos con código de país: `+591 7012 3456`.
- `_TEL_MOVIL` → celulares bolivianos: 8 dígitos que empiezan en 6 o 7. `\b` = borde de palabra.

```python
_NUM_LARGO = re.compile(r"\b\d{7,}\b")
```
- Detecta números largos (7 o más dígitos): cuentas y cédulas.

🎓 **Cómo explicarlo:** "El orden importa: primero detecto montos y teléfonos, y al final
los números largos restantes, para no confundir un monto con una cuenta."

## La función principal

```python
def anonimizar(texto, usar_ner=False):
    if texto is None:
        return ""
    t = str(texto)
    t = _EMAIL.sub("[EMAIL]", t)
    t = _MONTO.sub("[MONTO]", t)
    t = _TEL_INTL.sub("[TELEFONO]", t)
    t = _TEL_MOVIL.sub("[TELEFONO]", t)
    t = _NUM_LARGO.sub("[NUMERO]", t)
```
- `.sub("[EMAIL]", t)` → reemplaza cada coincidencia por la etiqueta.
- Se aplican **en orden** (email → monto → teléfono → número largo).

```python
    if usar_ner:
        t = _quitar_nombres_ner(t)
    return re.sub(r"\s{2,}", " ", t).strip()
```
- Si se pide, además quita nombres con inteligencia artificial (spaCy).
- `re.sub(r"\s{2,}", " ", t)` → colapsa espacios dobles en uno solo. `.strip()` → quita espacios al inicio/fin.

## Nombres de persona (opcional, con spaCy)

```python
def _quitar_nombres_ner(texto):
    ...
    import spacy
    _NLP = spacy.load("es_core_news_sm")
    ...
    for ent in sorted(doc.ents, key=lambda e: -e.start_char):
        if ent.label_ == "PER":
            resultado = resultado[:ent.start_char] + "[NOMBRE]" + resultado[ent.end_char:]
```
- Usa un modelo de spaCy en español para detectar **entidades de tipo persona (PER)**.
- Las reemplaza por `[NOMBRE]`, de atrás hacia adelante (para no desordenar las posiciones).
- Si spaCy no está instalado, avisa y sigue sin fallar.

> ⚠️ Las regex generales **no** detectan nombres; por eso los nombres necesitan spaCy o **revisión manual**
> (tal como dice el PDF: "regex + revisión manual").

**Actualización 2026-11-17 — nombres sin spaCy.** Al revisar el corpus aparecieron 10 nombres
de persona reales (p. ej. "yapeo de *Nombre Apellido*"). Se agregaron dos reglas que **siempre** se aplican:

- `_NOMBRE`: una o dos palabras con mayúscula seguidas de un **apellido frecuente en Bolivia**
  (Mamani, Quispe, Condori, Choque, Flores, Vargas, …) → `[NOMBRE]`.
  Ej.: *"yapeo de Juan Carlos Mamani Quispe"* → *"yapeo de [NOMBRE]"*.
- `_SALUDO_NOMBRE`: un nombre suelto justo después de "Hola" → *"Hola [NOMBRE],"*.

Se quitó "Cruz" de la lista para no borrar "Santa Cruz". Después de anonimizar, `armar_corpus.py`
deja 0 nombres en las particiones (verificado). Cómo explicarlo: *"la anonimización combina
expresiones regulares, una lista de apellidos frecuentes y revisión manual"*.

## Procesar un CSV completo

```python
def anonimizar_csv(entrada, salida, columna="texto", usar_ner=False):
    with open(entrada, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for fila in filas:
        fila[columna] = anonimizar(fila[columna], usar_ner=usar_ner)
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)
```
- Lee un CSV, anonimiza la columna `texto` de cada fila y escribe el resultado.

## Cómo se usa

```bash
python scripts/anonimizar.py                              # corre las pruebas
python scripts/anonimizar.py data/crudo/x.csv data/anonimizado/corpus.csv   # procesa un CSV
```

---

# Parte B — `kappa.py`

## Concepto base

- **Kappa de Cohen** mide cuánto **coinciden dos etiquetadores** más allá del azar.
- Si dos personas etiquetan igual por casualidad, el kappa lo descuenta.
- El PDF: por debajo de **0.60** hay que revisar el manual de etiquetado; el valor se **reporta**.

## Interpretación

```python
def interpretar(k):
    if k < 0.20: return "leve"
    if k < 0.40: return "aceptable bajo"
    if k < 0.60: return "moderado (REVISAR el manual, umbral del PDF)"
    if k < 0.80: return "sustancial (bien)"
    return "casi perfecto (excelente)"
```
- Traduce el número a una escala de referencia (Landis & Koch) para que sea entendible.

## El cálculo

```python
from sklearn.metrics import cohen_kappa_score
def kappa(etiq_a, etiq_b):
    if len(etiq_a) != len(etiq_b):
        raise ValueError(...)
    return cohen_kappa_score(etiq_a, etiq_b)
```
- `cohen_kappa_score(a, b)` → calcula el kappa entre las dos listas de etiquetas.
- Antes valida que ambas listas tengan el mismo largo.

```python
def kappa_desde_csv(ruta, col_a, col_b):
    ...
    a = [fila[col_a] for fila in filas]
    b = [fila[col_b] for fila in filas]
    return kappa(a, b), len(filas)
```
- Lee un CSV con dos columnas de etiquetas (una por etiquetador) y calcula el kappa.

## Cómo se usa

```bash
python scripts/kappa.py                                  # corre una prueba
python scripts/kappa.py etiquetados.csv etiqueta_a etiqueta_b   # calcula el kappa real
```

🎓 **Cómo explicarlo:** "Dos personas etiquetan el mismo lote por separado; el kappa mide
su acuerdo. Si es bajo, significa que mis criterios de etiquetado no son claros y debo
mejorar el manual antes de continuar."

---

# Parte C — `ocr.py`

## Concepto base

- **OCR** (Reconocimiento Óptico de Caracteres) = sacar el **texto** de una **imagen**.
- Sirve para las capturas de estafas que recopilas de la web/WhatsApp: el modelo aprende
  de texto, no de fotos, así que primero hay que extraer el texto.
- Usa **Tesseract** (el motor de OCR) a través de `pytesseract` (el puente de Python).

## Localizar Tesseract

```python
_RUTAS_TESSERACT = [r"C:\Program Files\Tesseract-OCR\tesseract.exe", ...]
for _r in _RUTAS_TESSERACT:
    if Path(_r).exists():
        pytesseract.pytesseract.tesseract_cmd = _r
        break
```
- Busca el programa Tesseract en las rutas típicas de Windows y se lo indica a `pytesseract`.

## Leer una imagen

```python
def leer_imagen(ruta, idioma="spa"):
    img = cv2.imread(str(ruta))
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    texto = pytesseract.image_to_string(gris, lang=idioma)
    return " ".join(texto.split())
```
- `cv2.imread(...)` → abre la imagen.
- `cv2.cvtColor(..., COLOR_BGR2GRAY)` → la pasa a **escala de grises** (mejora la lectura).
- `pytesseract.image_to_string(gris, lang="spa")` → extrae el texto **en español**.
- `" ".join(texto.split())` → junta todo en una línea limpia (sin saltos ni espacios dobles).

## Procesar una carpeta

```python
def procesar_carpeta(carpeta, salida, idioma="spa"):
    imagenes = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in EXTENSIONES)
    for img in imagenes:
        texto = leer_imagen(img, idioma)
        filas.append({"archivo": img.name, "texto": texto})
    # ... escribe un CSV con columnas (archivo, texto)
```
- Recorre todas las imágenes de una carpeta, les saca el texto y arma un CSV.
- Ese CSV es la entrada para `anonimizar.py`.

## Cómo se usa

```bash
python scripts/ocr.py captura.jpg                            # una imagen -> imprime el texto
python scripts/ocr.py carpeta/ data/crudo/ocr.csv           # carpeta -> CSV
```

🎓 **Cómo explicarlo:** "Las capturas se convierten a texto con OCR antes de entrar al
corpus. Uso Tesseract con el idioma español y paso la imagen a escala de grises para
mejorar la precisión de la lectura."

---

# Parte D — Scripts del corpus de texto y su evaluación (2026-11-17)

Estos cinco scripts forman la **cadena completa** del motor de texto, desde tu Excel hasta el
número final de la tesis. Se corren **en este orden**:

```
DOC/datos.xlsx ──► revisar_datos.py ──► corregir_datos.py ──► armar_corpus.py ──► (Colab 02_texto)
  (reales)          (diagnóstico)        (aplica arreglos)     (particiones)        entrenar + TEST
DOC/dataset_..tsv ─────────────────────────────────────────────┘
  (aumento)                       alternativa local: entrenar_beto_local.py ──► evaluar_test_texto.py
```

## D.1 `revisar_datos.py` — ¿qué sirve y qué no?

**Concepto:** antes de entrenar hay que saber cuántos mensajes son realmente distintos y cuáles
tienen problemas. No modifica nada; solo **diagnostica**.

- Anonimiza cada mensaje y agrupa los que quedan **iguales** → se queda con el primero.
  - `repetido_exacto`: la misma fila copiada.
  - `variante_solo_monto_o_numero`: mismo mensaje con otro monto/teléfono/nombre.
- Calcula **familias**: mensajes casi iguales (similitud coseno TF-IDF ≥ 0.80, componentes conexas).
- **Alertas** para revisar a mano:
  - *fraude sin gancho*: etiquetado `fraudulento` pero no pide nada (regla del gancho).
  - *fecha futura*: la fecha de recolección no puede ser posterior a hoy.
  - *el mismo mensaje con las dos etiquetas*: contradicción.
- Revisa también los mensajes de aumento: repetidos y demasiado parecidos a un real (≥ 0.70).

**Salida:** `DOC/datos_revisados.xlsx` (hojas: resumen, reales_utiles, reales_revisar,
reales_descartados, aumento_utiles, aumento_descartados). Uso: `python scripts/revisar_datos.py`

## D.2 `corregir_datos.py` — aplicar los arreglos (con respaldo)

**Concepto:** las decisiones de etiquetado quedan **escritas en código**, no hechas a mano en Excel.
Así son auditables (el tribunal puede ver qué se cambió y por qué).

- Guarda primero `DOC/datos_respaldo_2026-11-17.xlsx`.
- `A_LEGITIMO`: 20 filas que solo informaban → `legitimo` (con su motivo).
- `DESCARTAR`: 4 ambiguas → se **mueven** a la hoja `descartados` (no se borran).
- Corrige 5 fechas futuras y unifica `empresa_courier` → `courier`.
- Usa `openpyxl` para **no romper el formato** del Excel. Requiere el Excel **cerrado**.

## D.3 `armar_corpus.py` — las particiones (sin fuga)

**Concepto clave — fuga de datos (*data leakage*):** si un mensaje de test tiene un "gemelo"
casi igual en train, el modelo acierta de memoria y la métrica se infla. Para evitarlo:

1. Anonimiza y quita duplicados **después** de anonimizar.
2. Agrupa en familias y reparte con `StratifiedGroupKFold`: **cada familia va entera a una sola
   partición**, manteniendo la proporción fraude/legítimo. Reparto 60/20/20.
3. Los mensajes de aumento van **solo a train**.
4. Verifica con `assert`: 0 textos repetidos y 0 familias partidas entre train/val/test.

**Salidas** (anonimizadas, se suben al repo): `corpus_train.csv` (reales + aumento),
`corpus_train_solo_real.csv`, `corpus_val.csv`, `corpus_test.csv`. Además `DOC/corpus_completo.xlsx`
(local) con todo junto y la partición de cada mensaje.

> Cómo explicarlo: *"la partición se hizo agrupando mensajes casi idénticos, para que el modelo
> se evalúe sobre mensajes realmente nuevos y no sobre variantes de lo que ya vio"*.

## D.4 `entrenar_beto_local.py` — BETO en la PC (sin GPU)

Igual que `02_texto` pero por consola. `python scripts/entrenar_beto_local.py [--aumento]`.
Cada experimento guarda sus archivos con sufijo (`_solo_real` / `_aumento`) para no pisarse.
En CPU tarda ~10 min con 267 mensajes y >1 h con 2267 → para el experimento con aumento conviene Colab.

## D.5 `evaluar_test_texto.py` — el examen final

Abre el **test una sola vez**: F1, precisión, recall, exactitud, AUC-ROC, matrices de confusión,
**McNemar exacta** y criterio F1 ≥ 0.90. Guarda las predicciones fila por fila (McNemar las necesita).
La sección 5 de `02_texto` hace exactamente lo mismo en Colab.
