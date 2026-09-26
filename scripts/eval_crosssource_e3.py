#!/usr/bin/env python3
"""Evaluate frozen Laya checkpoints on the fixed E3 cross-source snapshot."""
import argparse
import collections
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, "/home/maolinqi/mlq/laya")
import laya
from laya.common import build_sequence, render_options, serialize_state

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    output = ROOT / "runs" / args.label
    assert not output.exists(), "Refusing to overwrite a completed or partial run"
    output.mkdir(parents=True)
    rows = [json.loads(s) for s in (ROOT / "data" / "eval.jsonl").read_text().splitlines()]
    assert len(rows) == 699
    agent = laya.load(args.model, device="cuda")
    records = []
    started = time.perf_counter()
    with (output / "records.jsonl").open("w") as stream:
        for i, row in enumerate(rows, 1):
            question = {"type": "choice", "instructions": row["instructions"],
                        "criteria": row["criteria"]}
            internal = agent._to_internal(question)
            state_ids = agent.tok(serialize_state(row["state"]).replace(agent.tok.mask_token, " "),
                                  add_special_tokens=False)["input_ids"]
            sequence, _ = build_sequence(agent.tok, row["state"], internal, 512, 192,
                                         state_ids=state_ids)
            empty, _ = build_sequence(agent.tok, "", internal, 512, 192, state_ids=[])
            retained = max(0, len(sequence) - len(empty))
            error = None
            predicted = None
            probabilities = None
            t0 = time.perf_counter()
            try:
                answer = agent.predict(row["state"], {"decision": question}, max_len=512,
                                       head_max_len=192)["answers"]["decision"]
                probabilities = {k: float(v) for k, v in answer["probabilities"].items()}
                predicted = max(probabilities, key=probabilities.get)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            torch.cuda.synchronize()
            record = {"id": row["id"], "family": row["family"], "label": row["label"],
                      "predicted": predicted, "correct": predicted == row["label"],
                      "probabilities": probabilities, "error": error,
                      "latency_s": time.perf_counter() - t0,
                      "state_tokens": len(state_ids), "retained_state_tokens": retained,
                      "truncated": len(state_ids) > retained,
                      "option_count": len(render_options(internal))}
            records.append(record)
            stream.write(json.dumps(record) + "\n")
            if i % 100 == 0:
                stream.flush()
                print(f"{args.label}: {i}/{len(rows)}", flush=True)
    family = collections.defaultdict(list)
    for record in records:
        family[record["family"]].append(record)
    per_family = {name: {"n": len(items), "correct": sum(r["correct"] for r in items),
                         "accuracy": sum(r["correct"] for r in items) / len(items),
                         "errors": sum(bool(r["error"]) for r in items),
                         "truncated": sum(r["truncated"] for r in items)}
                  for name, items in sorted(family.items())}
    summary = {"model": args.model, "n": len(records), "correct": sum(r["correct"] for r in records),
               "accuracy": sum(r["correct"] for r in records) / len(records),
               "macro_accuracy": sum(v["accuracy"] for v in per_family.values()) / len(per_family),
               "errors": sum(bool(r["error"]) for r in records),
               "truncated": sum(r["truncated"] for r in records),
               "by_family": per_family, "wall_s": time.perf_counter() - started}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
