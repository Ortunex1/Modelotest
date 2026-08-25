"""
Generador de corpus sintético (semilla) — Fase 1.

Crea ~800 mensajes en español (fraudulentos y legítimos) con VARIACIONES CONTROLADAS,
para arrancar el corpus mientras se recolectan los reales.

IMPORTANTE (declararlo en la tesis):
  - Estos datos son SINTÉTICOS, no reales. Se marcan con fuente='sintetico'.
  - Sirven de SEMILLA para el entrenamiento; la validación y el test deben incluir
    mensajes REALES para que las métricas reflejen el rendimiento real.
  - Ya salen "anonimizados" (usan [MONTO], [TELEFONO], [NUMERO]) para coincidir con
    el formato del corpus real tras pasar por scripts/anonimizar.py.

Uso:
  python scripts/generar_corpus_sintetico.py            # genera data/anonimizado/corpus_sintetico.csv
  python scripts/generar_corpus_sintetico.py 800        # genera N mensajes (balanceados)
"""
import sys
import csv
import random
from pathlib import Path

SEED = 42
FECHA = "2026-08-25"   # fecha de generación (declarable)

# --- Slots (rellenos) ---
URLS = ["verificacion-cuenta.xyz/acceso", "seguro-banca.info/login", "bit.ly/3xKq9a",
        "aduana-pagos.site/tramite", "premios-online.top/ganador", "gob-tramite.xyz/bono",
        "mi-entidad-segura.com/validar", "soporte-cuenta.info/urgente", "envios-retenidos.site",
        "actualiza-datos.top/cliente", "beneficio-estatal.xyz/cobro", "empleo-express.info/registro"]
COURIERS = ["la agencia de encomiendas", "la empresa de envios", "la paqueteria", "el courier"]
PREMIOS = ["un celular de ultima generacion", "Bs. 5.000 en efectivo", "una laptop",
           "un bono de compras", "una motocicleta", "un viaje todo pagado"]
PLAZOS = ["hoy", "en 24 horas", "antes de las 18:00", "en las proximas 2 horas", "manana"]
HORAS = ["08:00", "10:00", "14:30", "16:00", "09:15", "11:00"]
DIAS = ["lunes", "martes", "el viernes", "el 15 de este mes", "manana", "el proximo lunes"]
TIENDAS = ["la tienda", "el minimarket del barrio", "la farmacia", "la libreria", "el comercio"]
SERVICIOS = ["luz", "agua", "internet", "gas", "telefonia"]
TRAMITES = ["tu tramite", "la renovacion de tu documento", "tu consulta medica", "tu inscripcion"]

# --- Plantillas FRAUDULENTAS por identidad suplantada ---
FRAUDE = {
    "banco": [
        "Estimado cliente, su cuenta sera suspendida por seguridad. Valide sus datos en {url} de inmediato.",
        "ALERTA: detectamos un acceso no autorizado a su cuenta. Confirme su identidad en {url} o sera bloqueada.",
        "Su tarjeta fue bloqueada por seguridad. Para reactivarla ingrese a {url} y verifique su clave.",
        "Su token de acceso expira {plazo}. Actualice sus datos en {url} para no perder el servicio.",
        "Estimado usuario, se registro un intento de compra por [MONTO]. Si no fue usted, cancele en {url}.",
        "Su clave digital vencio. Genere una nueva en {url} antes de {plazo} para evitar el bloqueo.",
    ],
    "Estado": [
        "Usted tiene un bono de [MONTO] disponible. Cobrelo en {url} con su numero de carnet {plazo}.",
        "Su documento de identidad vence. Renuevelo en linea en {url} antes de {plazo}.",
        "Devolucion de impuestos aprobada: [MONTO]. Ingrese sus datos bancarios en {url} para recibirla.",
        "Programa social: usted es beneficiario de [MONTO]. Registre su cuenta en {url} {plazo}.",
    ],
    "paqueteria": [
        "Su paquete de {courier} esta retenido en aduana. Pague [MONTO] en {url} para liberarlo.",
        "No pudimos entregar su envio. Reprograme y pague [MONTO] de reenvio en {url}.",
        "Encomienda pendiente a su nombre. Confirme su direccion y pague [MONTO] aqui: {url}",
        "Su pedido esta detenido por falta de pago aduanero de [MONTO]. Regularice en {url} {plazo}.",
    ],
    "empleo": [
        "Trabajo desde casa, gane [MONTO] al dia. Cupos limitados, escriba al WhatsApp [TELEFONO].",
        "Empresa selecciona personal, sueldo [MONTO]. Registrese pagando [MONTO] de inscripcion en {url}.",
        "Vacante urgente medio tiempo, gane [MONTO] semanal sin experiencia. Mas info: {url}",
        "Seleccionado para entrevista de trabajo. Confirme sus datos y pague el examen medico [MONTO] en {url}.",
    ],
    "premio": [
        "FELICIDADES! usted gano {premio}. Reclamelo en {url} antes de {plazo}.",
        "Su numero fue seleccionado para {premio}. Pague [MONTO] de envio y reciba su premio: {url}",
        "Promocion exclusiva: usted es el ganador de {premio}. Confirme sus datos en {url}.",
        "Ha sido premiado con {premio}. Para recibirlo ingrese sus datos en {url} {plazo}.",
    ],
    "otro": [
        "Mama te quedaste sin saldo? este es mi nuevo numero. Recargame [MONTO] al [TELEFONO], luego te explico.",
        "Hola soy yo, cambie de numero. Necesito un favor urgente, puedes prestarme [MONTO]? te devuelvo manana.",
        "Su linea sera dada de baja por falta de actualizacion. Valide sus datos en {url} {plazo}.",
        "Confirmamos su suscripcion por [MONTO] mensual. Si no la reconoce, cancele en {url}.",
    ],
}

# --- Plantillas LEGÍTIMAS (incluye publicidad y avisos reales que NO piden datos) ---
LEGITIMO = [
    "Hola, te confirmo la reunion de manana a las {hora} en la oficina.",
    "Recordatorio: tu cita medica es {dia} a las {hora}. Llega 10 minutos antes por favor.",
    "Buenos dias, ya te envie el informe por correo. Cualquier cosa me avisas.",
    "Feliz cumpleanos! que tengas un lindo dia, un abrazo grande.",
    "Te llego el material que te preste? avisame cuando puedas pasarmelo.",
    "Su factura de {servicio} ya esta disponible. Vencimiento {dia}. Gracias.",
    "Gracias por su compra en {tienda}. Su pedido llegara {dia}.",
    "Su turno para {tramite} fue agendado para {dia} a las {hora}.",
    "{tienda}: 20% de descuento este fin de semana en toda la tienda. Te esperamos!",
    "Le informamos que su pago de servicios fue registrado correctamente. Gracias por su preferencia.",
    "Estimado cliente, su estado de cuenta ya esta disponible en nuestra app oficial.",
    "Hola profe, le escribo para consultar sobre la clase de manana. Habra examen?",
    "Ya llegue a casa, todo bien. Cualquier cosa te llamo mas tarde.",
    "Reunion de la directiva reprogramada para {dia}. Confirmen asistencia por favor.",
    "Se comunica a los vecinos que el corte de {servicio} sera {dia} de {hora} a la tarde.",
    "Gracias por escribir a atencion al cliente. Su consulta fue registrada, le responderemos pronto.",
    "El pedido que hiciste ya esta listo para recoger en {tienda}. Horario de atencion normal.",
    "Buenas, confirmo que recibi el pago. Muchas gracias, que tengas buen dia.",
]


def _fill(t, rng):
    return t.format(url=rng.choice(URLS), courier=rng.choice(COURIERS), premio=rng.choice(PREMIOS),
                    plazo=rng.choice(PLAZOS), hora=rng.choice(HORAS), dia=rng.choice(DIAS),
                    tienda=rng.choice(TIENDAS), servicio=rng.choice(SERVICIOS), tramite=rng.choice(TRAMITES))


def generar(n_total=800):
    rng = random.Random(SEED)
    objetivo = n_total // 2
    filas, vistos = [], set()

    # Fraudulentos (repartidos entre categorías)
    categorias = list(FRAUDE.keys())
    intentos = 0
    while sum(1 for f in filas if f["etiqueta"] == "fraudulento") < objetivo and intentos < objetivo * 50:
        intentos += 1
        cat = rng.choice(categorias)
        texto = _fill(rng.choice(FRAUDE[cat]), rng)
        if texto in vistos:
            continue
        vistos.add(texto)
        filas.append({"texto": texto, "vector": "texto", "identidad_suplantada": cat,
                      "etiqueta": "fraudulento", "fuente": "sintetico", "fecha": FECHA})

    # Legítimos
    intentos = 0
    while sum(1 for f in filas if f["etiqueta"] == "legitimo") < objetivo and intentos < objetivo * 50:
        intentos += 1
        texto = _fill(rng.choice(LEGITIMO), rng)
        if texto in vistos:
            continue
        vistos.add(texto)
        filas.append({"texto": texto, "vector": "texto", "identidad_suplantada": "otro",
                      "etiqueta": "legitimo", "fuente": "sintetico", "fecha": FECHA})

    rng.shuffle(filas)
    for i, f in enumerate(filas, 1):
        f["id"] = i
    return filas


def guardar(filas, ruta):
    campos = ["id", "texto", "vector", "identidad_suplantada", "etiqueta", "fuente", "fecha"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 800
    filas = generar(n)
    salida = Path("data/anonimizado/corpus_sintetico.csv")
    guardar(filas, salida)
    n_fraude = sum(1 for f in filas if f["etiqueta"] == "fraudulento")
    print(f"Generados {len(filas)} mensajes ({n_fraude} fraudulentos / {len(filas)-n_fraude} legitimos)")
    print(f"Guardado en {salida}")
    print("RECUERDA: son sintéticos (fuente='sintetico'). Declararlo en la tesis y mezclar con datos reales.")
