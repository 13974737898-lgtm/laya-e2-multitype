#!/usr/bin/env python3
"""Paired and source-stratified E3 comparison; no model selection."""
import collections
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "crosssource-e3" / "eval.jsonl"
RESULTS = ROOT / "results" / "crosssource-e3"
SEED = 20260926
RESAMPLES = 10000


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def interval(values, rng):
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in values) / n
                     for _ in range(RESAMPLES))
    return [samples[250], samples[9750]]


def main():
    source = read(DATA)
    base = read(RESULTS / "base" / "records.jsonl")
    tuned = read(RESULTS / "e2" / "records.jsonl")
    assert len(source) == len(base) == len(tuned) == 699
    ids = [r["id"] for r in source]
    assert [r["id"] for r in base] == [r["id"] for r in tuned] == ids
    assert all(s["label"] == a["label"] == b["label"] for s, a, b in zip(source, base, tuned))
    rng = random.Random(SEED)
    groups = collections.defaultdict(list)
    for src, a, b in zip(source, base, tuned):
        groups[src["family"]].append((src, a, b))
    output = {"n": 699, "seed": SEED, "resamples": RESAMPLES, "by_family": {}}
    delta_by_family = {}
    for name, rows in sorted(groups.items()):
        labels = collections.Counter(s["label"] for s, _, _ in rows)
        delta = [int(b["correct"]) - int(a["correct"]) for _, a, b in rows]
        delta_by_family[name] = delta
        output["by_family"][name] = {
            "n": len(rows), "base_correct": sum(a["correct"] for _, a, _ in rows),
            "e2_correct": sum(b["correct"] for _, _, b in rows),
            "gain": sum(delta) / len(delta), "paired_item_bootstrap_95ci": interval(delta, rng),
            "wrong_to_right": sum(not a["correct"] and b["correct"] for _, a, b in rows),
            "right_to_wrong": sum(a["correct"] and not b["correct"] for _, a, b in rows),
            "majority_label": labels.most_common(1)[0][0],
            "majority_label_accuracy": labels.most_common(1)[0][1] / len(rows),
            "base_errors": sum(bool(a["error"]) for _, a, _ in rows),
            "e2_errors": sum(bool(b["error"]) for _, _, b in rows),
            "base_truncated": sum(a["truncated"] for _, a, _ in rows),
            "e2_truncated": sum(b["truncated"] for _, _, b in rows),
        }
    names = sorted(delta_by_family)
    macro_delta = sum(sum(delta_by_family[n]) / len(delta_by_family[n]) for n in names) / len(names)
    boot = []
    for _ in range(RESAMPLES):
        boot.append(sum(sum(values[rng.randrange(len(values))] for _ in values) / len(values)
                        for values in (delta_by_family[n] for n in names)) / len(names))
    boot.sort()
    output["macro_gain"] = macro_delta
    output["macro_stratified_item_bootstrap_95ci"] = [boot[250], boot[9750]]
    output["micro_gain"] = sum(sum(v) for v in delta_by_family.values()) / 699
    (RESULTS / "paired.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
