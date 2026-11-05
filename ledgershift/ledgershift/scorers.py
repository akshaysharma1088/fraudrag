"""Learned payee matchers: embedding similarity and a fine-tuned cross-encoder (Ditto-style).

These run in CI (they need model downloads); the outputs are score caches that
the deterministic verifiers read, so every method still decides through the
same contract and every threshold is tuned on dev only.

  python -m ledgershift.scorers pairs            # payee-pair sets for training and evaluation
  python -m ledgershift.scorers train            # fine-tune the cross-encoder on dev-payee pairs
  python -m ledgershift.scorers score            # score every pair the linkers will ask about

Training data for the cross-encoder comes only from v2 dev payees, excluding
any family that appears in the v1 catalogue, so the same model can be tested on
v1 and on v2 test without having seen a test payee or its siblings.
"""
from __future__ import annotations

import gzip
import json
import random
import sys
from pathlib import Path

from . import verify as V
from .catalogue_v2 import MERCHANTS_V2
from .generator import MERCHANTS as MERCHANTS_V1, _ocr, read_jsonl
from .generator_v2 import _descriptor, catalogue

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results_scorers"
EMBED_MODELS = {"embed_minilm": "sentence-transformers/all-MiniLM-L6-v2", "embed_bge": "BAAI/bge-small-en-v1.5"}
CE_BASE = "distilroberta-base"
V1_FAMILIES = {m[3] for m in MERCHANTS_V1} | {"square"}     # Cash App is a Square product in v2


# ---------------- payee-pair sets ----------------
def payee_pairs(merchants, seed, n_pos=3, ocr=True):
    """(statement name, ledger descriptor, label, kind) for every payee in ``merchants``."""
    rng = random.Random(seed)
    rows = []
    for name, tmpls, kind, fam in merchants:
        sib = [m for m in merchants if m[3] == fam and m[0] != name]
        same = [m for m in merchants if m[2] == kind and m[3] != fam]
        other = [m for m in merchants if m[2] != kind]
        for k in range(n_pos):
            shown = _ocr(rng, name, 0.12) if (ocr and k == n_pos - 1) else name
            rows.append({"name": shown, "descriptor": _descriptor(rng, tmpls), "label": 1, "kind": "positive", "payee": name})
        for m in rng.sample(sib, k=min(2, len(sib))):
            rows.append({"name": name, "descriptor": _descriptor(rng, m[1]), "label": 0, "kind": "sibling", "payee": name})
        if same:
            rows.append({"name": name, "descriptor": _descriptor(rng, rng.choice(same)[1]), "label": 0, "kind": "same_kind", "payee": name})
        rows.append({"name": name, "descriptor": _descriptor(rng, rng.choice(other)[1]), "label": 0, "kind": "random", "payee": name})
    return rows


def write_jsonl(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def make_pairs():
    dev, test = catalogue("dev"), catalogue("test")
    train = [m for m in dev if m[3] not in V1_FAMILIES]
    write_jsonl(payee_pairs(dev, 1), OUT / "pairs_v2_dev.jsonl")                 # threshold tuning for pair evaluation
    write_jsonl(payee_pairs(test, 2), OUT / "pairs_v2_test.jsonl")               # pair evaluation
    # training set: many draws per payee, plus identical-text positives (the clean condition)
    rows = []
    for s in range(12):
        rows += payee_pairs(train, 100 + s)
    rows += [{"name": m[0], "descriptor": m[0], "label": 1, "kind": "identical", "payee": m[0]} for m in train]
    write_jsonl(rows, OUT / "pairs_train.jsonl")
    info = {"train_payees": len(train), "train_pairs": len(rows), "dev_payees": len(dev), "test_payees": len(test),
            "excluded_families": sorted(V1_FAMILIES & {m[3] for m in dev})}
    (OUT / "pairs_info.json").write_text(json.dumps(info, indent=2))
    print(info)


# ---------------- which pairs will the linkers ask about? ----------------
def requested_pairs(paths):
    """Run the deterministic linker with a recording similarity function to collect exactly the
    (statement text, ledger descriptor) pairs any linker will score."""
    seen = set()

    def rec(a, b):
        seen.add((a, b)); return 0.0
    V.EXTERNAL_SIM["__record__"] = rec
    for p in paths:
        for inst in read_jsonl(p):
            V.deterministic_links(inst, "__record__", t=0.0, repair=True)
    del V.EXTERNAL_SIM["__record__"]
    return sorted(seen)


def bench_paths():
    out = []
    for d in ("data", "data_v2"):
        for s in ("dev", "test"):
            p = ROOT / d / f"{s}.jsonl"
            if p.exists():
                out.append(p)
    return out


# ---------------- models ----------------
def train_cross_encoder(epochs=3, batch=32, seed=7):
    import torch
    from sentence_transformers import CrossEncoder, InputExample
    from torch.utils.data import DataLoader
    random.seed(seed); torch.manual_seed(seed)
    rows = read_jsonl(OUT / "pairs_train.jsonl")
    ex = [InputExample(texts=[r["name"], r["descriptor"]], label=float(r["label"])) for r in rows]
    model = CrossEncoder(CE_BASE, num_labels=1, max_length=48)
    loader = DataLoader(ex, shuffle=True, batch_size=batch)
    model.fit(train_dataloader=loader, epochs=epochs, warmup_steps=int(0.1 * len(loader) * epochs), show_progress_bar=False)
    model.save(str(OUT / "ditto_model"))
    print("trained on", len(ex), "pairs")


def score_all():
    import numpy as np
    from sentence_transformers import CrossEncoder, SentenceTransformer
    pairs = requested_pairs(bench_paths())
    eval_sets = {p.stem: read_jsonl(p) for p in sorted(OUT.glob("pairs_*.jsonl")) if p.stem != "pairs_train"}
    ext = ROOT / "external" / "foliome_pairs.jsonl"
    if ext.exists():
        eval_sets["pairs_foliome"] = read_jsonl(ext)
    allp = list(pairs) + [(r["name"], r["descriptor"]) for rows in eval_sets.values() for r in rows]
    allp = sorted(set(allp))
    print("unique pairs to score:", len(allp))
    scores = {}
    for key, name in EMBED_MODELS.items():
        m = SentenceTransformer(name)
        texts = sorted({t for ab in allp for t in ab})
        emb = m.encode(texts, batch_size=256, normalize_embeddings=True, show_progress_bar=False)
        idx = {t: i for i, t in enumerate(texts)}
        scores[key] = {f"{a}\t{b}": round(float(np.dot(emb[idx[a]], emb[idx[b]])), 4) for a, b in allp}
    ce = CrossEncoder(str(OUT / "ditto_model"), max_length=48)
    raw = ce.predict([[a, b] for a, b in allp], batch_size=256, show_progress_bar=False, apply_softmax=False)
    sig = 1 / (1 + np.exp(-np.asarray(raw, dtype=float)))
    scores["ditto"] = {f"{a}\t{b}": round(float(s), 4) for (a, b), s in zip(allp, sig)}
    for key, d in scores.items():
        with gzip.open(OUT / f"scores_{key}.json.gz", "wt") as f:
            json.dump(d, f)
    (OUT / "score_info.json").write_text(json.dumps({"n_linker_pairs": len(pairs), "n_scored": len(allp),
                                                     "models": {**EMBED_MODELS, "ditto": f"{CE_BASE} fine-tuned"},
                                                     "eval_sets": {k: len(v) for k, v in eval_sets.items()}}, indent=2))


# ---------------- used by the evaluation (no model download needed) ----------------
def load_scores(key, folder=OUT):
    with gzip.open(Path(folder) / f"scores_{key}.json.gz", "rt") as f:
        d = json.load(f)

    def simf(a, b):
        return d.get(f"{a}\t{b}", 0.0)
    return simf


if __name__ == "__main__":
    step = sys.argv[1]
    {"pairs": make_pairs, "train": train_cross_encoder, "score": score_all}[step]()
