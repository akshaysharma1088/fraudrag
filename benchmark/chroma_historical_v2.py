"""A real Chroma in-memory index of trusted historical synthetic bank evidence.

This is a standalone integration experiment, not the same retriever used in
the initial GPT study. Uses deterministic local feature hashing as embeddings
rather than falsely attributing embeddings to OpenAI or Anthropic.
"""
from __future__ import annotations
import json
from datetime import date

def verify_historical_record(row):
    if "fraud_label" in row["historical_vector_corpus_text"]:
        raise ValueError("target label leakage detected")
    ref=row.get("graph_reference") or json.loads(row["graph_reference_json"])
    if date.fromisoformat(ref["recorded_at"])>=date.fromisoformat(row["submission_date"]):
        raise ValueError("historical record timestamp is not before submission")
    return ref

def build_index(rows):
    import chromadb
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.preprocessing import normalize
    by_group={}
    for row in rows:
        verify_historical_record(row)
        by_group.setdefault(row["customer_group"],row)
    records=[by_group[k] for k in sorted(by_group)]
    vectorizer=HashingVectorizer(n_features=256,alternate_sign=False,norm="l2")
    docs=[r["historical_vector_corpus_text"] for r in records]
    embeddings=vectorizer.transform(docs).toarray().astype(float).tolist()
    client=chromadb.EphemeralClient()
    collection=client.get_or_create_collection(
        name="fraudrag_v2_history",
        embedding_function=None,
        metadata={"purpose":"past_only_unlabeled_synthetic_historical_evidence"})
    collection.add(
        ids=[f"history-{r['customer_group']}" for r in records],
        documents=docs,
        metadatas=[{
            "customer_group":r["customer_group"],
            "recorded_at":(r.get("graph_reference") or json.loads(r["graph_reference_json"]))["recorded_at"],
            "trusted_source_id":"history://"+r["customer_group"]
        } for r in records],
        embeddings=embeddings
    )
    return client,collection,vectorizer

def get_retrieval(collection,vectorizer,row,k=3):
    # Request all candidates then filter as-of-date, intentionally enforcing
    # no future evidence entering GPT context independent of Chroma query syntax.
    vector=vectorizer.transform([row["statement_text"]]).toarray()[0].astype(float).tolist()
    result=collection.query(query_embeddings=[vector],n_results=collection.count(),
                            include=["documents","metadatas","distances"])
    valid=[]
    for idx,meta in enumerate(result["metadatas"][0]):
        if meta["recorded_at"] >= row["submission_date"]:
            continue
        valid.append({
            "id":meta["trusted_source_id"],
            "recorded_at":meta["recorded_at"],
            "text":result["documents"][0][idx],
            "distance":float(result["distances"][0][idx])
        })
        if len(valid)>=k: break
    return valid
