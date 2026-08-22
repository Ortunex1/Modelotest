# Glosario de conceptos

Los conceptos que necesitas dominar para entender y **defender** tu tesis. Empieza por los
5 fundamentales (los del PDF) y sigue con el resto agrupado por tema.

---

# Parte 1 — Los 5 conceptos fundamentales

## 1. Las tres particiones (train / validation / test)

El corpus se corta en tres partes, cada una con un rol distinto:

- **Entrenamiento (train):** con esta parte el modelo **aprende**.
- **Validación (val):** con esta **decides** cuántas épocas correr, qué configuración usar,
  qué modelo es mejor. La miras muchas veces.
- **Prueba (test):** se abre **una sola vez, al final**. Es el número que reportas en la tesis.

> **Por qué importa:** si miras el test antes de tiempo para tomar decisiones, tus resultados
> dejan de ser honestos. El test tiene que ser "datos que el modelo nunca vio" para que la
> métrica sea creíble.

🎓 *Si te preguntan:* "Divido en tres para no hacer trampa: aprendo con train, ajusto con
validación y reservo el test para medir el rendimiento real una sola vez."

---

## 2. Etiqueta y predicción (label / prediction)

- **Etiqueta:** la respuesta correcta que **tú asignas** a cada mensaje: `legítimo` o `fraudulento`.
- **Predicción:** lo que el **modelo responde**.
- **Evaluar** es, literalmente, **comparar ambas columnas**: ¿cuántas veces la predicción
  coincidió con la etiqueta?

🎓 *Si te preguntan:* "La etiqueta es la verdad que yo defino; la predicción es lo que el
modelo cree. Toda la evaluación sale de comparar las dos."

---

## 3. La matriz de confusión (confusion matrix)

Una tabla de **4 casillas** que resume los aciertos y errores:

|  | Predijo legítimo | Predijo fraudulento |
|---|---|---|
| **Es legítimo** | Verdadero Negativo (VN) ✅ | Falso Positivo (FP) ❌ |
| **Es fraudulento** | **Falso Negativo (FN)** ❌ | Verdadero Positivo (VP) ✅ |

- **Falso Negativo (FN):** un mensaje fraudulento que el modelo **dejó pasar**. Es el **error caro**.
- **Falso Positivo (FP):** un mensaje legítimo marcado como fraude. Solo **asusta de más**.
- **Todas las métricas** (precisión, recall, F1) salen de estas 4 casillas.

🎓 *Si te preguntan:* "En mi problema el error caro es el falso negativo: una estafa que no
detecto. Por eso priorizo la exhaustividad sobre la clase fraudulento."

---

## 4. Sobreajuste (overfitting)

El modelo **memoriza** el conjunto de entrenamiento en vez de **aprender el patrón** general.

- **Señal clara:** acierto altísimo en entrenamiento pero mediocre en validación.
- **Cuándo pasa:** casi siempre con corpus pequeños (como el tuyo).
- **Cómo se combate:** con **dropout**, **detener el entrenamiento a tiempo** (pocas épocas),
  ponderar clases, o aumentar datos.

🎓 *Si te preguntan:* "El sobreajuste es cuando el modelo memoriza en vez de generalizar. Lo
detecto comparando train vs. validación, y lo controlo con dropout y pocas épocas."

---

## 5. Ajuste fino (fine-tuning)

En vez de entrenar una red **desde cero**, partes de un modelo que **ya aprendió español**
leyendo millones de textos (BETO) y solo le enseñas **tu tarea** (fraude/no fraude).

- Es lo que te permite trabajar con **cientos** de mensajes en lugar de **cientos de miles**.
- Es la razón técnica por la que tu corpus pequeño **alcanza**.

🎓 *Si te preguntan:* "No entreno BETO desde cero; hago ajuste fino. BETO ya sabe español, yo
solo le enseño a distinguir fraude. Por eso me alcanza un corpus pequeño."

---

# Parte 2 — Conceptos de los modelos

## Machine Learning clásico vs. Deep Learning

- **Machine Learning clásico** (Regresión Logística, Naive Bayes): modelos más simples y
  rápidos, no necesitan GPU. En tu tesis son la **línea base** (el rival).
- **Deep Learning** (CNN, BETO): redes neuronales que aprenden patrones complejos. Son tu
  **aporte**. La hipótesis es que **superan** al clásico.

## Regresión Logística
Modelo clásico que estima la **probabilidad** de que algo pertenezca a una clase. Simple,
interpretable, rápido.

## Naive Bayes
Modelo clásico basado en probabilidades (teorema de Bayes). "Naive" (ingenuo) porque asume
que las características son independientes. Muy usado en clasificación de texto/spam.

## TF-IDF
Forma de convertir texto en números. Mide la **importancia** de una palabra en un documento
respecto a todo el conjunto. Palabras muy comunes pesan menos; las distintivas, más.

## N-gramas de caracteres
Trozos de N caracteres seguidos. Ejemplo, `banco` en 3-gramas: `ban`, `anc`, `nco`. En URLs
se usan porque **una URL no tiene palabras**, tiene subcadenas sospechosas.

## CNN (red neuronal convolucional)
Red que detecta **patrones locales**. En imágenes detecta bordes; en tu CNN de URL detecta
combinaciones de caracteres típicas de phishing (`-login-`, `.xyz`).

## BERT / BETO
- **BERT:** un modelo de lenguaje profundo (transformer) que entiende contexto.
- **BETO:** un BERT entrenado específicamente en **español**. Es la base de tu motor de texto.

## Transformer
La arquitectura detrás de BERT/BETO. Su clave es el mecanismo de **atención**, que le permite
entender qué palabras de una frase se relacionan entre sí.

## Tokenizer
Convierte el texto en **tokens** (números) que el modelo entiende. Cada modelo tiene el suyo.

## Embedding
Representación de una palabra o carácter como un **vector de números**. Palabras parecidas
tienen vectores parecidos.

---

# Parte 3 — Conceptos de entrenamiento

## Época (epoch)
Una **pasada completa** por todo el conjunto de entrenamiento. Entrenas varias épocas (3–4 en BETO).

## Tasa de aprendizaje (learning rate)
Cuánto ajusta el modelo sus pesos en cada paso. En fine-tuning es **pequeña** (~`2e-5`) para
no "romper" lo que BETO ya sabe.

## Dropout
Apaga al azar un porcentaje de neuronas durante el entrenamiento. Evita el **sobreajuste**.

## Pesos por clase (class weights)
Cuando hay muchos más ejemplos de una clase que de otra (desbalance), se da **más peso** al
error sobre la clase minoritaria (fraude), en vez de descartar ejemplos.

## Semilla aleatoria (seed)
Un número fijo que hace **reproducible** todo lo aleatorio. Sin ella no podrías repetir tus
propios resultados cuando el tribunal pregunte.

## Estratificación (stratify)
Al partir los datos, mantiene la **misma proporción de clases** en cada parte. Importante con
desbalance.

---

# Parte 4 — Conceptos de evaluación

## Exactitud (accuracy)
% de aciertos totales. **Engaña con clases desbalanceadas** (por eso el baseline tonto de la Fase 0).

## Precisión (precision)
De todo lo que el modelo marcó como fraude, ¿cuánto era fraude de verdad?

## Exhaustividad / Recall
De todos los fraudes reales, ¿cuántos detectó el modelo? **Clave en tu problema.**

## F1
Equilibrio (media armónica) entre precisión y recall. Tu **métrica principal**. Criterio del
PDF: **F1 ≥ 0.90**.

## AUC-ROC
Mide qué tan bien el modelo separa las dos clases en todos los umbrales. 1.0 = perfecto, 0.5 = azar.

## Prueba de McNemar
Prueba **estadística** que compara dos modelos sobre las **mismas** observaciones. Da un
**valor p**: si p < 0.05, la diferencia entre el modelo profundo y el baseline es
**significativa** (no es casualidad). **Ese valor p decide tu hipótesis.**

## Kappa de Cohen
Mide el **acuerdo** entre dos etiquetadores, descontando las coincidencias por azar. Bajo 0.60
hay que revisar el manual de etiquetado.

## Valor p (p-value)
La probabilidad de que la diferencia observada sea por azar. Si es baja (< 0.05), la diferencia
es real (significativa).

---

# Parte 5 — Conceptos del proyecto

## CRISP-DM
La metodología en **6 fases** que ordena tu trabajo: comprensión del problema, datos, modelado,
evaluación, despliegue.

## Corpus
El conjunto de mensajes etiquetados. El **corpus boliviano en español es tu aporte principal**.

## Anonimización
Quitar datos personales (nombres, teléfonos, cuentas, montos) antes de guardar. **Obligación ética.**

## Smishing / Phishing / Quishing
- **Smishing:** estafa por **mensaje de texto** (SMS/WhatsApp).
- **Phishing:** estafa por **enlace** (URL falsa).
- **Quishing:** estafa por **código QR** (que lleva a una URL falsa).

## OCR
Reconocimiento óptico de caracteres: sacar el **texto** de una **imagen** (capturas de pantalla).
