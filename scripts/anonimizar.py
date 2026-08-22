"""
Anonimización de mensajes del corpus (Fase 1).

Regla ética del PDF: fuera nombres, teléfonos, números de cuenta/cédula y montos
ANTES de guardar el mensaje. Usa expresiones regulares + una revisión manual.

Los datos sensibles se reemplazan por etiquetas ([TELEFONO], [MONTO], ...), lo que
CONSERVA el patrón del fraude sin exponer datos reales.

Uso como módulo:
    from anonimizar import anonimizar
    limpio = anonimizar("Llama al 71234567 y deposita Bs. 1.500")

Uso por consola (anonimiza la columna 'texto' de un CSV):
    python scripts/anonimizar.py data/crudo/mensajes.csv data/anonimizado/corpus.csv

Sin argumentos, corre una batería de pruebas:
    python scripts/anonimizar.py
"""
import re
import sys
import csv

# --- Patrones (el orden importa: de lo más específico a lo más general) ---

# 1) Correos electrónicos
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# 2) Montos: Bs. 1.500 / $us 200 / USD 50 / 1.500 bolivianos
_MONTO = re.compile(
    r"(?:(?:bs\.?|\$us|\$|usd|bolivianos?)\s*\.?\s*\d[\d.,]*)"
    r"|(?:\d[\d.,]*\s*(?:bs\.?|bolivianos?|\$us|usd))",
    re.IGNORECASE,
)

# 3) Teléfonos Bolivia: +591 7012 3456 / 71234567 (móvil 8 díg. empieza 6 o 7)
_TEL_INTL = re.compile(r"\+?591[\s\-]?\d{4}[\s\-]?\d{4}")
_TEL_MOVIL = re.compile(r"\b[67]\d{7}\b")

# 4) Números largos restantes (cuentas / cédulas de 7+ dígitos)
_NUM_LARGO = re.compile(r"\b\d{7,}\b")


def anonimizar(texto, usar_ner=False):
    """Devuelve el texto con los datos personales reemplazados por etiquetas.

    usar_ner=True intenta borrar además nombres de persona con spaCy (modelo
    es_core_news_sm). Si spaCy o el modelo no están, se ignora sin fallar.
    """
    if texto is None:
        return ""
    t = str(texto)

    t = _EMAIL.sub("[EMAIL]", t)
    t = _MONTO.sub("[MONTO]", t)
    t = _TEL_INTL.sub("[TELEFONO]", t)
    t = _TEL_MOVIL.sub("[TELEFONO]", t)
    t = _NUM_LARGO.sub("[NUMERO]", t)

    if usar_ner:
        t = _quitar_nombres_ner(t)

    # Normaliza espacios sobrantes
    return re.sub(r"\s{2,}", " ", t).strip()


_NLP = None


def _quitar_nombres_ner(texto):
    """Reemplaza entidades PER (persona) por [NOMBRE] usando spaCy, si está disponible."""
    global _NLP
    if _NLP is None:
        try:
            import spacy
            _NLP = spacy.load("es_core_news_sm")
        except Exception:
            print("[aviso] spaCy/es_core_news_sm no disponible; se omiten los nombres. "
                  "Instálalo con: python -m spacy download es_core_news_sm", file=sys.stderr)
            _NLP = False
    if not _NLP:
        return texto
    doc = _NLP(texto)
    resultado = texto
    for ent in sorted(doc.ents, key=lambda e: -e.start_char):
        if ent.label_ == "PER":
            resultado = resultado[:ent.start_char] + "[NOMBRE]" + resultado[ent.end_char:]
    return resultado


def anonimizar_csv(entrada, salida, columna="texto", usar_ner=False):
    """Anonimiza la columna indicada de un CSV y escribe el resultado."""
    with open(entrada, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        print("El CSV está vacío.")
        return
    if columna not in filas[0]:
        raise KeyError(f"No existe la columna '{columna}'. Columnas: {list(filas[0])}")
    for fila in filas:
        fila[columna] = anonimizar(fila[columna], usar_ner=usar_ner)
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"Anonimizados {len(filas)} mensajes -> {salida}")


def _pruebas():
    casos = [
        ("Hola Juan, tu cuenta 1234567890 sera bloqueada. Llama al 71234567.",
         ["[NUMERO]", "[TELEFONO]"]),
        ("Deposita Bs. 1.500 o $us 200 hoy mismo",
         ["[MONTO]"]),
        ("Escribe a soporte@banco.com o al +591 7012 3456",
         ["[EMAIL]", "[TELEFONO]"]),
        ("Recordatorio: tu cita es manana a las 10",
         []),  # no debe cambiar nada sensible
    ]
    print("=== PRUEBAS DE ANONIMIZACIÓN ===")
    ok = True
    for original, esperados in casos:
        limpio = anonimizar(original)
        faltan = [e for e in esperados if e not in limpio]
        estado = "OK " if not faltan else "FALLA"
        if faltan:
            ok = False
        print(f"[{estado}] {original}")
        print(f"        -> {limpio}")
    print("\nResultado:", "todas las pruebas pasaron" if ok else "hay fallas")
    return ok


if __name__ == "__main__":
    if len(sys.argv) == 1:
        _pruebas()
    elif len(sys.argv) == 3:
        anonimizar_csv(sys.argv[1], sys.argv[2])
    else:
        print("Uso:\n  python anonimizar.py                (corre pruebas)\n"
              "  python anonimizar.py entrada.csv salida.csv")
