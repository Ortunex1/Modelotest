"""
Arma el corpus de entrenamiento: junta los mensajes REALES + mensajes de AUMENTO y los particiona.

Entradas (carpeta DOC/, fuera del repo):
  DOC/datos.xlsx                           reales (primera hoja; la hoja "descartados" se ignora)
  DOC/dataset_suplantacion_2041_4040.tsv   mensajes de aumento (ya anonimizados)
Salidas:
  data/anonimizado/particiones/  (VERSIONADAS, anonimizadas -> seguras para el repo y Colab)
      corpus_train.csv            reales de train + TODOS los de aumento
      corpus_train_solo_real.csv  solo reales de train (para comparar con/sin aumento)
      corpus_val.csv / corpus_test.csv   100% REALES
  DOC/corpus_completo.xlsx       (LOCAL) todo junto, con texto original y su partición

Reglas (métricas honestas):
  1. Reales: se ANONIMIZAN y se quitan duplicados DESPUÉS de anonimizar.
  2. "Familias" (mensajes casi iguales, similitud >= 0.80) van ENTERAS a una sola partición
     (StratifiedGroupKFold) -> el modelo no ve en train el "gemelo" de un mensaje de val/test.
  3. Aumento: SOLO train (aumento de datos, se declara en la metodología). Se descarta cualquiera casi igual a un real (>= 0.70).
  4. Reparto de reales: 60% train / 20% val / 20% test, estratificado por etiqueta.

Uso: python scripts/armar_corpus.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedGroupKFold

SEED = 42
UMBRAL_FAMILIA = 0.80
UMBRAL_SINT_REAL = 0.70

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from anonimizar import anonimizar  # noqa: E402

DOC = RAIZ.parent / "DOC"
REAL = DOC / "datos.xlsx"
SINT = DOC / "dataset_suplantacion_2041_4040.tsv"
SAL = RAIZ / "data" / "anonimizado" / "particiones"
COMPLETO = DOC / "corpus_completo.xlsx"


def separar_grupo(df, n_splits, seed):
    """Saca 1/n_splits de df respetando familias y estratificando por etiqueta."""
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    resto_idx, parte_idx = next(sgkf.split(df, df["etiqueta"], groups=df["familia"]))
    return df.iloc[resto_idx], df.iloc[parte_idx]


def main():
    SAL.mkdir(parents=True, exist_ok=True)

    # ---------- REALES ----------
    real = pd.read_excel(REAL, sheet_name=0)
    real = real.dropna(subset=["texto", "etiqueta"])
    real["etiqueta"] = real["etiqueta"].str.strip().str.lower()
    real["identidad_suplantada"] = real["identidad_suplantada"].replace({"empresa_courier": "courier"})
    real["texto_original"] = real["texto"].astype(str).str.strip()
    real["texto"] = real["texto_original"].map(anonimizar)
    n0 = len(real)
    real = real.drop_duplicates(subset=["texto"]).reset_index(drop=True)
    print(f"Reales: {n0} filas -> {len(real)} distintos tras anonimizar + quitar repetidos")

    X = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(real["texto"])
    S = cosine_similarity(X); np.fill_diagonal(S, 0)
    _, fam = connected_components(S >= UMBRAL_FAMILIA, directed=False)
    real["familia"] = [f"R{f:04d}" for f in fam]
    real["origen"] = "real"

    # 60/20/20 por familias: primero 20% test, luego 1/4 del resto (= 20%) val
    r_resto, r_test = separar_grupo(real, 5, SEED)
    r_train, r_val = separar_grupo(r_resto, 4, SEED)

    # ---------- AUMENTO ----------
    sint = pd.read_csv(SINT, sep="\t").dropna(subset=["texto", "etiqueta"])
    sint["texto_original"] = sint["texto"].astype(str).str.strip()
    sint["texto"] = sint["texto_original"].map(anonimizar)
    sint = sint.drop_duplicates(subset=["texto"])
    sint = sint[~sint["texto"].isin(set(real["texto"]))]
    vec = TfidfVectorizer(ngram_range=(1, 2)).fit(pd.concat([sint["texto"], real["texto"]]))
    sim = cosine_similarity(vec.transform(sint["texto"]), vec.transform(real["texto"])).max(axis=1)
    sint = sint[sim < UMBRAL_SINT_REAL].copy()
    sint["familia"] = ""
    sint["origen"] = "aumento"
    sint["fuente"] = "aumento"
    print(f"Aumento: {len(sint)} (solo train)")

    # ---------- PARTICIONES ----------
    cols = ["texto", "etiqueta", "origen", "familia"]
    mezclar = lambda d: d.sample(frac=1, random_state=SEED).reset_index(drop=True)
    train = mezclar(pd.concat([r_train[cols], sint[cols]], ignore_index=True))
    train_real = mezclar(r_train[cols])
    val, test = mezclar(r_val[cols]), mezclar(r_test[cols])

    # Verificación de fuga
    tr_txt = set(train["texto"])
    assert not (tr_txt & set(val["texto"])) and not (tr_txt & set(test["texto"])) \
        and not (set(val["texto"]) & set(test["texto"])), "FUGA: texto repetido entre particiones"
    f_tr, f_va, f_te = set(r_train["familia"]), set(r_val["familia"]), set(r_test["familia"])
    assert not (f_tr & f_va) and not (f_tr & f_te) and not (f_va & f_te), "FUGA: familia partida"
    v2 = TfidfVectorizer(ngram_range=(1, 2)).fit(real["texto"])
    gemelo = lambda d: (cosine_similarity(v2.transform(d["texto"]), v2.transform(r_train["texto"]))
                        .max(axis=1) >= UMBRAL_FAMILIA).sum()

    for nombre, d in [("corpus_train", train), ("corpus_train_solo_real", train_real),
                      ("corpus_val", val), ("corpus_test", test)]:
        d.to_csv(SAL / f"{nombre}.csv", index=False, encoding="utf-8")

    # ---------- ARCHIVO COMPLETO (local) ----------
    r_train = r_train.assign(particion="train"); r_val = r_val.assign(particion="val")
    r_test = r_test.assign(particion="test"); sint = sint.assign(particion="train")
    todo = pd.concat([r_train, r_val, r_test, sint], ignore_index=True)
    todo = todo[["id", "origen", "particion", "etiqueta", "identidad_suplantada", "fuente", "fecha",
                 "familia", "texto_original", "texto"]].rename(columns={"texto": "texto_anonimizado"})
    todo = todo.sort_values(["origen", "id"])
    resumen = (todo.groupby(["particion", "origen", "etiqueta"]).size()
               .unstack("etiqueta", fill_value=0).reset_index())
    resumen["total"] = resumen[["fraudulento", "legitimo"]].sum(axis=1)
    with pd.ExcelWriter(COMPLETO, engine="openpyxl") as xw:
        resumen.to_excel(xw, sheet_name="resumen", index=False)
        todo.to_excel(xw, sheet_name="corpus", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                largo = max(len(str(c.value or "")) for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, largo + 2), 80)

    def linea(n, d):
        print(f"  {n:<24}{len(d):>5} | {d['etiqueta'].value_counts().to_dict()} | {d['origen'].value_counts().to_dict()}")

    print("\nParticiones (anonimizadas) en data/anonimizado/particiones/:")
    linea("train (real+aumento)", train); linea("train_solo_real", train_real)
    linea("val", val); linea("test", test)
    print(f"\nFuga: 0 textos repetidos, 0 familias partidas. "
          f"Gemelos (>= {UMBRAL_FAMILIA}) en train: val={gemelo(val)}, test={gemelo(test)}")
    print(f"Todo junto (local): {COMPLETO}  ->  {len(todo)} mensajes")


if __name__ == "__main__":
    main()
