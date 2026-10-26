"""Integration with an ephemeral Neo4j service, NEVER the user's live data."""
import json
import os
import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"benchmark"))
from fraudrag_v2 import generate
from neo4j_snapshot import seed_reference, get_as_of_reference, assert_no_label_leakage


def main():
    from neo4j import GraphDatabase
    url=os.getenv("NEO4J_URI","bolt://localhost:7687")
    user=os.getenv("NEO4J_USER","neo4j")
    password=os.environ["NEO4J_PASSWORD"]
    rows=generate(12,20261026)
    refs={r["customer_group"]:(json.loads(r["graph_reference_json"]),r["submission_date"])
          for r in rows}
    with GraphDatabase.driver(url,auth=(user,password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            for cid,(ref,_) in refs.items():
                session.execute_write(seed_reference,cid,ref)
            for cid,(expected,submission_date) in refs.items():
                result=session.execute_read(get_as_of_reference,cid,submission_date)
                assert result==expected
                assert_no_label_leakage(result)
                # A future-dated reference must not enter past evidence.
                past=expected["recorded_at"]
                past_query=session.execute_read(get_as_of_reference,cid,past)
                assert past_query is None
            # Seed a new future snapshot: a test that query drops it.
            cid,(expected,submission_date)=next(iter(refs.items()))
            later=dict(expected)
            later["source"]=expected["source"]+"/later"
            later["recorded_at"]=(date.fromisoformat(submission_date)+timedelta(days=2)).isoformat()
            session.execute_write(seed_reference,cid,later)
            still=session.execute_read(get_as_of_reference,cid,submission_date)
            assert still==expected
    print("PASS: 12 authoritative snapshots, temporal as-of filters, source provenance and no labels")

if __name__=="__main__":
    main()
