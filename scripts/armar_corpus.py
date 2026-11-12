"""
Arma el corpus de entrenamiento combinando datos reales + sintéticos, y lo particiona.
Los datos reales se ANONIMIZAN (montos/teléfonos/códigos -> [MONTO]/[TELEFONO]/[NUMERO]),
de modo que las particiones son seguras para subir al repositorio y usarse en Colab.

Estrategia (métricas honestas):
  - SINTÉTICO -> solo al train.
  - REAL      -> una parte al train; val y test son REALES.

Entradas:
  data/crudo/corpus_real.csv            (reales, LOCAL)
  data/anonimizado/corpus_sintetico.csv (sintéticos, ya con marcadores [MONTO] etc.)
Salidas (VERSIONADAS, anonimizadas):
  data/anonimizado/particiones/corpus_train.csv / corpus_val.csv / corpus_test.csv

Uso: python scripts/armar_corpus.py
"""
import sys
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
RAIZ = Path.cwd()
sys.path.insert(0, str(RAIZ / "scripts"))
from anonimizar import anonimizar   # reusa la anonimización ya probada

REAL = RAIZ / "data" / "crudo" / "corpus_real.csv"
SINT = RAIZ / "data" / "anonimizado" / "corpus_sintetico.csv"
SAL = RAIZ / "data" / "anonimizado" / "particiones"
SAL.mkdir(parents=True, exist_ok=True)


def main():
    if not REAL.exists():
        raise SystemExit(f"Falta {REAL} (limpia el Excel primero).")

    real = pd.read_csv(REAL)[["texto", "etiqueta"]].copy()
    real["texto"] = real["texto"].map(anonimizar)   # <-- anonimiza los reales
    # De-duplicar DESPUÉS de anonimizar: mensajes que solo diferían en el monto
    # quedan idénticos y deben contar una sola vez (evita fuga entre train y val/test).
    antes = len(real)
    real = real.drop_duplicates(subset=["texto"]).reset_index(drop=True)
    print(f"Reales: {antes} -> {len(real)} tras anonimizar+dedup (colapsaron {antes-len(real)})")
    real["origen"] = "real"

    sint = pd.read_csv(SINT)[["texto", "etiqueta"]].copy()   # ya traen [MONTO] etc.
    sint["origen"] = "sintetico"
    print(f"Reales: {len(real)} (anonimizados)  |  Sintéticos: {len(sint)}")

    # REAL -> 60/20/20, estratificado. Val y test SOLO reales.
    r_tr, r_rest = train_test_split(real, test_size=0.40, stratify=real["etiqueta"], random_state=SEED)
    r_val, r_test = train_test_split(r_rest, test_size=0.50, stratify=r_rest["etiqueta"], random_state=SEED)

    train = pd.concat([sint, r_tr], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
    val, test = r_val.reset_index(drop=True), r_test.reset_index(drop=True)

    for nombre, part in [("corpus_train", train), ("corpus_val", val), ("corpus_test", test)]:
        part.to_csv(SAL / f"{nombre}.csv", index=False, encoding="utf-8")

    def resumen(n, d):
        print(f"  {n}: {len(d)} | clases={d['etiqueta'].value_counts().to_dict()}"
              f" | origen={d['origen'].value_counts().to_dict()}")

    print("Particiones ANONIMIZADAS guardadas en data/anonimizado/particiones/ (se suben al repo):")
    resumen("train", train); resumen("val  ", val); resumen("test ", test)
    print("\nVal y test son 100% reales -> métricas honestas.")


if __name__ == "__main__":
    main()
