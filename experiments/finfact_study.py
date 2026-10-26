"""Fin-Fact financial CLAIM verification study; NOT statement forgery or FraudRAG-2400."""
import argparse
import csv
import hashlib
import json
import os
import re
import urllib.request
from collections import Counter
from pathlib import Path

REV = "b30387813734d4b461e6fcdd576feb819cc0bcbd"
SOURCE = "https://raw.githubusercontent.com/IIT-DM/Fin-Fact/" + REV + "/finfact.json"
LABELS = ["false", "neutral", "true"]

def normalize_label(label):
    label = str(label).strip().lower().replace("_", " ").replace("-", " ")
    if label in ("true", "false"):
        return label
    if label in ("neutral", "not enough information", "nei", "unknown"):
        return "neutral"
    return None

def load(path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(SOURCE, headers={"User-Agent": "FraudRAG-academic-benchmark"})
        with urllib.request.urlopen(req, timeout=180) as res, path.open("wb") as dest:
            while chunk := res.read(1024 * 1024):
                dest.write(chunk)
    raw = path.read_bytes()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Unexpected Fin-Fact format: expected JSON array")
    rows = []
    for d in data:
        label = normalize_label(d.get("label"))
        claim = str(d.get("claim") or "").strip()
        if label and claim:
            url = str(d.get("url") or "").strip().lower().split("#")[0]
            group = url or re.sub(r"\s+", " ", claim.casefold())
            rows.append({"claim": claim, "label": label, "group": group})
    if len(rows) < 100:
        raise ValueError("Too few labeled records after validation")
    provenance = {"source": SOURCE, "sha256": hashlib.sha256(raw).hexdigest(),
                  "n": len(rows), "labels": dict(Counter(r["label"] for r in rows))}
    return rows, provenance

def split(rows):
    from sklearn.model_selection import GroupShuffleSplit
    splitter = GroupShuffleSplit(test_size=0.25, n_splits=1, random_state=42)
    tr, te = next(splitter.split(rows, groups=[r["group"] for r in rows]))
    train, test = [rows[i] for i in tr], [rows[i] for i in te]
    assert set(r["group"] for r in train).isdisjoint(r["group"] for r in test)
    return train, test

def metrics(y, predicted):
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    return {"n": len(y), "accuracy": accuracy_score(y, predicted),
            "macro_f1": f1_score(y, predicted, labels=LABELS, average="macro", zero_division=0),
            "weighted_f1": f1_score(y, predicted, labels=LABELS, average="weighted", zero_division=0),
            "confusion_labels": LABELS,
            "confusion_matrix": confusion_matrix(y, predicted, labels=LABELS).tolist()}

def evaluate_baselines(train, test):
    from sklearn.dummy import DummyClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    xtrain = [r["claim"] for r in train]
    ytrain = [r["label"] for r in train]
    xtest = [r["claim"] for r in test]
    ytest = [r["label"] for r in test]
    dumb = DummyClassifier(strategy="most_frequent").fit([[0]] * len(train), ytrain)
    majority = dumb.predict([[0]] * len(test)).tolist()
    clf = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                        LogisticRegression(class_weight="balanced", random_state=42, max_iter=1200))
    clf.fit(xtrain, ytrain)
    pred = clf.predict(xtest).tolist()
    return {"majority": metrics(ytest, majority),
            "tfidf_logreg_claim_only": metrics(ytest, pred)}, pred

def llm_request(claim, provider, model):
    # No user secrets are read from the repository. Requires caller-supplied env keys.
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": "Bearer " + str(key)}
        payload = {"model": model, "temperature": 0,
                   "messages": [{"role": "system", "content":
                       "Label this financial claim true, false, or neutral if insufficient evidence. Return only the label."},
                       {"role": "user", "content": claim}]}
    else:
        key = os.environ.get("ANTHROPIC_API_KEY")
        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": str(key), "anthropic-version": "2023-06-01"}
        payload = {"model": model, "max_tokens": 30, "temperature": 0,
                   "system": "Label financial claims true, false, or neutral if insufficient evidence. Return only the label.",
                   "messages": [{"role": "user", "content": claim}]}
    if not key:
        raise RuntimeError("LLM API key not configured")
    headers["Content-Type"] = "application/json"
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=120) as res:
        obj = json.load(res)
    response = obj["choices"][0]["message"]["content"] if provider == "openai" else obj["content"][0]["text"]
    match = re.search(r"\b(true|false|neutral)\b", response.lower())
    return match.group(1) if match else None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["baseline", "llm"], default="baseline")
    p.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--data", default="data/external/finfact.json")
    p.add_argument("--output", default="artifacts/finfact")
    args = p.parse_args()
    if args.mode == "llm" and not os.getenv(args.provider.upper() + "_API_KEY"):
        raise SystemExit("Missing API credential. No LLM inference or charges occurred.")
    rows, provenance = load(Path(args.data))
    train, test = split(rows)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    result = {"dataset": provenance, "split": "grouped source-URL 75/25, seed 42",
              "train_n": len(train), "test_n": len(test),
              "scope": "financial fact-checking claims, NOT bank-statement fraud",
              "is_fraudrag_manuscript_result": False}
    if args.mode == "baseline":
        result["baselines"], pred = evaluate_baselines(train, test)
        sample = test
    else:
        sample = test[:args.limit]
        pred = []
        for i, row in enumerate(sample):
            try:
                pred.append(llm_request(row["claim"], args.provider, args.model))
            except Exception as exc:
                print("LLM error at case", i, type(exc).__name__, flush=True)
                pred.append(None)
        valid = [i for i, v in enumerate(pred) if v is not None]
        summary = {"attempted": len(sample), "completed": len(valid),
                   "coverage": len(valid) / len(sample) if sample else 0,
                   "provider": args.provider, "model": args.model}
        if valid:
            summary.update(metrics([sample[i]["label"] for i in valid], [pred[i] for i in valid]))
        result["llm_claim_only"] = summary
    with (output / (args.mode + "_predictions.csv")).open("w", newline="", encoding="utf8") as f:
        writer = csv.writer(f)
        writer.writerow(["claim", "truth", "prediction"])
        writer.writerows((row["claim"], row["label"], p or "ABSTAIN")
                         for row, p in zip(sample, pred))
    (output / (args.mode + "_metrics.json")).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)

if __name__ == "__main__":
    main()
