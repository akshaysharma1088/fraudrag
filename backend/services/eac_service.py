"""FraudRAG-EAC executable evidence-acquisition sandbox.

Only fictional issuer records. This module is not an issuer authentication
system or a fraud detector. Human-supplied trust metadata is not a signature.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from typing import Protocol

from benchmark.provenance_certificate_v4 import (
    Claim, Reference, verify, reference_admissible, CONFLICT,
)

EFFECTIVE_AT = "2026-07-30T12:00:00Z"
CUTOFF = "2026-07-30T23:00:00Z"
CLAIM_KEYS = ("account", "closing", "transaction")
FULL = 7
SCENARIOS = {
    "consistent": "Complete fictional issuer records match the submission",
    "altered": "The submitted closing balance differs from the original",
    "partial": "Sources have no transaction-level supporting reference",
    "conflicting": "Two pre-fetched issuer references disagree on a field",
    "future": "References arrive after the decision cutoff",
}


@dataclass(frozen=True)
class Action:
    name: str
    fields: tuple[str, ...]
    cost_tenths: int
    availability: float


class EvidenceProvider(Protocol):
    def fetch(self, action_name: str) -> tuple[Reference, ...]:
        ...


def _source(key: str, value: str, name: str, *, future: bool = False) -> Reference:
    return Reference(
        source_id=f"sandbox://{name}/{key}",
        source_family="fictional-issuer-" + name,
        key=key, value=value,
        valid_from="2026-07-01T00:00:00Z",
        valid_until="2026-08-01T00:00:00Z",
        recorded_at="2026-08-04T00:00:00Z" if future else "2026-07-29T00:00:00Z",
        ingested_at="2026-08-04T00:00:00Z" if future else "2026-07-30T00:00:00Z",
        issuer_attested=True,
        completeness_attested_for_key=True,
        source_digest_sha256=sha256(f"FICTIONAL:{key}:{value}:{name}".encode()).hexdigest(),
    )


class SandboxProvider:
    """Deterministic fictional data; never calls a bank, graph or GPT."""

    def __init__(self, scenario: str):
        if scenario not in SCENARIOS:
            raise ValueError("Unknown sandbox scenario")
        self.scenario = scenario
        self.issuer_values = {
            "account": "ACC-DEMO-001", "closing": "120.00",
            "transaction": "T-DEMO-001:20.00",
        }
        submitted = dict(self.issuer_values)
        if scenario == "altered":
            submitted["closing"] = "125.00"
        self.claims = tuple(Claim(k, submitted[k]) for k in CLAIM_KEYS)
        self.actions = (
            Action("single_account", ("account",), 10, 0.78),
            Action("single_closing", ("closing",), 10, 0.83),
            Action("single_transaction", ("transaction",), 10, 0.76),
            Action("primary_bundle", CLAIM_KEYS, 22, 0.86),
            Action("backup_bundle", CLAIM_KEYS, 31, 0.81),
        )
        self.initial_references = (
            (_source("closing", "120.00", "seed-A"),
             _source("closing", "121.00", "seed-B"))
            if scenario == "conflicting" else ()
        )

    def fetch(self, action_name: str) -> tuple[Reference, ...]:
        action = next((x for x in self.actions if x.name == action_name), None)
        if action is None:
            raise ValueError("Unknown source action")
        keys = tuple(k for k in action.fields
                     if self.scenario != "partial" or k != "transaction")
        return tuple(_source(k, self.issuer_values[k], action.name,
                             future=self.scenario == "future") for k in keys)


def _coverage(references: tuple[Reference, ...]) -> int:
    from benchmark.provenance_certificate_v4 import timestamp
    at, cutoff = timestamp(EFFECTIVE_AT), timestamp(CUTOFF)
    mask = 0
    for j, key in enumerate(CLAIM_KEYS):
        if any(reference_admissible(r, key, at, cutoff)[0]
               and r.completeness_attested_for_key for r in references):
            mask |= (1 << j)
    return mask


def _planner(actions: tuple[Action, ...], strategy: str):
    """Classical deterministic planning against shared fictional priors."""
    masks = tuple(sum(1 << CLAIM_KEYS.index(k) for k in a.fields) for a in actions)

    def choices(mask, used, left):
        return [i for i, a in enumerate(actions) if not (used & (1 << i))
                and a.cost_tenths <= left and masks[i] & ~mask]

    @lru_cache(maxsize=None)
    def value(mask, used, left):
        if mask == FULL:
            return 1.
        best = 0.
        for i in choices(mask, used, left):
            action = actions[i]
            rest = left - action.cost_tenths
            used2 = used | (1 << i)
            score = (action.availability * value(mask | masks[i], used2, rest)
                     + (1-action.availability)*value(mask, used2, rest)
                     - 0.035*action.cost_tenths/10)
            best = max(best, score)
        return best

    def select(mask, used, left):
        options = choices(mask, used, left)
        if mask == FULL or not options:
            return None
        if strategy == "fixed":
            priority = ("primary_bundle", "single_account", "single_closing",
                        "single_transaction", "backup_bundle")
            return min(options, key=lambda i: priority.index(actions[i].name))
        if strategy == "greedy":
            return min(options, key=lambda i:
                       (-actions[i].availability*(masks[i] & ~mask).bit_count()
                        / actions[i].cost_tenths, i))
        if strategy != "adaptive_dp":
            raise ValueError("Unknown source selection policy")
        best = value(mask, used, left)
        if best <= 0:
            return None
        for i in options:
            action = actions[i]
            rest = left - action.cost_tenths
            used2 = used | (1 << i)
            score = (action.availability * value(mask | masks[i], used2, rest)
                     + (1-action.availability)*value(mask, used2, rest)
                     - 0.035*action.cost_tenths/10)
            if abs(score-best) < 1e-10:
                return i
        return None

    return select


def run_sandbox(*, scenario: str, strategy: str = "adaptive_dp",
                budget_units: float = 4.0) -> dict:
    """Fetch source responses, report trace and replay final certificate."""
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    if strategy not in ("adaptive_dp", "greedy", "fixed"):
        raise ValueError("Unknown policy")
    if not 1 <= budget_units <= 8 or abs(budget_units*10-round(budget_units*10)) > 1e-8:
        raise ValueError("Budget must be between 1 and 8 in tenths")

    provider = SandboxProvider(scenario)
    refs = list(provider.initial_references)
    select = _planner(provider.actions, strategy)
    used = spent = 0
    trace = []
    mask = _coverage(tuple(refs))
    cert = verify(provider.claims, tuple(refs),
                  effective_at=EFFECTIVE_AT, as_of_cutoff=CUTOFF)
    if cert["document_status"] != CONFLICT:
        while mask != FULL:
            idx = select(mask, used, round(budget_units*10)-spent)
            if idx is None:
                break
            action = provider.actions[idx]
            used |= 1 << idx
            spent += action.cost_tenths
            newly = provider.fetch(action.name)
            refs.extend(newly)
            updated = _coverage(tuple(refs))
            cert = verify(provider.claims, tuple(refs),
                          effective_at=EFFECTIVE_AT, as_of_cutoff=CUTOFF)
            trace.append({
                "action": action.name,
                "cost_units": action.cost_tenths/10,
                "returned_source_ids": [r.source_id for r in newly],
                "newly_covered_fields": [k for i,k in enumerate(CLAIM_KEYS)
                                         if updated & (1<<i) and not mask & (1<<i)],
                "decision_after_action": cert["document_status"],
            })
            mask = updated
            if cert["document_status"] == CONFLICT:
                break
    result = {
        "system": "FraudRAG-EAC",
        "scenario": scenario,
        "description": SCENARIOS[scenario],
        "policy": strategy,
        "budget_units": budget_units,
        "spent_units": spent/10,
        "queries": len(trace),
        "trace": trace,
        "completed_field_coverage": mask == FULL,
        "certificate": cert,
        "sandbox_only": True,
        "disclaimer": (
            "All issuer records, attestation flags and costs are fictional. "
            "No independent signature verification, real financial fraud "
            "determination or actual bank connection is performed."
        ),
    }
    return result
