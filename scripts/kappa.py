"""
Kappa de Cohen — acuerdo entre etiquetadores (Fase 1).

Dos personas etiquetan por separado el mismo lote de mensajes. El kappa mide
cuánto coinciden más allá del azar. El PDF: por debajo de 0.60 hay que revisar
el manual de etiquetado antes de seguir, y el valor se REPORTA en la metodología.

Uso por consola (CSV con dos columnas de etiquetas):
    python scripts/kappa.py etiquetados.csv etiqueta_a etiqueta_b

Sin argumentos, corre una prueba de ejemplo:
    python scripts/kappa.py
"""
import sys
import csv

from sklearn.metrics import cohen_kappa_score


def interpretar(k):
    """Escala de referencia (Landis & Koch)."""
    if k < 0.00:
        return "sin acuerdo (peor que el azar)"
    if k < 0.20:
        return "leve"
    if k < 0.40:
        return "aceptable bajo"
    if k < 0.60:
        return "moderado (REVISAR el manual, umbral del PDF)"
    if k < 0.80:
        return "sustancial (bien)"
    return "casi perfecto (excelente)"


def kappa(etiq_a, etiq_b):
    """Calcula el kappa de Cohen entre dos listas de etiquetas del mismo largo."""
    if len(etiq_a) != len(etiq_b):
        raise ValueError(f"Las listas difieren en largo: {len(etiq_a)} vs {len(etiq_b)}")
    if not etiq_a:
        raise ValueError("No hay etiquetas para comparar.")
    return cohen_kappa_score(etiq_a, etiq_b)


def kappa_desde_csv(ruta, col_a, col_b):
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    a = [fila[col_a] for fila in filas]
    b = [fila[col_b] for fila in filas]
    return kappa(a, b), len(filas)


def _reportar(k, n=None):
    extra = f" sobre {n} mensajes" if n else ""
    print(f"Kappa de Cohen{extra}: {round(k, 3)}")
    print(f"Interpretación: {interpretar(k)}")


def _prueba():
    print("=== PRUEBA (dos etiquetadores con un desacuerdo) ===")
    a = ["fraudulento", "legitimo", "fraudulento", "legitimo", "fraudulento"]
    b = ["fraudulento", "legitimo", "fraudulento", "fraudulento", "fraudulento"]
    _reportar(kappa(a, b), len(a))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _prueba()
    elif len(sys.argv) == 4:
        k, n = kappa_desde_csv(sys.argv[1], sys.argv[2], sys.argv[3])
        _reportar(k, n)
    else:
        print("Uso:\n  python kappa.py                               (corre una prueba)\n"
              "  python kappa.py etiquetados.csv etiqueta_a etiqueta_b")
