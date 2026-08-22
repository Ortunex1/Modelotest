"""
OCR de capturas → texto (Fase 1).

Convierte imágenes (capturas de estafas recopiladas de la web, WhatsApp, etc.) en texto,
para luego anonimizar, etiquetar y meter al corpus. Hace UNA sola cosa: imagen → texto.

Requisitos:
  1. pip install pytesseract opencv-python pillow   (ya están en el entorno 'tesis')
  2. Programa Tesseract-OCR con idioma español instalado
     (en este equipo: C:\\Program Files\\Tesseract-OCR).

Uso:
  python scripts/ocr.py captura.jpg                              # una imagen -> imprime el texto
  python scripts/ocr.py carpeta_capturas/ data/crudo/ocr.csv    # carpeta -> CSV (archivo, texto)

Después, el CSV se anonimiza con:
  python scripts/anonimizar.py data/crudo/ocr.csv data/anonimizado/corpus.csv
"""
import sys
import csv
from pathlib import Path

import cv2
import pytesseract

# --- Localizar el ejecutable de Tesseract en Windows (si no está en el PATH) ---
_RUTAS_TESSERACT = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    str(Path.home() / "AppData/Local/Programs/Tesseract-OCR/tesseract.exe"),
]
for _r in _RUTAS_TESSERACT:
    if Path(_r).exists():
        pytesseract.pytesseract.tesseract_cmd = _r
        break

EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def leer_imagen(ruta, idioma="spa"):
    """Devuelve el texto de una imagen. Pasa a escala de grises para mejorar el OCR."""
    img = cv2.imread(str(ruta))
    if img is None:
        raise FileNotFoundError(f"No se pudo abrir la imagen: {ruta}")
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    texto = pytesseract.image_to_string(gris, lang=idioma)
    return " ".join(texto.split())   # una sola línea limpia, útil para el CSV


def procesar_carpeta(carpeta, salida, idioma="spa"):
    """OCR a todas las imágenes de una carpeta -> CSV con columnas (archivo, texto)."""
    carpeta = Path(carpeta)
    imagenes = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in EXTENSIONES)
    if not imagenes:
        print(f"No se encontraron imágenes en {carpeta}")
        return
    filas = []
    for img in imagenes:
        try:
            texto = leer_imagen(img, idioma)
            filas.append({"archivo": img.name, "texto": texto})
            print(f"[OK] {img.name}: {texto[:60]}{'...' if len(texto) > 60 else ''}")
        except Exception as e:
            print(f"[FALLA] {img.name}: {e}", file=sys.stderr)
    with open(salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "texto"])
        w.writeheader()
        w.writerows(filas)
    print(f"\n{len(filas)} imágenes procesadas -> {salida}")
    print("Siguiente paso: python scripts/anonimizar.py", salida, "data/anonimizado/corpus.csv")


def _verificar_tesseract():
    try:
        print(f"Tesseract detectado: versión {pytesseract.get_tesseract_version()}")
        return True
    except Exception:
        print("⚠️ No se encontró Tesseract-OCR. Instálalo desde:")
        print("   https://github.com/UB-Mannheim/tesseract/wiki  (marca el idioma Spanish)")
        return False


if __name__ == "__main__":
    if not _verificar_tesseract():
        sys.exit(1)
    if len(sys.argv) == 2:
        print("\n----- TEXTO -----")
        print(leer_imagen(sys.argv[1]))
    elif len(sys.argv) == 3:
        procesar_carpeta(sys.argv[1], sys.argv[2])
    else:
        print("Uso:\n  python ocr.py imagen.jpg\n"
              "  python ocr.py carpeta/ salida.csv")
