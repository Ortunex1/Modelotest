# Guía de recolección del corpus — buscar casos DIFÍCILES

El objetivo ya no es *cantidad*, es **variedad y dificultad**. Un corpus donde el fraude es
obvio y lo legítimo es inofensivo hace que cualquier modelo acierte el 100% — y así **no se
puede demostrar que el deep learning aporte algo**. El valor está en los **casos borderline**.

---

## La regla de oro: los 4 cuadrantes

Piensa cada mensaje en dos ejes: **qué es** (legítimo/fraude) y **cómo se ve** (inofensivo/sospechoso).

| | **Se ve inofensivo** | **Se ve sospechoso** |
|---|---|---|
| **Es LEGÍTIMO** | 🟢 Fácil (junta algunos) | ⭐ **DIFÍCIL — busca estos** |
| **Es FRAUDE** | ⭐ **DIFÍCIL — busca estos** | 🔴 Fácil (junta algunos) |

Los dos cuadrantes con ⭐ son **oro para tu tesis**. Junta sobre todo esos.

---

## ⭐ Caso difícil 1: Fraude que parece legítimo

Fraudes **bien redactados**, sin errores, que imitan el tono real de un banco o institución.

Ejemplos (ilustrativos):
- *"Estimado cliente, por su seguridad detectamos actividad inusual en su cuenta. Comuníquese con nuestra línea de atención para verificar su identidad."* (sin enlace obvio, pide llamar)
- *"Su solicitud de crédito fue preaprobada. Un asesor se comunicará con usted en las próximas horas."* (suena normal, pero es gancho)
- *"Actualización de términos y condiciones de su cuenta. Revise los cambios en el portal oficial."* (imita comunicación real)

👉 **Dónde buscarlos:** reportes de estafas "sofisticadas", grupos de víctimas, casos que engañaron a gente con experiencia.

---

## ⭐ Caso difícil 2: Legítimo que parece sospechoso

Mensajes **reales** que, por su forma, parecen estafa.

Ejemplos (ilustrativos):
- *"BANCO X: Su código de verificación es 123456. No lo comparta con nadie."* (es un OTP legítimo, pero se parece al smishing)
- *"¡Felicidades! Ganaste el sorteo de la feria universitaria. Recoge tu premio en secretaría."* (legítimo, pero suena a "premio falso")
- *"Última oportunidad: 50% de descuento solo hoy. Compra en nuestra tienda."* (promo real agresiva)
- *"Su paquete llegó a la agencia. Recójalo con su cédula antes del viernes."* (notificación real de encomienda)

👉 **Dónde buscarlos:** tus propios SMS/WhatsApp reales (bancos, promociones, códigos OTP, encomiendas, la universidad).

---

## Los casos fáciles (junta algunos, pero no abuses)

- 🔴 **Fraude obvio:** con enlaces raros, mala ortografía, urgencia extrema, premios imposibles.
- 🟢 **Legítimo obvio:** "Hola, ¿cómo estás?", recordatorios personales, confirmaciones simples.

Necesitas algunos para el balance, pero **el modelo ya los distingue solo**. No llenes el corpus solo con estos.

---

## ❌ Qué EVITAR

| Evita | Por qué |
|---|---|
| **Familias de mensajes** (10 variantes del mismo SMS de TIGO) | El modelo memoriza el patrón → métricas infladas (1.000) |
| **El mismo mensaje con distinto monto** | Tras anonimizar quedan idénticos — cuentan como uno |
| **Rellenar con copias** para subir el número | No aporta; el modelo no aprende nada nuevo |
| Solo fraudes obvios y legítimos obvios | La tarea queda demasiado fácil |

**Mejor 10 mensajes distintos y difíciles que 100 parecidos y fáciles.**

---

## Metas prácticas

- **Variedad > cantidad.** Apunta a mensajes **distintos entre sí**.
- **Balance:** más o menos mitad fraude, mitad legítimo.
- **Prioriza los cuadrantes ⭐** (los difíciles). Si la mitad de tu corpus son casos borderline, vas excelente.
- Sigue llenando `datos.xlsx` con las **mismas 7 columnas**.

---

## Recordatorio de las columnas

`id, texto, vector, identidad_suplantada, etiqueta, fuente, fecha`

- `etiqueta`: `legitimo` o `fraudulento` (siempre igual).
- `identidad_suplantada`: banco / gobierno / telecom / courier / empleo_premio / plataforma_pago / familiar_amigo / ninguna.
- `fuente`: de dónde salió (SMS, WhatsApp, etc.).

---

> **En una frase:** busca los mensajes que **a ti mismo te harían dudar** — esos son los que
> hacen que tu modelo (y tu tesis) valgan la pena.
