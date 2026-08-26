# Justificación (¿por qué deep learning?) y metodología (CRISP-DM)

Material redactado para los capítulos de **marco teórico** y **metodología** de la tesis.

---

# Parte 1 — ¿Por qué deep learning y no machine learning clásico?

## Aclaración de fondo: no es "en vez de", es "contra"

El proyecto **usa los dos**. El machine learning clásico (Regresión Logística, Naive Bayes)
es la **línea base**: el rival contra el que se contrasta la hipótesis. El deep learning
(BETO, CNN) es la **propuesta**. El objetivo de la tesis es **demostrar**, con evidencia
estadística, que el deep learning **supera** al enfoque clásico. Sin el baseline no habría
con qué comparar, y sin comparación no habría aporte.

## Razones técnicas por las que el deep learning se ajusta a este problema

### 1. Entiende el contexto del lenguaje, no solo palabras sueltas
Los modelos clásicos con TF-IDF tratan el texto como una **bolsa de palabras**: cuentan
términos sin entender el orden ni el significado. Una estafa se puede **reformular
infinitamente** ("valide sus datos" / "confirme su información" / "actualice su cuenta")
y un modelo de palabras no capta que son lo mismo. **BETO (un transformer)** sí entiende
el **contexto** y las relaciones entre palabras, así que generaliza a mensajes reescritos.

### 2. Aprovecha el aprendizaje previo (transfer learning)
BETO ya aprendió español leyendo **millones de textos**. Con **ajuste fino** solo le enseñas
tu tarea (fraude/no fraude) sobre tu corpus. Esto permite trabajar con **cientos** de
mensajes en lugar de cientos de miles. Un modelo clásico parte de cero cada vez.

### 3. Aprende patrones que no defines a mano
En las URLs, la **CNN de caracteres** aprende sola las **subcadenas sospechosas**
(`-login-`, `.xyz`, dominios de imitación como `banc0sol`) sin que tú tengas que
programar reglas. Detecta los dominios de imitación (typosquatting) que un enfoque manual
se perdería.

### 4. Generaliza mejor a estafas nuevas
Como entiende el patrón y no solo las palabras exactas, el modelo profundo **responde mejor
a variantes y estafas nuevas** que no vio en el entrenamiento.

## Por qué, aun así, se conserva el machine learning clásico

- Es el **antecedente local**: los trabajos previos usaron Regresión Logística y Naive Bayes.
  Compararse contra ellos hace válida la hipótesis.
- Es **rápido e interpretable**, y sirve de piso de referencia.
- **Rigor científico:** si el modelo profundo no le gana de forma **significativa**
  (prueba de McNemar, p < 0.05), no hay aporte que defender. La comparación es honesta.

> **Frase para la defensa:** "No uso deep learning porque esté de moda, sino porque el
> lenguaje tiene contexto que los modelos clásicos no capturan. Y no lo afirmo: lo demuestro
> comparando contra el baseline clásico con la prueba de McNemar."

---

# Parte 2 — Metodología: CRISP-DM

## Qué es

**CRISP-DM** (Cross-Industry Standard Process for Data Mining) es la metodología estándar
para proyectos de minería de datos y aprendizaje automático. Organiza el trabajo en **6 fases**
y es **iterativa**: se puede volver a una fase anterior si hace falta.

## Por qué se eligió

- Es el **estándar** de la industria para proyectos de datos, ampliamente aceptado.
- Es **ordenada e iterativa**, ideal para un trabajo que empieza desde cero.
- Es **centrada en los datos**, y en este proyecto la mayor parte del esfuerzo está justamente
  en los datos (recolección, limpieza, etiquetado del corpus), no en el modelo.

## Las 6 fases y cómo se aplican en este proyecto

### Fase 1 — Comprensión del problema
Definir objetivos, alcance y delimitación: detectar mensajes de suplantación de identidad
(smishing, phishing, quishing) en el contexto boliviano. Aquí se fija qué **está** y qué **no
está** dentro del alcance (ej.: no se abordan ataques de red como el envenenamiento de DNS).

### Fase 2 — Comprensión de los datos
Explorar los datos disponibles: datasets públicos de URL y SMS, y el corpus propio. Analizar
su tamaño, balance de clases y calidad.

### Fase 3 — Preparación de los datos *(la fase más pesada)*
Recolectar el corpus boliviano (ficha + capturas), aplicar **OCR** a las imágenes,
**anonimizar**, **etiquetar** (con etiquetado doble y kappa de Cohen), quitar duplicados,
balancear y **partir** en train/validación/test. *La mayor parte del esfuerzo del proyecto
está aquí.*

### Fase 4 — Modelado
Construir los modelos: líneas base clásicas (Regresión Logística, Naive Bayes) y modelos
profundos (**BETO** para texto, **CNN** para URL). Ajustar hiperparámetros (épocas, tasa de
aprendizaje, ponderación de clases).

### Fase 5 — Evaluación
Medir sobre el **test**: exactitud, precisión, exhaustividad, **F1**, AUC-ROC y matriz de
confusión. Comparar el modelo profundo contra el baseline con la **prueba de McNemar**, y
comprobar el criterio técnico **F1 ≥ 0.90**.

### Fase 6 — Despliegue
Construir el **prototipo de alerta** (demostración con Gradio): un módulo de decisión que
combina los motores y emite **Seguro / Sospechoso / Peligroso**, con la ruta del QR
(decodificar a URL) integrada.

## Diagrama del flujo

```
[1] Comprensión    →  [2] Comprensión   →  [3] Preparación   →  [4] Modelado
    del problema         de los datos         de los datos          (baseline + DL)
                                                                          ↓
                          [6] Despliegue   ←   [5] Evaluación   ←────────┘
                              (prototipo)         (McNemar, F1)
        (las flechas pueden retroceder: CRISP-DM es iterativo)
```

> **Frase para la defensa:** "Uso CRISP-DM porque es el estándar para proyectos de datos y
> porque es iterativo y centrado en los datos, que es donde está el 80% del esfuerzo de mi
> trabajo: construir un corpus en español que no existía."
