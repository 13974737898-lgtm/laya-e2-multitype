#!/usr/bin/env python3
"""Evaluate one Laya checkpoint on a fixed E2 split; development split by default."""
import argparse
import collections
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, "/home/maolinqi/mlq/laya")
import laya

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    out = ROOT / "runs" / args.label
    assert not out.exists(), "Refusing to overwrite a completed run"
    out.mkdir(parents=True)
    rows = [json.loads(line) for line in (ROOT / "data" / f"{args.split}.jsonl").read_text().splitlines()]
    agent = laya.load(args.model, device="cuda")
    records = []
    start = time.perf_counter()
    with (out / "records.jsonl").open("w") as stream:
        for i, row in enumerate(rows, 1):
            question = {"type": "choice", "instructions": row["instructions"], "criteria": row["criteria"]}
            t0 = time.perf_counter()
            error = None
            predicted = None
            probs = None
            try:
                answer = agent.predict(row["state"], {"decision": question},
                                       max_len=512, head_max_len=192)["answers"]["decision"]
                probs = {k: float(v) for k, v in answer["probabilities"].items()}
                predicted = max(probs, key=probs.get)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            torch.cuda.synchronize()
            record = {"id": row["id"], "family": row["family"], "label": row["label"],
                      "predicted": predicted, "correct": predicted == row["label"],
                      "probs": probs, "latency_s": time.perf_counter() - t0, "error": error}
            records.append(record)
            stream.write(json.dumps(record) + "\n")
            if i % 250 == 0:
                stream.flush()
                print(f"{i}/{len(rows)}", flush=True)
    family = collections.defaultdict(list)
    for row in records:
        family[row["family"]].append(row)
    summary = {"model": args.model, "split": args.split, "n": len(records),
               "accuracy": sum(r["correct"] for r in records) / len(records),
               "errors": sum(bool(r["error"]) for r in records),
               "by_family": {k: {"n": len(v), "accuracy": sum(x["correct"] for x in v) / len(v)}
                             for k, v in sorted(family.items())},
               "wall_s": time.perf_counter() - start}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
