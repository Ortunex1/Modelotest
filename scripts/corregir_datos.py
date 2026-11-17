"""
Aplica a DOC/datos.xlsx las correcciones de la revisión del 2026-11-17 (ver revisar_datos.py).

Regla del gancho: un mensaje es "fraudulento" solo si pide algo (enlace, datos/claves/códigos,
pago, o contacto no oficial). Si solo informa o deriva a una oficina/canal oficial -> "legitimo".
Si es ambiguo -> se descarta (se mueve a la hoja "descartados", no se borra).

Cambios:
  - 19 filas "fraudulento" sin gancho -> "legitimo" (identidad_suplantada = "ninguna").
  - 4 filas ambiguas -> hoja "descartados".
  - 5 fechas futuras -> fecha de la revisión (2026-11-17).
  - "empresa_courier" -> "courier" en todo el archivo.
Antes de modificar se guarda una copia: DOC/datos_respaldo_2026-11-17.xlsx

Uso (con datos.xlsx CERRADO en Excel): python scripts/corregir_datos.py
"""
import shutil
from datetime import datetime
from pathlib import Path

import openpyxl

DOC = Path(__file__).resolve().parent.parent.parent / "DOC"
ARCH = DOC / "datos.xlsx"
RESPALDO = DOC / "datos_respaldo_2026-11-17.xlsx"
FECHA_REVISION = datetime(2026, 11, 17)

# Solo informan o derivan a un canal/oficina oficial -> legítimo
A_LEGITIMO = {
    728: "UMSA: comunicado informativo, no pide nada",
    752: "Ministerio de Trabajo: recordatorio de plazo, no pide nada",
    765: "copia exacta de la 752 (misma etiqueta para el mismo texto)",
    755: "UMSA: aviso de cronograma, no pide nada",
    768: "Ketal: promoción canjeable en cajas (canal oficial)",
    773: "ASFI: información de horarios",
    797: "Hipermaxi: canje en sucursales (canal oficial)",
    816: "Entel: aviso de mejora sin costo, no pide datos ni pago",
    845: "DHL: aviso de retraso, no pide nada",
    851: "Banco Unión: alerta de seguridad informativa, no pide datos",
    873: "DHL: aviso de retención, no pide pago ni enlace",
    883: "Prodem: invitación informativa",
    885: "Min. Obras Públicas: aviso informativo",
    891: "Tigo: deriva a 'nuestra web' (oficial)",
    893: "Entel: deriva a oficinas comerciales (oficial)",
    900: "BCP: deriva a su app (oficial)",
    902: "AE: aviso de tarifas, informativo",
    907: "Min. Trabajo: aviso de inspección, informativo",
    917: "PIEB: convocatoria informativa",
    919: "YPFB: revisión presencial (oficial)",
}
# Ambiguos (presión/oferta sin gancho claro, o sin contexto suficiente) -> descartar
DESCARTAR = {
    804: "ambiguo: 'un oficial se comunicará' sin canal ni pedido; no se puede decidir solo con el texto",
    807: "ambiguo: oferta no solicitada sin pedido ni canal",
    868: "ambiguo: amenaza de comparecencia sin pedido ni canal oficial",
    889: "ambiguo: 'revisa el archivo compartido' sin enlace ni remitente identificable",
}
FECHA_FUTURA = [873, 893, 895, 900, 904]
# 880 (pide autenticar credenciales) y 904 (pide confirmar) SÍ tienen gancho -> siguen fraudulentos.


def main():
    if not RESPALDO.exists():
        shutil.copy2(ARCH, RESPALDO)
    wb = openpyxl.load_workbook(ARCH)
    ws = wb.worksheets[0]
    cab = [c.value for c in ws[1]]
    col = {n: i + 1 for i, n in enumerate(cab)}

    if "descartados" in wb.sheetnames:
        desc_ws = wb["descartados"]
    else:
        desc_ws = wb.create_sheet("descartados")
        desc_ws.append(cab + ["motivo_descarte"])

    n_leg = n_fecha = n_cour = 0
    borrar = []
    for fila in range(2, ws.max_row + 1):
        id_ = ws.cell(fila, col["id"]).value
        if id_ is None:
            continue
        idn = ws.cell(fila, col["identidad_suplantada"])
        if idn.value == "empresa_courier":
            idn.value = "courier"; n_cour += 1
        if id_ in A_LEGITIMO:
            ws.cell(fila, col["etiqueta"]).value = "legitimo"
            idn.value = "ninguna"; n_leg += 1
        if id_ in FECHA_FUTURA:
            ws.cell(fila, col["fecha"]).value = FECHA_REVISION; n_fecha += 1
        if id_ in DESCARTAR:
            desc_ws.append([ws.cell(fila, c).value for c in range(1, len(cab) + 1)] + [DESCARTAR[id_]])
            borrar.append(fila)

    for fila in reversed(borrar):
        ws.delete_rows(fila)
    for c in desc_ws["G"][1:]:
        c.number_format = ws.cell(2, col["fecha"]).number_format

    wb.save(ARCH)
    print(f"-> legítimo: {n_leg} | descartados: {len(borrar)} | fechas corregidas: {n_fecha} "
          f"| empresa_courier->courier: {n_cour}")
    print(f"Respaldo en {RESPALDO.name}. Filas restantes: {ws.max_row - 1}")


if __name__ == "__main__":
    main()
