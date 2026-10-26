# FraudRAG

**Research prototype for financial-document consistency checking, retrieval, and conditional evidence verification.**

[![CI/CD](https://github.com/akshaysharma1088/fraudrag/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/akshaysharma1088/fraudrag/actions)

> **Research integrity notice (October 26, 2026):** FraudRAG is a research prototype, **not a validated bank-statement forgery detector or production fraud adjudication service**. Historic AUC 0.943, F1 0.883, fraud-ring detection rates, latency claims, and "first in finance" claims from older README/manuscript drafts have not been reproduced with the necessary original evidence and **must not be cited as results**. A complete artificial bank reference lets a fair exact-match program achieve the same F1 as evidence-grounded GPT in the available small synthetic pilot. Source-retrieval and financial QA experiments are different tasks from real fraud adjudication.

## What this repository contains

FraudRAG explores an ingestion-and-analysis prototype with a FastAPI backend, a React frontend, document processing, Neo4j relationship storage, ChromaDB retrieval, and language-model analysis. Individual architectural capabilities should be treated as *implementation design*, not proof of end-to-end quality, issuer authentication, multi-hop benefits or production security.

**Source conditional verification** distinguishes an extracted claim from a separately sourced reference. When reference evidence is unavailable, untrusted, stale, temporally invalid, incomplete or contradictory, a conservative checker can defer or flag a difference rather than authenticate a document. The reference issuer's identity and completeness must be independently established in a real deployment; the synthetic studies assume attestation metadata and do not cryptographically validate bank issuers.

## Research results that are supported by archived runs

| Experiment | Observed result | What it does *not* show |
|---|---|---|
| V2 synthetic statement comparison | 28 customer-disjoint fictional cases. GPT with actual Neo4j/Chroma evidence and a fair exact-ledger non-LLM comparator both obtained F1 1.000. | Better bank-fraud performance than deterministic matching, or external bank generalization. |
| V3 publisher-synthetic PDF text perturbations | 20 controlled text cases derived from five externally published *synthetic* PDF sources; 60 GPT calls with differing source availability. | PDF image tamper localization or genuine adjudicated fraud. |
| V4 artificial source-acquisition study | At four invented cost units, dynamic programming completed 509/720 cases (70.69%); prior-aware greedy completed 495/720 (68.75%). The reported paired coverage confidence interval includes zero. | Novel DP optimization or real-dollar bank-API cost savings. |
| V5 published financial-report source-witness intervention | 329 supplied gold-answer candidates from 187 TAT-QA contexts under constructed evidence perturbations. | End-to-end autonomous question answering, issuer signatures, or real bank-fraud labels. |
| V6 no-source GPT test | Both prompting approaches abstained on 24/24 questions with no supplied evidence. | That extra abstention prompting outperforms ordinary prompting. |
| V7B public TAT-QA test QA | Two GPT approaches answered 64/64 each; approximate normalized token-overlap F1 0.518 vs 0.534, with paired difference confidence interval crossing zero. | Evidence-entailed human-verified answers, institution-disjoint evaluation, or statistically established superiority. |

The original V5 paragraph-deletion GPT pilot cannot establish unsupported-answer rates: deleting exact gold-answer strings did not necessarily remove semantically equivalent supporting information. The incomplete first V7 run is archived and is not treated as a completed benchmark.

For experimental provenance, citations, caveats, source hashes, and publication clearance see **[Research publication evidence](research/publication/README.md)**. The broader experimental implementation remains in the separate research branch and unmerged [draft PR #1](https://github.com/akshaysharma1088/fraudrag/pull/1).

## Development quick start

These instructions are for **local prototype development using fictional or authorized non-sensitive documents**, not real customer financial information.

```bash
git clone https://github.com/akshaysharma1088/fraudrag.git
cd fraudrag
cp .env.example .env
# Set credentials appropriate to the providers you actually use.
docker compose up -d
```

See `docker-compose.yml`, backend documentation and `http://localhost:8000/docs` if the API stack is configured and running. Do not upload genuine statements, identity numbers or confidential personal data without an independently reviewed privacy/security/data-retention process; archival code has not validated all production controls.

For a local lightweight Python development setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-ci.txt
python -m pytest tests/ -q
```

CI results do not establish scientific novelty, privacy compliance, real issuer authentication, or deployment readiness.

## Publication and citation

The earlier public [FraudRAG SSRN preprint (DOI: 10.2139/ssrn.6714178)](https://doi.org/10.2139/ssrn.6714178) exists and has been cited. Its older performance/novelty statements are **not independently reproducible from the currently available original experiment artifacts**. An author-controlled correction and accurate overlap disclosure are pending.

A later comparative research manuscript is a **working author-review draft only**. It has **not** been submitted to IEEE OJ-CS, accepted by IEEE TKDE or otherwise certified by IEEE. Do not cite it as an accepted or published IEEE article. Scientific conclusions are limited to the tasks and experimental evidence described above.

## Maintainer

Akshay Sharma. Project code and research materials remain subject to the repository's applicable license, upstream third-party dataset terms, and publication/IP clearance. Neither a copied source hash nor a synthetic issuer-attested flag proves financial authenticity.
