"""
Arma el corpus de entrenamiento combinando datos reales + sintéticos, y lo particiona.
(Fase de preparación de datos.)

Estrategia (honesta para la evaluación):
  - SINTÉTICO (semilla) -> va SOLO al train.
  - REAL                -> se reparte: una parte al train, y val/test son REALES.
  Así las métricas se miden sobre mensajes reales, no sobre plantillas.

Formato: unifica todo a estilo LITERAL (los reales ya son literales; a los sintéticos
se les reemplazan los marcadores [MONTO]/[TELEFONO]/[NUMERO] por valores literales
variados), para que el modelo vea un formato consistente.

Entradas (LOCAL, no versionadas):
  data/crudo/corpus_real.csv          (tus 482 reales)
Entrada versionada:
  data/anonimizado/corpus_sintetico.csv (800 semilla)
Salidas (LOCAL, en data/particiones/ que está en .gitignore):
  corpus_train.csv, corpus_val.csv, corpus_test.csv

Uso:
  python scripts/armar_corpus.py
"""
import random
import re
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

SEED = 42
rng = random.Random(SEED)

RAIZ = Path.cwd()
REAL = RAIZ / "data" / "crudo" / "corpus_real.csv"
SINT = RAIZ / "data" / "anonimizado" / "corpus_sintetico.csv"
PART = RAIZ / "data" / "particiones"
PART.mkdir(parents=True, exist_ok=True)

MONTOS = ["Bs. 250", "Bs. 500", "Bs. 1.200", "Bs. 80", "350 bolivianos",
          "$us 100", "Bs. 2.000", "Bs. 150", "Bs. 750", "Bs. 3.000"]


def a_literal(texto):
    """Convierte los marcadores del sintético a valores literales variados."""
    t = str(texto)
    while "[MONTO]" in t:
        t = t.replace("[MONTO]", rng.choice(MONTOS), 1)
    while "[TELEFONO]" in t:
        t = t.replace("[TELEFONO]", "7" + "".join(str(rng.randint(0, 9)) for _ in range(7)), 1)
    while "[NUMERO]" in t:
        t = t.replace("[NUMERO]", "".join(str(rng.randint(0, 9)) for _ in range(6)), 1)
    return t


def cargar():
    if not REAL.exists():
        raise SystemExit(f"Falta {REAL} (corre la limpieza del Excel primero).")
    real = pd.read_csv(REAL)[["texto", "etiqueta"]].copy()
    real["origen"] = "real"
    sint = pd.read_csv(SINT)[["texto", "etiqueta"]].copy()
    sint["texto"] = sint["texto"].map(a_literal)   # unificar formato a literal
    sint["origen"] = "sintetico"
    return real, sint


def main():
    real, sint = cargar()
    print(f"Reales: {len(real)}  |  Sintéticos: {len(sint)}")

    # El REAL se reparte 60/20/20 (val y test SOLO reales)
    r_train, r_resto = train_test_split(real, test_size=0.40, stratify=real["etiqueta"], random_state=SEED)
    r_val, r_test = train_test_split(r_resto, test_size=0.50, stratify=r_resto["etiqueta"], random_state=SEED)

    # TRAIN = sintético completo + parte real ; VAL/TEST = solo reales
    train = pd.concat([sint, r_train], ignore_index=True).sample(frac=1, random_state=SEED).reset_index(drop=True)
    val, test = r_val.reset_index(drop=True), r_test.reset_index(drop=True)

    for nombre, part in [("corpus_train", train), ("corpus_val", val), ("corpus_test", test)]:
        part.to_csv(PART / f"{nombre}.csv", index=False, encoding="utf-8")

    def resumen(nombre, d):
        b = d["etiqueta"].value_counts().to_dict()
        o = d["origen"].value_counts().to_dict() if "origen" in d else {}
        print(f"  {nombre}: {len(d)}  | clases={b}  | origen={o}")

    print("Particiones guardadas en data/particiones/ (LOCAL, no a Git):")
    resumen("train", train)
    resumen("val  ", val)
    resumen("test ", test)
    print("\nVal y test son 100% reales -> métricas honestas.")


if __name__ == "__main__":
    main()
