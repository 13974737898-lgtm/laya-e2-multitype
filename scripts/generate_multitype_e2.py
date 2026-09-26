#!/usr/bin/env python3
"""Generate independently labelled decision tasks; no JevBench text is used."""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "multitype-e2"
VERSION = "multitype-e2-v1"
COUNTS = {"train": 2400, "dev": 480, "test": 480}  # Per family; divisible by 3 labels.
SEEDS = {"train": 2026092501, "dev": 2026092502, "test": 2026092503}
LEX = {
    "train": ["Aster", "Brindle", "Cedar", "Doric", "Ember", "Fallow", "Grove", "Haven"],
    "dev": ["Ibis", "Juniper", "Kestrel", "Linden", "Morrow", "Nacre", "Oriole", "Pine"],
    "test": ["Quartz", "Rowan", "Sable", "Tamar", "Umber", "Vesper", "Willow", "Yarrow"],
}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def shuffled_criteria(rng, mapping):
    items = list(mapping.items())
    rng.shuffle(items)
    return dict(items)


def policy(rng, split, target, n):
    entity = rng.choice(LEX[split])
    request = f"{entity}-{n + (100000 if split == 'train' else 200000 if split == 'dev' else 300000)}"
    cap = rng.randint(20, 150)
    amount = rng.randint(1, cap) if target == "process" else rng.randint(cap + 1, cap + 80)
    risk = target == "escalate"
    verified = target != "hold" or rng.choice([False, True])
    if target == "hold" and verified:
        amount = cap + rng.randint(1, 80)
    if target == "escalate":
        amount = rng.randint(1, cap + 80)
        verified = rng.choice([False, True])
    facts = [f"identity verified: {'yes' if verified else 'no'}",
             f"risk flag: {'present' if risk else 'absent'}",
             f"requested amount: {amount}", f"ordinary limit: {cap}"]
    rng.shuffle(facts)
    if split == "train":
        rules = "A risk flag requires escalation regardless of other fields. Otherwise, hold if identity is unverified or the requested amount exceeds the ordinary limit. Process all remaining requests."
        instruction = f"Apply the rules to request {request}. Which action is required?"
    elif split == "dev":
        rules = "Escalation takes precedence when risk is flagged. Without a flag, missing verification or an over-limit amount means hold. If neither applies, process."
        instruction = f"Choose the required disposition for file {request}."
    else:
        rules = "First check for a risk flag and escalate if one exists. Next hold an unverified or over-limit case. A case passing these checks may be processed."
        instruction = f"What should happen to case {request} under this policy?"
    return {"state": f"Policy: {rules} File {request}: " + "; ".join(facts) + ".",
            "instructions": instruction,
            "criteria": shuffled_criteria(rng, {"process": "Proceed with this case.",
                                             "hold": "Pause this case for ordinary review.",
                                             "escalate": "Send this case to the risk team."}),
            "label": target}


def temporal(rng, split, target, n):
    case = f"T{n + (100000 if split == 'train' else 200000 if split == 'dev' else 300000)}"
    deadline = rng.randint(20, 80)
    cap = rng.randint(40, 200)
    if target == "over_limit":
        amount = cap + rng.randint(1, 100)
        minute = rng.randint(deadline - 10, deadline + 10)
    elif target == "late":
        amount = rng.randint(1, cap)
        minute = deadline + rng.randint(1, 20)
    else:
        amount = rng.randint(1, cap)
        minute = deadline - rng.randint(0, 20)
    fields = [f"submitted at minute {minute}", f"deadline minute {deadline}",
              f"amount {amount}", f"cap {cap}"]
    rng.shuffle(fields)
    if split == "train":
        rules = "Amounts strictly above the cap are over limit, regardless of submission time. Otherwise a submission strictly after the deadline is late. Equality with either boundary is allowed."
        instruction = f"Classify submission {case} using the stated priority."
    elif split == "dev":
        rules = "Check the cap before timing: exceeding it wins over lateness. If within cap, a minute greater than the deadline is late; at the deadline is on time."
        instruction = f"Which status applies to transaction {case}?"
    else:
        rules = "An amount greater than the cap is over limit first. For other amounts, time later than the deadline is late; time equal to or earlier than it is on time."
        instruction = f"Assign the correct status to entry {case}."
    return {"state": f"Rule: {rules} Entry {case}: " + "; ".join(fields) + ".",
            "instructions": instruction,
            "criteria": shuffled_criteria(rng, {"on_time": "Within the cap and no later than the deadline.",
                                             "late": "Within the cap but after the deadline.",
                                             "over_limit": "Amount exceeds the cap; this has priority."}),
            "label": target}


def evidence(rng, split, target, n):
    key = f"R{n + (100000 if split == 'train' else 200000 if split == 'dev' else 300000)}"
    owner = rng.choice(LEX[split])
    other = rng.choice([x for x in LEX[split] if x != owner])
    tier = rng.choice(["bronze", "silver", "gold"])
    other_tier = rng.choice([x for x in ["bronze", "silver", "gold"] if x != tier])
    if target == "supported":
        claim_tier, include = tier, True
    elif target == "contradicted":
        claim_tier, include = other_tier, True
    else:
        claim_tier, include = rng.choice(["bronze", "silver", "gold"]), False
    records = [f"Record {key} belongs to {owner}.",
               f"{other} has tier {other_tier}."]
    if include:
        records.append(f"{owner} has tier {tier}.")
    else:
        records.append(f"The tier for {owner} is not listed.")
    rng.shuffle(records)
    if split == "train":
        instruction = f"Claim: the owner of record {key} has tier {claim_tier}. Decide whether the records establish, refute, or leave it open."
    elif split == "dev":
        instruction = f"For record {key}, is the owner's tier {claim_tier} confirmed, contradicted, or unknown from these entries?"
    else:
        instruction = f"Assess this assertion using only the listed records: the owner of {key} is {claim_tier} tier."
    return {"state": "Registry entries: " + " ".join(records), "instructions": instruction,
            "criteria": shuffled_criteria(rng, {"supported": "The available records establish the assertion.",
                                             "contradicted": "The available records establish a different value.",
                                             "insufficient": "The available records do not establish the needed value."}),
            "label": target}


def routing(rng, split, target, n):
    ticket = f"Q{n + (100000 if split == 'train' else 200000 if split == 'dev' else 300000)}"
    if target == "lookup":
        operation, authorized = rng.choice(["inspect", "view", "check"]), rng.choice([True, False])
    elif target == "modify":
        operation, authorized = rng.choice(["update", "change", "edit"]), True
    else:
        operation, authorized = rng.choice(["update", "change", "edit"]), False
    asset = rng.choice(LEX[split])
    if split == "train":
        rules = "Read-only requests use lookup. A write request with valid authorization uses modify. An unauthorized write must be escalated; do not modify it."
        instruction = f"Choose exactly one tool for ticket {ticket}."
    elif split == "dev":
        rules = "Use lookup to inspect without changing data. Only a permitted change may use modify. Route an unpermitted change to escalation."
        instruction = f"What tool is appropriate for request {ticket}?"
    else:
        rules = "Inspection goes to lookup. Changes require authorization for modify; otherwise send the request for escalation."
        instruction = f"Select the safe tool for case {ticket}."
    return {"state": f"Tool policy: {rules} Ticket {ticket} asks to {operation} the {asset} record. Authorization: {'valid' if authorized else 'missing'}.",
            "instructions": instruction,
            "criteria": shuffled_criteria(rng, {"lookup": "Read information without changing it.",
                                             "modify": "Apply an authorized change.",
                                             "escalate": "Hand off a change that lacks authorization."}),
            "label": target}


FAMILIES = {
    "policy": (policy, ["process", "hold", "escalate"]),
    "temporal": (temporal, ["on_time", "late", "over_limit"]),
    "evidence": (evidence, ["supported", "contradicted", "insufficient"]),
    "routing": (routing, ["lookup", "modify", "escalate"]),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"version": VERSION, "seeds": SEEDS, "counts_per_family": COUNTS,
                "family_labels": {k: labels for k, (_, labels) in FAMILIES.items()},
                "source": "independently authored deterministic generators; no benchmark items imported",
                "splits": {}}
    global_fingerprints = set()
    for split, count in COUNTS.items():
        rng = random.Random(SEEDS[split])
        rows = []
        for family, (builder, labels) in FAMILIES.items():
            for i in range(count):
                target = labels[i % 3]
                row = builder(rng, split, target, i)
                row.update({"family": family, "split": split, "template_version": VERSION})
                assert row["label"] in row["criteria"]
                fingerprint = sha(row["state"] + "\x1f" + row["instructions"])
                assert fingerprint not in global_fingerprints
                global_fingerprints.add(fingerprint)
                row["id"] = fingerprint
                rows.append(row)
        rng.shuffle(rows)
        path = OUT / f"{split}.jsonl"
        with path.open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        manifest["splits"][split] = {"rows": len(rows), "sha256": sha(path.read_text()),
                                     "counts": {k: dict(Counter(r["label"] for r in rows if r["family"] == k))
                                                for k in FAMILIES}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v["rows"] for k, v in manifest["splits"].items()}))


if __name__ == "__main__":
    main()
