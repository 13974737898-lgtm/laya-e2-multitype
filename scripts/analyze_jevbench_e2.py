#!/usr/bin/env python3
"""Fixed paired comparison of frozen E2 and base JevBench public predictions."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "results" / "multitype-e2" / "jevbench-transfer"


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    base = read(ROOT / "base-records.jsonl")
    tuned = read(ROOT / "records.jsonl")
    assert len(base) == len(tuned) == 231
    assert [r["task_id"] for r in base] == [r["task_id"] for r in tuned]
    delta = [int(b["correct"]) - int(a["correct"]) for a, b in zip(base, tuned)]
    rng = random.Random(20260925)
    boot = sorted(sum(delta[rng.randrange(len(delta))] for _ in delta) / len(delta)
                  for _ in range(10000))
    output = {
        "n": len(delta),
        "base_correct": sum(bool(r["correct"]) for r in base),
        "e2_correct": sum(bool(r["correct"]) for r in tuned),
        "gain": sum(delta) / len(delta),
        "item_bootstrap_95ci": [boot[250], boot[9750]],
        "wrong_to_right": sum(not a["correct"] and b["correct"] for a, b in zip(base, tuned)),
        "right_to_wrong": sum(a["correct"] and not b["correct"] for a, b in zip(base, tuned)),
        "bootstrap_seed": 20260925,
        "bootstrap_resamples": 10000,
    }
    (ROOT / "paired.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
