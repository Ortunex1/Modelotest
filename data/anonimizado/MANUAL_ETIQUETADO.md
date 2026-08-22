# Manual de etiquetado

*Documento vivo — sin esto, el etiquetado no es defendible ante el tribunal.*

Define, con criterios claros, qué cuenta como cada etiqueta. Todo etiquetador debe
leerlo antes de empezar. (Meta del PDF: ~2 páginas de criterios.)

## Etiquetas

### `fraudulento`
Mensaje que **suplanta una identidad** (banco, Estado, paquetería, empleo, premio…)
para engañar y obtener datos, dinero o acceso. Señales típicas:
- Pide datos sensibles (clave, código, PIN, número de cuenta, cédula).
- Enlace que imita a una entidad real pero con dominio distinto.
- Urgencia o amenaza ("su cuenta será bloqueada", "última oportunidad").
- Premio o pago inesperado que exige "confirmar datos" o pagar algo antes.

### `legitimo`
Comunicación real, **aunque sea publicidad molesta**. Ejemplos:
- Aviso real de un banco/empresa sin pedir datos por el canal.
- Promoción o publicidad legítima de un comercio.
- Mensaje personal, recordatorio de cita, notificación de servicio.

> Publicidad insistente **no es** fraude. Etiquétala `legitimo`.

### Se descarta (no entra al corpus)
- Mensajes sin texto útil o ilegibles.
- Duplicados exactos.
- Contenido que no se puede anonimizar sin perder el sentido.

## Procedimiento de etiquetado doble

1. Dos personas etiquetan **por separado** el mismo lote.
2. Se calcula el **kappa de Cohen** (`cohen_kappa_score`). Por debajo de **0,60** se
   revisa este manual antes de seguir.
3. Los desacuerdos los resuelve una **tercera persona**.
4. Se **reporta** el valor de kappa en la metodología.

## Casos límite (ir agregando aquí)

| Mensaje (ejemplo anonimizado) | Decisión | Motivo |
|---|---|---|
| *(pendiente)* | | |
