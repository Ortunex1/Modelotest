# Guía de defensa — preguntas del tribunal y cómo responderlas

Las preguntas típicas que hace un tribunal sobre un proyecto como el tuyo, con respuestas
listas para estudiar. La idea no es memorizar, sino **entender la lógica** de cada respuesta.

---

## Sobre el enfoque general

### ¿De qué trata tu tesis en una frase?
Un sistema que detecta estafas por suplantación de identidad (smishing, phishing y quishing)
en mensajes, enlaces y códigos QR, usando aprendizaje profundo, con foco en el contexto
boliviano en español.

### ¿Cuál es tu aporte principal?
El **corpus boliviano en español**: un conjunto de mensajes reales de estafa y legítimos,
recolectado y etiquetado por mí. No existe un dataset así; los datasets públicos están en
inglés o son solo de URLs. Ese corpus es lo que permite entrenar un detector adaptado a
nuestro contexto.

### ¿Por qué es relevante el problema?
Las estafas por suplantación crecen y afectan sobre todo a personas con baja alfabetización
digital. Un detector en español, del contexto local, puede alertar a tiempo.

---

## Sobre la metodología

### ¿Qué metodología usaste?
**CRISP-DM**, en 6 fases: comprensión del problema, comprensión y preparación de datos,
modelado, evaluación, y despliegue. La mayor parte del esfuerzo está en los datos.

### ¿Por qué separas los datos en train, validación y test?
Para no engañarme a mí mismo. Entreno con train, ajusto la configuración con validación, y
reservo el test para medir el rendimiento real **una sola vez**. Si usara el test para decidir,
mis resultados estarían contaminados.

### ¿Cómo garantizas que tus resultados son reproducibles?
Fijo una **semilla aleatoria** en cada partición y entrenamiento, y llevo una bitácora de
cada experimento. Así puedo repetir exactamente cualquier resultado.

---

## Sobre por qué deep learning

### ¿Por qué usar deep learning y no solo machine learning clásico?
Porque el lenguaje natural tiene matices (contexto, sinónimos, redacción) que los modelos
clásicos captan peor. BETO entiende el **contexto** del español. Pero no lo afirmo sin más:
**lo demuestro** comparando contra un baseline clásico con la prueba de McNemar.

### Entonces, ¿el machine learning clásico para qué está?
Es mi **línea base**, el rival. Son los mismos algoritmos del antecedente local (Regresión
Logística y Naive Bayes). Si mi modelo profundo no le gana de forma significativa, no hay
aporte. Es la referencia contra la que se mide la hipótesis.

### ¿Por qué BETO y no otro modelo?
Porque está preentrenado específicamente en **español**. Un BERT en inglés no serviría para
mensajes en español boliviano. Además, hacer **ajuste fino** de BETO me permite trabajar con
un corpus pequeño.

---

## Sobre los datos

### ¿Cómo construiste el corpus?
Con una ficha de recolección (formulario de Google) difundida en la comunidad, más
recopilación de capturas públicas. Las capturas se convierten a texto con **OCR**, se
**anonimizan** (quitando datos personales) y se etiquetan.

### ¿Cómo aseguras la calidad del etiquetado?
Con **etiquetado doble**: dos personas etiquetan por separado, calculo el **kappa de Cohen**
para medir el acuerdo, y los desacuerdos los resuelve una tercera persona. Reporto el valor
de kappa.

### ¿Qué haces con los datos personales?
Los **anonimizo** antes de guardar: elimino nombres, teléfonos, cédulas, cuentas y montos, con
expresiones regulares y revisión manual. Es una obligación ética; nunca subo datos sin
anonimizar a ningún servicio público.

### ¿Qué pasa si el corpus queda pequeño?
Aplico **aumento de datos** con variaciones controladas e incorporo corpus públicos en
español, y lo **declaro** explícitamente en la metodología. También pondero la función de
pérdida en vez de descartar ejemplos.

### ¿Por qué el motor de URL usa datos en inglés y el de texto no?
Porque **las URLs no tienen idioma**: una dirección web sospechosa se ve igual en cualquier
país. El texto sí depende del idioma, y ahí es donde mi corpus en español es indispensable.

---

## Sobre la evaluación

### ¿Por qué usas F1 y no la exactitud?
Porque mis clases están **desbalanceadas** (hay más mensajes legítimos que fraudes). Un modelo
que siempre dijera "legítimo" tendría alta exactitud pero no detectaría ningún fraude. El F1
de la clase fraudulento sí refleja el rendimiento real. Lo demuestro con el baseline tonto.

### ¿Qué es el error más costoso en tu problema?
El **falso negativo**: una estafa que el modelo deja pasar. Un falso positivo solo asusta de
más; un falso negativo puede costarle dinero al usuario. Por eso vigilo la exhaustividad (recall).

### ¿Por qué la prueba de McNemar y no solo comparar F1?
Porque una diferencia de F1 podría ser **casualidad**. McNemar es una prueba **estadística**
que compara los dos modelos sobre los mismos mensajes y me da un **valor p**. Si p < 0.05, la
mejora es significativa. Ese valor p, no la diferencia de F1, es lo que decide mi hipótesis.

### ¿Cuál es tu criterio de aceptación?
Que el modelo profundo alcance **F1 ≥ 0.90** y que supere al baseline de forma
**estadísticamente significativa** (McNemar, p < 0.05).

### ¿Cómo analizas los errores del modelo?
Reviso a mano ~20 errores del modelo sobre el test. Esa lectura me dice qué tipo de mensajes
lo confunden y es el material de mi discusión de resultados.

---

## Sobre la arquitectura

### ¿Cómo funciona el motor de QR?
El QR **no es un modelo aparte**. La foto del QR se **decodifica a una URL**, y esa URL entra
al motor de enlaces. Reutilizo el motor de URL.

### ¿Cómo se combinan los dos motores?
En un **módulo de decisión** que toma la salida de ambos y emite tres niveles: **Seguro,
Sospechoso o Peligroso**, con umbrales que yo justifico.

### ¿Por qué n-gramas de caracteres para las URLs?
Porque una URL no tiene palabras, tiene **subcadenas sospechosas** (como `-login-` o `.xyz`).
Los n-gramas de caracteres capturan justamente esos patrones.

### ¿Tu sistema protege contra el envenenamiento de DNS o ataques de red (TCP/UDP)?
No, y es a propósito. Mi detector trabaja en la **capa de aplicación**: analiza el **contenido**
de mensajes, enlaces (HTTP/HTTPS) y QR para decidir si parecen estafa. El envenenamiento de
**DNS** o **ARP**, y los ataques sobre **TCP/UDP**, ocurren en la **capa de red/transporte** y
se combaten con defensas de infraestructura (DNSSEC, certificados, firewalls, IDS), no con un
clasificador de texto. Por eso quedan **fuera del alcance** de la tesis; es una delimitación
deliberada, no un olvido.

### Entonces, ¿qué pasa con enlaces que no son HTTP/HTTPS (tel:, mailto:, etc.)?
Un mensaje de estafa puede traer esquemas como `tel:`, `sms:` o `mailto:`. Como el **motor de
texto (BETO)** lee el mensaje completo, esos casos los capta igual por el contenido. El **motor
de URL** se enfoca en HTTP/HTTPS porque es lo estándar del phishing y de los datasets públicos.

### ¿Cómo detecta tu sistema un QR que lleva a una URL parecida a la de un banco real?
Ese es un caso central de **quishing**: el QR se decodifica a una URL que **imita** al banco
pero es falsa. Mi sistema lo procesa así: QR → se decodifica a URL → la URL entra al motor de
enlaces. Los enlaces de imitación usan trucos que dejan **huella en los caracteres**:
- **Typosquatting:** errores tipográficos (`banc0sol.com`, `bancosoI.com` con i mayúscula).
- **Combosquatting:** agregan palabras (`bancosol-seguro.xyz`, `secure-bancosol.com`).
- **TLD distinto:** dominios raros (`bancosol.xyz`, `bancosol.info`).
- **Subdominio engañoso:** `bancosol.verificacion-cuenta.xyz` (el banco es solo el gancho).
- **Homoglifos:** letras visualmente iguales de otro alfabeto (la `а` cirílica por la `a` latina).

Por eso mi motor de URL trabaja a **nivel de carácter** (n-gramas de caracteres y CNN de
caracteres), no de palabra: un modelo de palabras no distingue `bancosol` de `banc0sol`, pero
uno de caracteres **sí** capta esas subcadenas sospechosas. El diseño está pensado justo para
atrapar estos dominios de imitación.

> Distínguelo del **envenenamiento de DNS**: ese redirige un dominio **legítimo** a un servidor
> falso a nivel de red (fuera de alcance). Aquí el dominio ya **es** falso y se detecta por su
> texto (dentro de alcance).

---

## Sobre las limitaciones (te lo van a preguntar)

### ¿Qué limitaciones tiene tu trabajo?
- El corpus, al ser recolectado, puede tener sesgos (según quién reportó).
- El modelo aprende de estafas **conocidas**; las nuevas modalidades requieren reentrenar.
- El prototipo es una **demostración**, no una app lista para producción.

### ¿Qué trabajo futuro propones?
- Ampliar y actualizar el corpus continuamente.
- Detección multimodal (imagen + texto en la misma captura).
- Integración con canales reales (WhatsApp Business, apps bancarias).

---

## Consejo final

Si no sabes una respuesta, **no inventes**. Di lo que sí sabes, reconoce el límite y explica
cómo lo abordarías. Un tribunal valora más la honestidad y el criterio que una respuesta
memorizada. Y ten siempre a mano tu **matriz de confusión** y tu **valor de F1**: casi todo se
explica desde ahí.
