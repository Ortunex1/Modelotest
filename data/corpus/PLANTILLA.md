# Plantilla del corpus boliviano

Este es **tu aporte y tu prioridad**. No se descarga: se recolecta.

Meta: **500–1.500 mensajes fraudulentos** bien etiquetados + una cantidad parecida de legítimos.

## Campos (uno por columna en `corpus_boliviano.csv`)

| Campo | Descripción | Valores |
|---|---|---|
| `id` | Número correlativo | 1, 2, 3, … |
| `texto` | Contenido del mensaje **anonimizado** | texto libre |
| `vector` | Canal del ataque | `texto` / `url` / `qr` |
| `identidad_suplantada` | A quién finge ser | `banco` / `Estado` / `paqueteria` / `empleo` / `premio` / `otro` |
| `etiqueta` | Clasificación | `legitimo` / `fraudulento` |
| `fuente` | De dónde salió | `WhatsApp` / `SMS` / `reporte` / `FELCC` |
| `fecha` | Fecha de recolección | AAAA-MM-DD |

## Reglas de anonimización y ética (obligatorias)

1. **Borra antes de guardar**: nombres de personas, números de teléfono, cédulas y datos de cuentas.
2. Los datasets públicos se usan **solo con fines académicos**.
3. **Lo fraudulento es el mensaje, no la entidad suplantada**: no señales a ningún banco o institución como inseguro.

## Fuentes para recolectar

Capturas y reenvíos de WhatsApp/SMS de conocidos, grupos comunitarios, reportes públicos y —si se consigue— datos de la FELCC.
