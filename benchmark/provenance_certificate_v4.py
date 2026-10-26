"""FraudRAG V4 RESEARCH PROTOTYPE: source-conditional verification certificates.

Only checks *differences and consistency against independently ATTESTED
references*. This code DOES NOT authenticate bank issuers, cryptographically
verify signatures, adjudicate fraud, or make any production authenticity claim.

Use as a falsification target for fair deterministic comparators, not as
demonstration of a novel outperforming GraphRAG algorithm.

No LLM required. Timestamps must be timezone-aware ISO 8601.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

DIFFERENCE="DIFFERENCE_PROVEN"
MATCH="MATCH_SUPPORTED"
CONFLICT="EVIDENCE_CONFLICT"
INSUFFICIENT="INSUFFICIENT_EVIDENCE"
UNTRUSTED="SOURCE_UNTRUSTED_OR_STALE"

def timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("An ISO-8601 timezone-aware timestamp is required")
    dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("A timezone offset is required; naive datetime is not permitted")
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class Claim:
    key: str
    value: str

@dataclass(frozen=True)
class Reference:
    source_id: str
    source_family: str
    key: str
    value: str
    valid_from: str
    valid_until: str
    recorded_at: str
    ingested_at: str
    issuer_attested: bool
    completeness_attested_for_key: bool
    # For production, the source registry must independently verify issuer
    # identity and document digest; boolean alone is NOT cryptographic proof.
    source_digest_sha256: str

def from_row(row: Mapping[str, Any]) -> Reference:
    required=Reference.__dataclass_fields__.keys()
    unknown=set(row)-set(required)
    if unknown:
        raise ValueError(f"Unsupported evidence fields: {sorted(unknown)}")
    return Reference(**{key:row[key] for key in required})

def reference_admissible(
    ref: Reference, key: str, effective_at: datetime, cutoff: datetime
) -> tuple[bool, str]:
    if ref.key != key:
        return False,"different_field"
    if not ref.issuer_attested:
        return False,"issuer_not_attested"
    if ref.source_family in ("submitted-document","user-upload","same-user-upload"):
        return False,"submitted_document_is_not_independent_reference"
    if not (isinstance(ref.source_digest_sha256,str)
            and len(ref.source_digest_sha256)==64
            and all(c in "0123456789abcdef" for c in ref.source_digest_sha256)):
        return False,"source_digest_missing_or_malformed"
    if not ref.source_id.strip() or not ref.source_family.strip():
        return False,"source_identity_missing"
    begin=timestamp(ref.valid_from)
    end=timestamp(ref.valid_until)
    observed=timestamp(ref.recorded_at)
    ingested=timestamp(ref.ingested_at)
    if not begin < end:
        return False,"invalid_validity_interval"
    if observed > cutoff or ingested > cutoff:
        return False,"future_evidence_not_known_at_cutoff"
    if not (begin <= effective_at < end):
        return False,"record_not_valid_at_claim_time"
    return True,"accepted_source_attestation_assumption"

def verify(
    claims: Sequence[Claim],
    references: Sequence[Reference],
    *,
    effective_at: str,
    as_of_cutoff: str,
) -> dict[str, Any]:
    at=timestamp(effective_at)
    cutoff=timestamp(as_of_cutoff)
    if cutoff < at:
        raise ValueError("Knowledge cutoff cannot predate the statement effective instant")
    if not claims:
        raise ValueError("At least one required document claim is necessary")
    if len({c.key for c in claims})!=len(claims):
        raise ValueError("Duplicate claim field keys are not allowed")
    if any(not c.key.strip() for c in claims):
        raise ValueError("Claim keys must be non-empty")
    outcome={}
    source_payload=[]
    for claim in sorted(claims,key=lambda x:x.key):
        valid=[]
        rejected=[]
        for ref in references:
            ok,reason=reference_admissible(ref,claim.key,at,cutoff)
            if ok:valid.append(ref)
            elif ref.key==claim.key:
                rejected.append({"source_id":ref.source_id,"reason":reason})
        witness_ids=sorted({r.source_id for r in valid})
        families=sorted({r.source_family for r in valid})
        values=sorted({r.value for r in valid})
        if len(values)>1:
            status=CONFLICT
            # No general ability to resolve independently attested conflict
            # without an externally authorized priority policy.
        elif len(values)==1:
            if values[0]!=claim.value:
                status=DIFFERENCE
            elif any(r.completeness_attested_for_key for r in valid):
                status=MATCH
            else:
                status=INSUFFICIENT
        elif rejected:
            status=UNTRUSTED
        else:
            status=INSUFFICIENT
        outcome[claim.key]={
            "status":status,
            "witness_source_ids":witness_ids,
            "distinct_source_families":families,
            "rejected_sources":rejected,
            "issuer_attestation_not_cryptographically_checked":True,
            "completeness_attested_by_source_ids":sorted({
                r.source_id for r in valid if r.completeness_attested_for_key
            }),
        }
        for ref in valid:
            source_payload.append({
                "key":ref.key,"value":ref.value,
                "source_id":ref.source_id,"family":ref.source_family,
                "valid_from":ref.valid_from,"valid_until":ref.valid_until,
                "recorded_at":ref.recorded_at,"ingested_at":ref.ingested_at,
                "digest":ref.source_digest_sha256,
                "complete":ref.completeness_attested_for_key,
            })
    statuses={field["status"] for field in outcome.values()}
    if CONFLICT in statuses:
        doc_status=CONFLICT
    elif DIFFERENCE in statuses:
        doc_status=DIFFERENCE
    elif statuses=={MATCH}:
        doc_status=MATCH
    elif UNTRUSTED in statuses:
        doc_status=UNTRUSTED
    else:
        doc_status=INSUFFICIENT
    canonical={
        "effective_at":at.isoformat(),
        "as_of_cutoff":cutoff.isoformat(),
        "claims":sorted([asdict(x) for x in claims],key=lambda x:x["key"]),
        "accepted_sources":sorted(source_payload,key=lambda x:(x["key"],x["source_id"],x["value"])),
        "field_results":outcome,
        "document_status":doc_status
    }
    envelope_hash=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "scope":"synthetic-research conditional record-consistency; NOT real bank document authentication",
        "document_status":doc_status,
        "field_results":outcome,
        "unresolved_fields":sorted(k for k,v in outcome.items() if v["status"] not in (MATCH,DIFFERENCE)),
        "basis_sha256":envelope_hash,
        "as_of_cutoff":cutoff.isoformat(),
        "preconditions":{
            "source_issuer_attestation_supplied_not_verified_by_code":True,
            "source_digest_format_checked_not_matched_to_external_bytes":True,
            "evidence_independence_based_on_source_family_metadata":True,
            "no_real_fraud_inference":True
        }
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--case",required=True,help="Path to synthetic fixture JSON, never a confidential original bank record")
    a=p.parse_args()
    source=json.loads(open(a.case,encoding="utf8").read())
    out=verify(
        [Claim(**item) for item in source["claims"]],
        [from_row(item) for item in source["references"]],
        effective_at=source["effective_at"],as_of_cutoff=source["as_of_cutoff"]
    )
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":main()
