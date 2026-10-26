"""Neo4j temporal evidence adapter for *synthetic* FraudRAG-v2 graph snapshots.

Standalone integration-test helper. The current paid GPT pilot consumes the
corresponding serialized bank reference, NOT this Neo4j adapter. No production
claims are warranted from this test.
"""
from __future__ import annotations

import json
from datetime import date

def seed_reference(tx, customer_id, ref):
    if not isinstance(ref,dict) or not ref.get("recorded_at"):
        raise ValueError("Expected documented synthetic bank reference")
    params={
        "cid":customer_id,
        "aid":f"{customer_id}:{ref['account']}",
        "recorded_at":ref["recorded_at"],
        "source":ref["source"],"institution":ref["institution"],
        "reference_json":json.dumps(ref,sort_keys=True)
    }
    tx.run("""
        MERGE (c:BenchCustomer {id:$cid})
        MERGE (a:BenchAccount {id:$aid})
        SET a.number=$aid
        MERGE (c)-[:OWNS]->(a)
        MERGE (r:BenchLedgerSnapshot {source:$source})
        SET r.recorded_at=$recorded_at, r.evidence_json=$reference_json
        MERGE (i:BenchInstitution {name:$institution})
        MERGE (a)-[:ISSUED_BY]->(i)
        MERGE (a)-[:HAS_LEDGER]->(r)
    """,**params).consume()


def get_as_of_reference(tx, customer_id, submission_date):
    # Avoid future-fact leakage, even if graph contains a later bank correction.
    if not isinstance(submission_date,str):
        raise ValueError("Expected YYYY-MM-DD submission date")
    _=date.fromisoformat(submission_date)
    result=tx.run("""
        MATCH (:BenchCustomer {id:$customer_id})-[:OWNS]->(:BenchAccount)
            -[:HAS_LEDGER]->(snap:BenchLedgerSnapshot)
        WHERE date(snap.recorded_at) < date($submission_date)
        RETURN snap.source AS source,
               snap.evidence_json AS evidence_json,
               snap.recorded_at AS recorded_at
        ORDER BY snap.recorded_at DESC
        LIMIT 1
    """,customer_id=customer_id,submission_date=submission_date)
    row=result.single()
    return json.loads(row["evidence_json"]) if row is not None else None


def assert_no_label_leakage(reference):
    if reference is None:
        return
    forbidden={"fraud_label","tamper_type","ground_truth_rule"}
    if forbidden.intersection(reference):
        raise AssertionError("Oracle label in time-filtered graph reference")
