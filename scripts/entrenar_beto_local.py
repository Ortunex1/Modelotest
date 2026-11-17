"""
Entrena BETO localmente (CPU) sobre las particiones ya armadas.
Pensado para correr en una PC sin GPU: usa max_length corto (mensajes cortos) para acelerar.

Lee:   data/anonimizado/particiones/corpus_train_solo_real.csv (o corpus_train.csv si USAR_AUMENTO) y corpus_val.csv
Guarda: modelos/beto_final/  (modelo + tokenizer)
        resultados/02_texto_val_pred.csv  (predicciones de validación)

Uso: python scripts/entrenar_beto_local.py
"""
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter

import torch
from torch.utils.data import Dataset
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import (classification_report, f1_score, accuracy_score,
                             precision_recall_fscore_support)

SEED = 42
MAX_LEN = 64          # mensajes cortos -> 64 tokens sobran, acelera en CPU
EPOCAS = 4
CKPT = 'dccuchile/bert-base-spanish-wwm-cased'
ETIQUETAS = ['legitimo', 'fraudulento']
lab2id = {l: i for i, l in enumerate(ETIQUETAS)}

np.random.seed(SEED); torch.manual_seed(SEED)
PART = Path('data/anonimizado/particiones')
import sys
USAR_AUMENTO = '--aumento' in sys.argv   # python entrenar_beto_local.py [--aumento]
SUF = '_aumento' if USAR_AUMENTO else '_solo_real'   # cada experimento guarda sus propios archivos
print('Experimento:', 'reales + aumento' if USAR_AUMENTO else 'solo reales')
MODELOS = Path('modelos'); MODELOS.mkdir(exist_ok=True)
RES = Path('resultados'); RES.mkdir(exist_ok=True)

train = pd.read_csv(PART / ('corpus_train.csv' if USAR_AUMENTO else 'corpus_train_solo_real.csv'))[['texto', 'etiqueta']].dropna()
val = pd.read_csv(PART / 'corpus_val.csv')[['texto', 'etiqueta']].dropna()
print(f'train={len(train)}  val={len(val)}')
print('Train:', train['etiqueta'].value_counts().to_dict(), '| Val:', val['etiqueta'].value_counts().to_dict())

# ---------- Baseline clásico (el rival) ----------
base = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1),
                     LogisticRegression(max_iter=1000, class_weight='balanced'))
base.fit(train['texto'], train['etiqueta'])
pred_base = base.predict(val['texto'])
f1_base = f1_score(val['etiqueta'], pred_base, pos_label='fraudulento', zero_division=0)
print(f'\n[BASELINE] F1(fraude) = {f1_base:.3f}')
print(classification_report(val['etiqueta'], pred_base, digits=3, zero_division=0))

# ---------- BETO ----------
tok = AutoTokenizer.from_pretrained(CKPT)

class DS(Dataset):
    def __init__(self, textos, etiquetas):
        self.enc = tok(list(textos), truncation=True, padding=True, max_length=MAX_LEN)
        self.labels = [lab2id[e] for e in etiquetas]
    def __len__(self): return len(self.labels)
    def __getitem__(self, i):
        item = {k: torch.tensor(v[i]) for k, v in self.enc.items()}
        item['labels'] = torch.tensor(self.labels[i]); return item

ds_tr, ds_val = DS(train['texto'], train['etiqueta']), DS(val['texto'], val['etiqueta'])

cnt = Counter(train['etiqueta']); tot = sum(cnt.values())
pesos = torch.tensor([tot / (2 * cnt[l]) for l in ETIQUETAS], dtype=torch.float)

class TrainerPond(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop('labels')
        out = model(**inputs)
        loss = torch.nn.CrossEntropyLoss(weight=pesos.to(model.device))(out.logits, labels)
        return (loss, out) if return_outputs else loss

def metricas(pred):
    logits = pred.predictions[0] if isinstance(pred.predictions, tuple) else pred.predictions
    preds = np.argmax(logits, axis=1)
    p, r, f1, _ = precision_recall_fscore_support(pred.label_ids, preds, labels=[0, 1],
                                                  average=None, zero_division=0)
    return {'accuracy': accuracy_score(pred.label_ids, preds), 'f1_fraudulento': f1[1],
            'recall_fraudulento': r[1], 'precision_fraudulento': p[1]}

modelo = AutoModelForSequenceClassification.from_pretrained(
    CKPT, num_labels=2, id2label={i: l for l, i in lab2id.items()}, label2id=lab2id)

args = TrainingArguments(
    output_dir=str(MODELOS / f'beto_ckpt{SUF}'),
    num_train_epochs=EPOCAS, learning_rate=2e-5,
    per_device_train_batch_size=16, per_device_eval_batch_size=32,
    eval_strategy='epoch', save_strategy='epoch', save_total_limit=1,
    load_best_model_at_end=True, metric_for_best_model='f1_fraudulento',
    seed=SEED, logging_steps=20, report_to='none')

trainer = TrainerPond(model=modelo, args=args, train_dataset=ds_tr,
                      eval_dataset=ds_val, compute_metrics=metricas)
print('\n[BETO] Entrenando (CPU, puede tardar)...')
trainer.train()

res = trainer.evaluate()
f1_beto = res['eval_f1_fraudulento']
print(f'\n===== RESULTADO =====')
print(f'BETO     F1(fraude) = {f1_beto:.3f}')
print(f'Baseline F1(fraude) = {f1_base:.3f}')
print('BETO GANA al baseline' if f1_beto > f1_base else 'El baseline no fue superado')

trainer.save_model(str(MODELOS / f'beto_final{SUF}'))
tok.save_pretrained(str(MODELOS / f'beto_final{SUF}'))
logits = trainer.predict(ds_val).predictions
logits = logits[0] if isinstance(logits, tuple) else logits
pred_beto = [ETIQUETAS[i] for i in np.argmax(logits, axis=1)]
pd.DataFrame({'texto': val['texto'].values, 'y_real': val['etiqueta'].values,
             'pred_beto': pred_beto, 'pred_baseline': pred_base}).to_csv(
    RES / f'02_texto_val_pred{SUF}.csv', index=False)
print(f'\nModelo en modelos/beto_final{SUF}/  |  predicciones en resultados/02_texto_val_pred{SUF}.csv')
