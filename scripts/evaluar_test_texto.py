"""
Evaluación FINAL del motor de texto sobre el TEST (se abre una sola vez).

Compara BETO (modelo guardado) contra la línea base clásica (TF-IDF + LogReg), entrenados con
los MISMOS datos del experimento, sobre los MISMOS 89 mensajes reales de test:
  - exactitud, precisión, recall, F1 (clase fraudulento) y AUC-ROC
  - matriz de confusión
  - prueba de McNemar (exacta): su valor p decide la hipótesis
  - criterio técnico F1 >= 0.90

Lee:    data/anonimizado/particiones/corpus_train[_solo_real].csv, corpus_test.csv
        modelos/beto_final_<exp>/
Guarda: resultados/03_texto_test_pred_<exp>.csv   (texto, real, predicciones y probabilidades)
        resultados/03_texto_test_metricas_<exp>.txt

Uso: python scripts/evaluar_test_texto.py [--aumento]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.pipeline import make_pipeline
from statsmodels.stats.contingency_tables import mcnemar
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SEED = 42
MAX_LEN = 64            # igual que en el entrenamiento local
F1_MINIMO = 0.90
CLASES = ['legitimo', 'fraudulento']

USAR_AUMENTO = '--aumento' in sys.argv
EXP = 'aumento' if USAR_AUMENTO else 'solo_real'
PART = Path('data/anonimizado/particiones')
MODELO = Path('modelos') / f'beto_final_{EXP}'
RES = Path('resultados'); RES.mkdir(exist_ok=True)

train = pd.read_csv(PART / ('corpus_train.csv' if USAR_AUMENTO else 'corpus_train_solo_real.csv'))
test = pd.read_csv(PART / 'corpus_test.csv')
y = test['etiqueta'].values
y_bin = (y == 'fraudulento').astype(int)

# ---------- Línea base (mismos datos de entrenamiento) ----------
base = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1),
                     LogisticRegression(max_iter=1000, class_weight='balanced'))
base.fit(train['texto'], train['etiqueta'])
pred_base = base.predict(test['texto'])
prob_base = base.predict_proba(test['texto'])[:, list(base.classes_).index('fraudulento')]

# ---------- BETO (modelo guardado) ----------
tok = AutoTokenizer.from_pretrained(MODELO)
modelo = AutoModelForSequenceClassification.from_pretrained(MODELO).eval()
enc = tok(list(test['texto']), truncation=True, padding=True, max_length=MAX_LEN, return_tensors='pt')
with torch.no_grad():
    logits = modelo(**enc).logits
prob_beto = torch.softmax(logits, dim=1)[:, 1].numpy()
pred_beto = np.array([CLASES[i] for i in logits.argmax(dim=1).numpy()])


def metricas(pred, prob):
    kw = dict(pos_label='fraudulento', zero_division=0)
    return {'exactitud': accuracy_score(y, pred), 'precision': precision_score(y, pred, **kw),
            'recall': recall_score(y, pred, **kw), 'f1': f1_score(y, pred, **kw),
            'auc': roc_auc_score(y_bin, prob)}


m_beto, m_base = metricas(pred_beto, prob_beto), metricas(pred_base, prob_base)
ok_b, ok_c = pred_beto == y, pred_base == y
tabla = [[int((ok_b & ok_c).sum()), int((ok_b & ~ok_c).sum())],
         [int((~ok_b & ok_c).sum()), int((~ok_b & ~ok_c).sum())]]
p = mcnemar(tabla, exact=True).pvalue

lineas = [
    f'EVALUACIÓN FINAL EN TEST — motor de texto — experimento: {EXP}',
    f'test = {len(test)} mensajes reales {dict(pd.Series(y).value_counts())} | train = {len(train)}',
    '',
    f'{"métrica":<10}{"BETO":>8}{"baseline":>10}',
    *[f'{k:<10}{m_beto[k]:>8.3f}{m_base[k]:>10.3f}' for k in m_beto],
    '',
    'Matriz de confusión (filas = real [legitimo, fraudulento], columnas = predicción)',
    f'  BETO    : {confusion_matrix(y, pred_beto, labels=CLASES).tolist()}',
    f'  baseline: {confusion_matrix(y, pred_base, labels=CLASES).tolist()}',
    '',
    'McNemar (exacta)',
    f'  aciertan ambos={tabla[0][0]}  solo BETO={tabla[0][1]}  solo baseline={tabla[1][0]}  fallan ambos={tabla[1][1]}',
    f'  p = {p:.5f}  ->  ' + ('diferencia SIGNIFICATIVA (p < 0.05)' if p < 0.05 else 'diferencia NO significativa (p >= 0.05)'),
    '',
    f'Criterio técnico F1 >= {F1_MINIMO}: BETO {"CUMPLE" if m_beto["f1"] >= F1_MINIMO else "NO cumple"} '
    f'({m_beto["f1"]:.3f})',
]
informe = '\n'.join(lineas)
print(informe)
(RES / f'03_texto_test_metricas_{EXP}.txt').write_text(informe, encoding='utf-8')
pd.DataFrame({'texto': test['texto'], 'y_real': y, 'pred_beto': pred_beto, 'prob_beto': prob_beto.round(4),
              'pred_baseline': pred_base, 'prob_baseline': prob_base.round(4)}).to_csv(
    RES / f'03_texto_test_pred_{EXP}.csv', index=False, encoding='utf-8')
print(f'\nGuardado: resultados/03_texto_test_pred_{EXP}.csv y 03_texto_test_metricas_{EXP}.txt')
