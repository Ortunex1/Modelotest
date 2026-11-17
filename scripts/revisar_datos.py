"""
Revisa los datos recolectados y los ordena en un Excel: qué sirve, qué se descarta y qué hay que revisar a mano.

Entradas (carpeta DOC/, fuera del repo):
  DOC/datos.xlsx                            mensajes reales recolectados
  DOC/dataset_suplantacion_2041_4040.tsv    mensajes de aumento (redactados, solo para train)
Salida (LOCAL, contiene texto real sin anonimizar -> NO subir al repo):
  DOC/datos_revisados.xlsx

Reglas:
  - Un mensaje "útil" es uno DISTINTO después de anonimizar (montos/teléfonos/códigos -> [MONTO]...).
    Si dos filas quedan iguales, se guarda la primera y la otra se descarta (repetido o variante de monto).
  - "Familia": mensajes casi iguales (similitud >= UMBRAL_FAMILIA). Sirven, pero valen menos
    y deben ir juntos a la misma partición (para no inflar métricas).
  - Alertas (no descartan, piden revisión manual): fecha futura, etiqueta dudosa según la
    regla del gancho, mensaje de aumento demasiado parecido a un real.

Uso: python scripts/revisar_datos.py
"""
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from anonimizar import anonimizar  # noqa: E402

DOC = RAIZ.parent / "DOC"
REAL = DOC / "datos.xlsx"
SINT = DOC / "dataset_suplantacion_2041_4040.tsv"
SALIDA = DOC / "datos_revisados.xlsx"

HOY = date.today()
UMBRAL_FAMILIA = 0.80      # real vs real: casi el mismo mensaje
UMBRAL_SINT_REAL = 0.70    # mensaje de aumento demasiado parecido a un real -> riesgo de fuga a val/test

# --- Regla del gancho (heurística) ---
_ENLACE = re.compile(r"https?://|www\.|\b[\w-]+\.(com|net|org|bo|top|xyz|info|link|site|online|ly|me|co|app|io)\b", re.I)
_CONTACTO = re.compile(r"\[TELEFONO\]|\b[67]\d{7}\b|whatsapp|llam[ae]|comun[ií]quese|escr[ií]b|cont[aá]ct", re.I)
_PIDE = re.compile(
    r"deposit|transfer|pag[auoe]|abon|cancel[ae]|gir[oa]|"
    r"c[oó]digo|clave|contrase|\bpin\b|token|datos|carnet|c[eé]dula|tarjeta|cuenta|"
    r"ingres[ae]|clic|haz click|enlace|link|actuali[cz]|verifi|confirm|valid|desbloque|reactiv|"
    r"respond|env[ií]|reenv|comparte|descarg|instal|registr|reclam|cobr|"
    r"prest|m[aá]nd|yap[eé]|transfi|\bqr\b|saldo|[uú]nete|grupo|telegram|@\w|devu[eé]lv|adelant|reserv|autentic|credencial",
    re.I)


def alerta_etiqueta(texto, etiqueta):
    t = anonimizar(texto)
    tiene_enlace = bool(_ENLACE.search(t))
    tiene_gancho = tiene_enlace or bool(_CONTACTO.search(t)) or bool(_PIDE.search(t))
    if etiqueta == "fraudulento" and not tiene_gancho:
        return "fraude SIN gancho (no pide nada): ¿es legítimo o hay que descartarlo?"
    if etiqueta == "legitimo" and tiene_enlace:
        return "legítimo CON enlace: confirma que el dominio sea el oficial"
    return ""


def familias(textos, umbral):
    """Agrupa mensajes casi iguales (componentes conexas del grafo de similitud)."""
    X = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(textos)
    S = cosine_similarity(X)
    np.fill_diagonal(S, 0)
    _, grupo = connected_components(S >= umbral, directed=False)
    return grupo, S.max(axis=1)


def main():
    r = pd.read_excel(REAL)
    s = pd.read_csv(SINT, sep="\t")
    r["identidad_suplantada"] = r["identidad_suplantada"].replace({"empresa_courier": "courier"})
    s["identidad_suplantada"] = s["identidad_suplantada"].replace({"empresa_courier": "courier"})

    # ---------------- REALES ----------------
    r["texto_anonimizado"] = r["texto"].astype(str).map(anonimizar)
    primero = {}
    estado, igual_a = [], []
    for _, fila in r.iterrows():
        clave = fila["texto_anonimizado"]
        if clave not in primero:
            primero[clave] = fila
            estado.append("util"); igual_a.append("")
        else:
            orig = primero[clave]
            mismo = str(orig["texto"]).strip() == str(fila["texto"]).strip()
            estado.append("repetido_exacto" if mismo else "variante_solo_monto_o_numero")
            igual_a.append(int(orig["id"]))
    r["estado"], r["igual_a_id"] = estado, igual_a

    # Repetidos con distinta etiqueta = contradicción
    contradic = r.groupby("texto_anonimizado")["etiqueta"].nunique()
    contradic = set(contradic[contradic > 1].index)

    utiles = r[r["estado"] == "util"].copy()
    veces = r.groupby("texto_anonimizado").size()
    utiles["veces_en_excel"] = utiles["texto_anonimizado"].map(veces)
    grupo, sim_max = familias(utiles["texto_anonimizado"].tolist(), UMBRAL_FAMILIA)
    utiles["familia"] = grupo
    tam = pd.Series(grupo).value_counts()
    utiles["tamano_familia"] = [tam[g] for g in grupo]
    utiles["similitud_max_con_otro"] = sim_max.round(2)
    # Renumerar familias: solo las de 2+ miembros reciben número, las demás "—"
    ids_fam = {g: i + 1 for i, g in enumerate(sorted(tam[tam > 1].index))}
    utiles["familia"] = [f"F{ids_fam[g]:03d}" if g in ids_fam else "" for g in grupo]

    fechas = pd.to_datetime(utiles["fecha"], errors="coerce").dt.date
    alertas = []
    for (_, f), fe in zip(utiles.iterrows(), fechas):
        a = []
        if pd.notna(fe) and fe > HOY:
            a.append(f"fecha futura ({fe})")
        e = alerta_etiqueta(f["texto"], f["etiqueta"])
        if e:
            a.append(e)
        if f["texto_anonimizado"] in contradic:
            a.append("el mismo mensaje aparece con las DOS etiquetas")
        alertas.append(" | ".join(a))
    utiles["alertas"] = alertas

    col_u = ["id", "texto", "texto_anonimizado", "etiqueta", "identidad_suplantada", "fuente", "fecha",
             "veces_en_excel", "familia", "tamano_familia", "similitud_max_con_otro", "alertas"]
    reales_utiles = utiles[col_u].sort_values(["familia", "id"], key=lambda c: c.replace("", "ZZZ") if c.name == "familia" else c)
    reales_revisar = utiles[utiles["alertas"] != ""][col_u]
    descart = r[r["estado"] != "util"][["id", "texto", "etiqueta", "fuente", "fecha", "estado", "igual_a_id"]]
    descart = descart.rename(columns={"estado": "motivo"})

    # ---------------- AUMENTO ----------------
    s["texto"] = s["texto"].astype(str)
    s["texto_anonimizado"] = s["texto"].map(anonimizar)
    s_dup = s["texto_anonimizado"].duplicated()
    vec = TfidfVectorizer(ngram_range=(1, 2)).fit(pd.concat([s["texto_anonimizado"], utiles["texto_anonimizado"]]))
    sim_sr = cosine_similarity(vec.transform(s["texto_anonimizado"]), vec.transform(utiles["texto_anonimizado"]))
    s["similitud_max_con_real"] = sim_sr.max(axis=1).round(2)
    s["real_mas_parecido_id"] = utiles["id"].values[sim_sr.argmax(axis=1)]
    motivo = np.where(s_dup, "repetido",
              np.where(s["similitud_max_con_real"] >= UMBRAL_SINT_REAL, "casi igual a un real (fuga a val/test)", ""))
    s["motivo"] = motivo
    s["alertas"] = [alerta_etiqueta(t, e) for t, e in zip(s["texto"], s["etiqueta"])]
    col_s = ["id", "texto", "etiqueta", "identidad_suplantada", "fuente", "fecha", "similitud_max_con_real", "alertas"]
    sint_utiles = s[s["motivo"] == ""][col_s]
    sint_desc = s[s["motivo"] != ""][col_s + ["motivo", "real_mas_parecido_id"]]

    # ---------------- RESUMEN ----------------
    n_fam = (utiles["tamano_familia"] > 1).sum()
    fut = sum(1 for fe in fechas if pd.notna(fe) and fe > HOY)
    filas = [
        ("REALES (datos.xlsx)", ""),
        ("Filas en el Excel", len(r)),
        ("  Repetidos exactos (descartados)", (r["estado"] == "repetido_exacto").sum()),
        ("  Mismo mensaje con otro monto/número (descartados)", (r["estado"] == "variante_solo_monto_o_numero").sum()),
        ("  ÚTILES (mensajes distintos)", len(utiles)),
        ("     fraudulento", (utiles["etiqueta"] == "fraudulento").sum()),
        ("     legitimo", (utiles["etiqueta"] == "legitimo").sum()),
        ("     de ellos, en una 'familia' de casi iguales", n_fam),
        ("     con alguna alerta para revisar", len(reales_revisar)),
        ("        fecha futura", fut),
        ("", ""),
        ("AUMENTO (dataset_suplantacion_2041_4040)", ""),
        ("Filas", len(s)),
        ("  Repetidos", int(s_dup.sum())),
        ("  Casi iguales a un real (descartados)", int((s["motivo"] == "casi igual a un real (fuga a val/test)").sum())),
        ("  ÚTILES", len(sint_utiles)),
        ("     fraudulento", (sint_utiles["etiqueta"] == "fraudulento").sum()),
        ("     legitimo", (sint_utiles["etiqueta"] == "legitimo").sum()),
        ("     con alguna alerta para revisar", (sint_utiles["alertas"] != "").sum()),
        ("", ""),
        ("CÓMO SE USAN", ""),
        ("Reales útiles", "train + validación + test (son los únicos que miden de verdad)"),
        ("Aumento útiles", "SOLO train (aumento de datos, se declara en la metodología)"),
        ("Familias", "sirven, pero cada familia va entera a una sola partición"),
        ("Alertas", "revisar a mano: corregir etiqueta/fecha o borrar la fila en datos.xlsx"),
        ("Revisado el", str(HOY)),
    ]
    resumen = pd.DataFrame(filas, columns=["concepto", "valor"])

    with pd.ExcelWriter(SALIDA, engine="openpyxl") as xw:
        resumen.to_excel(xw, sheet_name="resumen", index=False)
        reales_utiles.to_excel(xw, sheet_name="reales_utiles", index=False)
        reales_revisar.to_excel(xw, sheet_name="reales_revisar", index=False)
        descart.to_excel(xw, sheet_name="reales_descartados", index=False)
        sint_utiles.to_excel(xw, sheet_name="aumento_utiles", index=False)
        sint_desc.to_excel(xw, sheet_name="aumento_descartados", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                letra = col[0].column_letter
                largo = max(len(str(c.value or "")) for c in col[:200])
                ws.column_dimensions[letra].width = min(max(10, largo + 2), 90)

    print(resumen.to_string(index=False))
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
