"""Third-party REAL SEC-AAER-linked *firm-year* fraud baseline.

This is NOT bank-statement forgery, and not the synthetic FraudRAG-v2 task.
The data are provided publicly by the authors of Bao et al. (2020), Journal
of Accounting Research, DOI: 10.1111/1475-679X.12292.
Source contains Compustat-derived features: do not redistribute raw dataset
without determining rights; download only at experimental runtime.
"""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

SOURCE_COMMIT="2d10bc6c7ce18f5dea051a90d823546907abaa84"
SOURCE=f"https://raw.githubusercontent.com/JarFraud/FraudDetection/{SOURCE_COMMIT}/data_FraudDetection_JAR2020.csv"
# Raw accounting attributes, not fraud-event indicators, AAER disclosure, p_aaer,
# or firm identifier/date. Exclude data leakage from post-investigation labels.
ATTRIBUTES=("act","ap","at","ceq","che","cogs","csho","dlc","dltis",
            "dltt","dp","ib","invt","ivao","ivst","lct","lt","ni","ppegt",
            "pstk","re","rect","sale","sstk","txp","txt","xint","prcc_f")

def get_data(path):
    import pandas as pd
    path=Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"FraudRAG-independent-public-study"})
        with urllib.request.urlopen(req,timeout=180) as response, path.open("wb") as output:
            while chunk:=response.read(1024*1024):
                output.write(chunk)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    data=pd.read_csv(path,low_memory=False)
    data.columns=[str(x).strip().lower() for x in data.columns]
    necessary={"misstate","gvkey","fyear"}
    missing=necessary-set(data.columns)
    if missing:
        raise ValueError(f"Published data fields missing: {sorted(missing)}; fields: {list(data.columns)[:20]}")
    use=[x for x in ATTRIBUTES if x in data.columns]
    if len(use)<20:
        raise ValueError(f"Too few documented raw attributes: {len(use)}")
    data["misstate"]=pd.to_numeric(data["misstate"],errors="coerce")
    data["fyear"]=pd.to_numeric(data["fyear"],errors="coerce")
    data=data.loc[data["misstate"].isin([0,1]) & data["fyear"].notna()].copy()
    for feature in use:
        data[feature]=pd.to_numeric(data[feature],errors="coerce")
    data["gvkey"]=data["gvkey"].astype(str)
    return data,use,digest

def metrics(true,prob,threshold):
    from sklearn.metrics import (
        average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,
        balanced_accuracy_score,confusion_matrix
    )
    pred=(prob>=threshold).astype(int)
    result={
        "n":len(true),"n_positive":int(sum(true)),"prevalence":float(sum(true)/len(true)),
        "average_precision":float(average_precision_score(true,prob)),
        "roc_auc":float(roc_auc_score(true,prob)) if len(set(true))==2 else None,
        "precision":float(precision_score(true,pred,zero_division=0)),
        "recall":float(recall_score(true,pred,zero_division=0)),
        "f1":float(f1_score(true,pred,zero_division=0)),
        "balanced_accuracy":float(balanced_accuracy_score(true,pred)),
        "confusion_matrix_0_1":confusion_matrix(true,pred,labels=[0,1]).tolist(),
        "decision_threshold":float(threshold)
    }
    return result

def pipeline():
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    return make_pipeline(SimpleImputer(strategy="median",add_indicator=True),
                         StandardScaler(),
                         LogisticRegression(max_iter=1500,class_weight="balanced",random_state=42))

def fit_report(train,val,test,features,label):
    import numpy as np
    from sklearn.metrics import f1_score
    if min(len(train),len(val),len(test))<100:
        raise ValueError(f"Underpopulated split {label}: {len(train)}, {len(val)}, {len(test)}")
    for split in (train,val,test):
        if split["misstate"].nunique()!=2:
            raise ValueError(f"Split missing a fraud class: {label}")
    model=pipeline()
    model.fit(train[list(features)],train["misstate"].astype(int))
    val_prob=model.predict_proba(val[list(features)])[:,1]
    # Only select F1 threshold on validation, never on final held-out test.
    candidates=np.linspace(0.05,0.95,19)
    threshold=float(max(candidates,key=lambda x:f1_score(val["misstate"],
                     val_prob>=x,zero_division=0)))
    prediction=model.predict_proba(test[list(features)])[:,1]
    report={
        "split":label,
        "train":{"n":len(train),"positive":int(train["misstate"].sum())},
        "validation":{"n":len(val),"positive":int(val["misstate"].sum())},
        "test":metrics(test["misstate"].astype(int).to_numpy(),prediction,threshold),
        "majority_all_negative_accuracy":float(1-test["misstate"].mean()),
        "random_prevalence_expected_average_precision":float(test["misstate"].mean()),
        "model":"median-imputed scaled class-balanced logistic regression",
        "features":list(features),"label_source":"published SEC-AAER-derived misstate"
    }
    return report, prediction

def run(out="artifacts/external_aaer"):
    from sklearn.model_selection import GroupShuffleSplit
    import numpy as np
    import pandas as pd
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    data,features,digest=get_data(out/"source_aaer_firm_year.csv")
    # Protocol A: strict past-to-future time split
    temporal=data.loc[data["fyear"]<=2014].copy()
    train=temporal.loc[temporal["fyear"]<=2004]
    val=temporal.loc[(temporal["fyear"]>=2005)&(temporal["fyear"]<=2008)]
    test=temporal.loc[temporal["fyear"]>=2009]
    temporal_result,_=fit_report(train,val,test,features,"time-ordered: 1991-2004 / 2005-2008 / 2009-2014")
    # Protocol B: entity-disjoint; train and validation further split by firm
    splitter=GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=42)
    tr_idx,te_idx=next(splitter.split(data,groups=data["gvkey"]))
    pre=data.iloc[tr_idx]
    te=data.iloc[te_idx]
    splitter2=GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=43)
    tr2,va2=next(splitter2.split(pre,groups=pre["gvkey"]))
    train2=pre.iloc[tr2];val2=pre.iloc[va2]
    assert set(train2["gvkey"]).isdisjoint(te["gvkey"])
    assert set(val2["gvkey"]).isdisjoint(te["gvkey"])
    assert set(train2["gvkey"]).isdisjoint(val2["gvkey"])
    disjoint_result,_=fit_report(train2,val2,te,features,"company-isolated, random group holdout seed 42")
    result={
        "source":SOURCE,"sha256":digest,"total_labeled_rows":len(data),
        "task":"firm-year accounting misstatement detection, NOT submitted bank-document forgery",
        "real_sec_enforcement_linked_outcomes":True,
        "not_fraudrag_v2_labels":True,
        "publication":"Bao et al., Journal of Accounting Research (2020), DOI 10.1111/1475-679X.12292",
        "source_redistribution":"Raw downloaded CSV is not committed or redistributed; license not independently established",
        "temporal":temporal_result,"entity_disjoint":disjoint_result,
        "limitations":["enforcement-based labels may miss uninvestigated cases",
                       "financial features obtained from Compustat derived processed data",
                       "not a statement forgery task; no text/images/Neo4j/Chroma/GPT evaluated",
                       "temporal evaluation may retain firms across years; entity-disjoint may use later years in training",
                       "model metrics are not evidence about FraudRAG document consistency detector"]}
    (out/"independent_aaer_metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    # Do not upload/commit raw external data, only metrics/provenance.
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="artifacts/external_aaer")
    a=p.parse_args()
    run(a.out)

if __name__=="__main__":
    main()
