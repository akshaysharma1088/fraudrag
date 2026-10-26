"""Fail-closed validation for independently labeled external research documents.

Does not infer that a dataset is authentic merely because files exist.
It validates integrity/provenance fields, group leakage, label independent
adjudication, rights, and temporal ordering. It cannot itself authenticate
permission contracts, identity, document truth, or independent review.

USAGE: python benchmark/external_evidence_gate.py --manifest path.json
       python benchmark/external_evidence_gate.py --manifest path.json --promotion

Never ingest or upload raw private bank documents to GitHub CI. The real-data
manifest and bytes must remain on an access-controlled, approved machine.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path, PurePosixPath

VERDICTS=("authentic","tampered","unknown")
VALID_TASKS=("bank_statement_authenticity","check_signature_authenticity",
             "document_image_tampering","synthetic_text_edit")
SAFE_SHA=re.compile(r"^[0-9a-f]{64}$")
SAFE_ID=re.compile(r"^[a-zA-Z0-9_-]{3,100}$")
REQUIRED_DATASET=("dataset_id","version","task","description","rights","files","split_policy",
                  "independent_annotation_protocol")
REQUIRED_RECORD=("sample_id","relative_path","sha256","document_group","source_institution_group",
                 "label","split","label_origin","reference_as_of_date","submission_date")
REQUIRED_RIGHTS=("license_or_permission_url","permitted_research_use","approval_reference",
                 "data_controller","third_party_redistribution_allowed")
SPLITS=("train","validation","test")

def problem(code, message, details=None):
    item={"code":code,"message":message}
    if details is not None:
        item["details"]=details
    return item

def safe_path(root: Path, relative: str):
    path=PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts or not relative:
        raise ValueError("Unsafe relative path")
    resolved=(root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("File would escape dataset root")
    return resolved

def assess(data: dict, root: Path, check_bytes: bool=True, promotion: bool=False):
    issues=[]
    for field in REQUIRED_DATASET:
        if field not in data:
            issues.append(problem("missing_dataset_field",f"Required: {field}"))
    if issues:
        return {"pass":False,"issues":issues}
    if data["task"] not in VALID_TASKS:
        issues.append(problem("unsupported_task",str(data["task"])))
    rights=data["rights"]
    for k in REQUIRED_RIGHTS:
        if not rights.get(k):
            issues.append(problem("missing_rights",k))
    if rights.get("permitted_research_use") not in ("noncommercial","commercial","both"):
        issues.append(problem("rights_scope_not_defined","Explicit legal scope required"))
    if rights.get("approval_reference") in ("pending","none","not_requested"):
        issues.append(problem("permission_not_granted","Approval must precede use"))
    if not isinstance(data["files"],list) or not data["files"]:
        issues.append(problem("no_external_files","No external document records"))
        return {"pass":False,"issues":issues}
    if data["split_policy"] != "source_document_group_disjoint":
        issues.append(problem("split_rule_invalid","Document groups must never cross train, validation and test"))
    seen=set()
    group_splits={}
    institution_splits={}
    labels=Counter()
    task=data["task"]
    for i,item in enumerate(data["files"]):
        prefix=f"files[{i}]"
        missing=[name for name in REQUIRED_RECORD if not item.get(name)]
        if missing:
            issues.append(problem("missing_file_fields",prefix,missing))
            continue
        sid=item["sample_id"]
        if not SAFE_ID.fullmatch(sid):
            issues.append(problem("bad_sample_id",prefix))
        if sid in seen:
            issues.append(problem("duplicate_sample_id",prefix))
        seen.add(sid)
        if item["split"] not in SPLITS:
            issues.append(problem("invalid_split",prefix))
        if item["label"] not in VERDICTS:
            issues.append(problem("invalid_label",prefix))
        labels[item["label"]]+=1
        gid=item["document_group"]
        group_splits.setdefault(gid,set()).add(item["split"])
        inst=item["source_institution_group"]
        institution_splits.setdefault(inst,set()).add(item["split"])
        if not SAFE_SHA.fullmatch(item["sha256"]):
            issues.append(problem("invalid_hash",prefix))
        else:
            try:
                f=safe_path(root,item["relative_path"])
                if check_bytes:
                    if not f.is_file():
                        issues.append(problem("missing_file",prefix))
                    elif hashlib.sha256(f.read_bytes()).hexdigest()!=item["sha256"]:
                        issues.append(problem("hash_mismatch",prefix))
            except ValueError:
                issues.append(problem("unsafe_path",prefix))
        try:
            if date.fromisoformat(item["reference_as_of_date"]) >= date.fromisoformat(item["submission_date"]):
                issues.append(problem("reference_temporal_leakage",prefix))
        except (TypeError,ValueError):
            issues.append(problem("invalid_temporal_fields",prefix))
        if not item["label_origin"] in ("human_independent_adjudication",
                                        "source_authentic_paired_original",
                                        "controlled_synthetic_edit",
                                        "publisher_signature_class"):
            issues.append(problem("unsupported_label_origin",prefix))
        if item["label"]=="tampered" and not item.get("label_evidence_id"):
            issues.append(problem("tamper_evidence_missing",prefix))
        if promotion and item["label_origin"]!="human_independent_adjudication":
            issues.append(problem("not_independently_adjudicated",prefix))
    for gid,splits in group_splits.items():
        if len(splits)>1:
            issues.append(problem("group_leakage",gid,sorted(splits)))
    if data.get("require_institution_holdout"):
        for inst,splits in institution_splits.items():
            if len(splits)>1:
                issues.append(problem("institution_leakage",inst,sorted(splits)))
    if promotion:
        if task!="bank_statement_authenticity":
            issues.append(problem("wrong_task_for_bank_fraud","Signature, receipt and synthetic-edit tasks cannot validate bank statement authenticity"))
        if not data.get("real_world_documents"):
            issues.append(problem("real_world_authenticity_unestablished","Generated originals are not real bank documents"))
        if not data.get("independent_annotation_protocol",{}).get("inter_rater_reconciliation_record"):
            issues.append(problem("annotation_review_missing","Independent blinded review and reconciliation document required"))
        if "authentic" not in labels or "tampered" not in labels:
            issues.append(problem("class_missing","Independent authentic and tampered cases both required"))
        if not data.get("ethics_and_privacy",{}).get("approval_reference"):
            issues.append(problem("ethics_privacy_missing","Formal ethical/privacy authorization required"))
        if not data.get("signed_data_use_review_reference"):
            issues.append(problem("no_signed_use_review","Author/data-controller signoff is required"))
    return {"pass":not issues,"issues":issues,"samples":len(data["files"]),
            "source_document_groups":len(group_splits),"institution_groups":len(institution_splits),
            "labels":dict(labels),"promotion_checked":promotion,
            "caveat":"Automated structural checks cannot verify real document truth, legal rights or scientific significance"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--root",type=Path,help="Raw dataset root; defaults to manifest parent")
    p.add_argument("--promotion",action="store_true",help="Apply additional BANK STATEMENT fraud publication evidence requirements")
    p.add_argument("--metadata-only",action="store_true",help="Offline audit without reading dataset bytes; never counts as full source verification")
    args=p.parse_args()
    dataset=json.loads(args.manifest.read_text(encoding="utf8"))
    result=assess(dataset,args.root or args.manifest.parent,
                  check_bytes=not args.metadata_only,promotion=args.promotion)
    result["file_bytes_verified"]=not args.metadata_only
    print(json.dumps(result,indent=2))
    if not result["pass"]:
        raise SystemExit(1)
    if args.metadata_only:
        print("Metadata structure passed, but raw file checksums remain UNVERIFIED.")

if __name__=="__main__":
    main()
