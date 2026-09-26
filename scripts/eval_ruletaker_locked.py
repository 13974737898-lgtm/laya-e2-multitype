#!/usr/bin/env python3
"""One locked test evaluation of base and dev-selected native Laya checkpoint."""
import collections
import json
import random
import statistics
import sys
import time
from pathlib import Path

import torch
from safetensors.torch import load_file

sys.path.insert(0, "/home/maolinqi/mlq/laya")
import laya

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "runs" / "native_ruletaker_seed20260925"


def evaluate(agent, rows):
    results = []
    for i, row in enumerate(rows, 1):
        question = {"type": "choice",
                    "instructions": "Does the statement logically follow from the context? Statement: " + row["question"],
                    "criteria": {
                        "entailment": "The statement follows from the context.",
                        "not entailment": "The statement does not follow from the context."}}
        start = time.perf_counter()
        answer = agent.predict(row["context"], {"decision": question},
                               max_len=512, head_max_len=192)["answers"]["decision"]
        torch.cuda.synchronize()
        probs = {k: float(v) for k, v in answer["probabilities"].items()}
        predicted = max(probs, key=probs.get)
        results.append({"predicted": predicted, "p_entailment": probs["entailment"],
                        "correct": predicted == row["label"],
                        "latency_s": time.perf_counter() - start})
        if i % 250 == 0:
            print(f"{i}/{len(rows)}", flush=True)
    return results


def metrics(results, rows):
    correct = [r["correct"] for r in results]
    confidence = [max(r["p_entailment"], 1 - r["p_entailment"]) for r in results]
    latencies = sorted(r["latency_s"] for r in results)
    bins = [[] for _ in range(10)]
    for c, conf in zip(correct, confidence):
        bins[min(9, int(conf * 10))].append((conf, c))
    ece = sum(len(bucket) / len(rows) * abs(statistics.mean(x[0] for x in bucket) -
              statistics.mean(x[1] for x in bucket)) for bucket in bins if bucket)
    by_config = collections.defaultdict(list)
    for result, row in zip(results, rows):
        by_config[row["config"]].append(result["correct"])
    return {"n": len(rows), "accuracy": statistics.mean(correct),
            "brier_binary": statistics.mean((r["p_entailment"] - (row["label"] == "entailment")) ** 2
                                            for r, row in zip(results, rows)),
            "ece_10bin": ece, "p50_latency_s": latencies[len(latencies) // 2],
            "p95_latency_s": latencies[int(.95 * (len(latencies) - 1))],
            "by_config": {k: {"n": len(v), "accuracy": statistics.mean(v)}
                          for k, v in sorted(by_config.items())}}


def main():
    assert (RUN / "best.json").exists() and (RUN / "best.safetensors").exists()
    assert not (RUN / "test_summary.json").exists(), "Locked test already evaluated"
    manifest = json.loads((ROOT / "pilot" / "manifest.json").read_text())
    rows = [json.loads(line) for line in (ROOT / "pilot" / "test.jsonl").read_text().splitlines()]
    assert len(rows) == manifest["splits"]["test"]["rows"] == 1750
    agent = laya.load("/home/maolinqi/mlq/laya-jevbench-baseline/model", device="cuda")
    print("Evaluating base", flush=True)
    base = evaluate(agent, rows)
    weights = load_file(RUN / "best.safetensors", device="cpu")
    agent.model.load_state_dict(weights, strict=True)
    agent.model.eval()
    print("Evaluating dev-selected checkpoint", flush=True)
    tuned = evaluate(agent, rows)
    deltas = [int(t["correct"]) - int(b["correct"]) for b, t in zip(base, tuned)]
    rng = random.Random(20260925)
    boot = sorted(sum(deltas[rng.randrange(len(deltas))] for _ in deltas) / len(deltas)
                  for _ in range(2000))
    summary = {"split": "test", "selection": json.loads((RUN / "best.json").read_text()),
               "base": metrics(base, rows), "tuned": metrics(tuned, rows),
               "paired_gain": sum(deltas) / len(deltas),
               "paired_bootstrap_95ci": [boot[50], boot[1950]],
               "wrong_to_right": sum(not b["correct"] and t["correct"] for b, t in zip(base, tuned)),
               "right_to_wrong": sum(b["correct"] and not t["correct"] for b, t in zip(base, tuned)),
               "prompt_version": "ruletaker-choice-v1", "test_used_for_selection": False}
    with (RUN / "test_records.jsonl").open("w") as stream:
        for row, b, t in zip(rows, base, tuned):
            stream.write(json.dumps({"pair_sha256": row["pair_sha256"], "config": row["config"],
                                     "label": row["label"], "base": b, "tuned": t}) + "\n")
    (RUN / "test_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
