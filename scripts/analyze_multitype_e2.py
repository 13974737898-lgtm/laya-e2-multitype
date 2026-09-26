#!/usr/bin/env python3
"""Pair fixed E2 test predictions from base, E1, and E2 checkpoints."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ["base_test", "e1_test", "e2_test"]


def records(name):
    return [json.loads(line) for line in (ROOT / "runs" / name / "records.jsonl").read_text().splitlines()]


def compare(a, b):
    delta = [int(y["correct"]) - int(x["correct"]) for x, y in zip(a, b)]
    rng = random.Random(20260925)
    boot = sorted(sum(delta[rng.randrange(len(delta))] for _ in delta) / len(delta)
                  for _ in range(3000))
    return {"gain": sum(delta) / len(delta),
            "item_bootstrap_95ci": [boot[75], boot[2925]],
            "wrong_to_right": sum(not x["correct"] and y["correct"] for x, y in zip(a, b)),
            "right_to_wrong": sum(x["correct"] and not y["correct"] for x, y in zip(a, b))}


def main():
    all_rows = {name: records(name) for name in NAMES}
    n = len(all_rows[NAMES[0]])
    assert n == 1920
    assert all(len(rows) == n for rows in all_rows.values())
    ids = [row["id"] for row in all_rows[NAMES[0]]]
    assert all([row["id"] for row in rows] == ids for rows in all_rows.values())
    summary = {"n": n, "models": {},
               "base_to_e1": compare(all_rows["base_test"], all_rows["e1_test"]),
               "base_to_e2": compare(all_rows["base_test"], all_rows["e2_test"]),
               "e1_to_e2": compare(all_rows["e1_test"], all_rows["e2_test"])}
    for name, rows in all_rows.items():
        report = json.loads((ROOT / "runs" / name / "summary.json").read_text())
        assert report["split"] == "test"
        summary["models"][name] = {"accuracy": report["accuracy"],
                                   "errors": report["errors"], "by_family": report["by_family"]}
    output = ROOT / "runs" / "locked_comparison.json"
    assert not output.exists(), "Refusing to overwrite locked comparison"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
