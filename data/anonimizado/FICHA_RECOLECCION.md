# Ficha de recolección (Formulario de Google)

*Publícala y difúndela YA: cada semana sin difundir es una semana menos de corpus.*

Crea un Formulario de Google con estos **6 campos** y un encabezado de consentimiento.
Las respuestas se exportan a CSV y entran a `data/crudo/`; luego se anonimizan y
se llevan a `data/anonimizado/corpus.csv`.

## Encabezado — aviso de consentimiento

> Esta información se usa **solo con fines académicos** para una tesis de la carrera
> de Ingeniería de Sistemas (UPEA). No registres nombres, teléfonos, números de
> cuenta ni montos: se eliminan antes de guardar. Al enviar, autorizas el uso
> anonimizado del mensaje.

## Campos

| # | Campo | Tipo | Notas |
|---|---|---|---|
| 1 | Canal de recepción | Opción | WhatsApp / SMS / correo / otro |
| 2 | Fecha aproximada | Fecha | cuándo lo recibiste |
| 3 | Contenido del mensaje o captura | Texto largo / archivo | pega el texto o sube la imagen |
| 4 | Enlace, si lo hubo | Texto corto | la URL tal cual (opcional) |
| 5 | Entidad suplantada | Opción | banco / Estado / paquetería / empleo / premio / otro |
| 6 | Desenlace | Opción | lo ignoré / hice clic / di datos / no sé |

## Después de recibir respuestas

1. **OCR** de las capturas → texto (idioma `spa`).
   → `python scripts/ocr.py carpeta_capturas/ data/crudo/ocr.csv`
2. **Anonimización**: fuera nombres, teléfonos, cédulas, cuentas y montos
   (expresiones regulares + revisión manual).
   → `python scripts/anonimizar.py data/crudo/mensajes.csv data/anonimizado/corpus.csv`
   ⚠️ Los **nombres** requieren revisión manual (o spaCy con `es_core_news_sm`); las
   regex solo cubren teléfonos, montos, correos y números largos.
3. **Etiquetado doble** según `MANUAL_ETIQUETADO.md` y cálculo del kappa.
   → `python scripts/kappa.py etiquetados.csv etiqueta_a etiqueta_b`
4. Cargar al `corpus.csv` anonimizado.

> Meta Fase 1: `corpus.csv` con al menos **300 filas balanceadas**, el manual y el valor de kappa.
