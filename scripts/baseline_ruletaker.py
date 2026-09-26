#!/usr/bin/env python3
"""Evaluate native Laya choices on RuleTaker pilot development examples."""
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
    data = ROOT / "pilot" / "dev.jsonl"
    manifest = json.loads((ROOT / "pilot" / "manifest.json").read_text())
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    assert len(rows) == manifest["splits"]["dev"]["rows"] == 1750
    output = ROOT / "pilot" / "base_dev_records.jsonl"
    summary_path = ROOT / "pilot" / "base_dev_summary.json"
    assert not output.exists() and not summary_path.exists(), "Refusing to overwrite a completed run"
    agent = laya.load("/home/maolinqi/mlq/laya-jevbench-baseline/model", device="cuda")
    results = []
    start = time.perf_counter()
    with output.open("w") as stream:
        for i, row in enumerate(rows, 1):
            question = {"type": "choice",
                        "instructions": "Does the statement logically follow from the context? Statement: " + row["question"],
                        "criteria": {
                            "entailment": "The statement follows from the context.",
                            "not entailment": "The statement does not follow from the context."}}
            t0 = time.perf_counter()
            error = None
            predicted = None
            confidence = None
            try:
                answer = agent.predict(row["context"], {"decision": question},
                                       max_len=512, head_max_len=192)["answers"]["decision"]
                probs = answer["probabilities"]
                predicted = max(probs, key=probs.get)
                confidence = float(probs[predicted])
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
            torch.cuda.synchronize()
            record = {"pair_sha256": row["pair_sha256"], "config": row["config"],
                      "label": row["label"], "predicted": predicted,
                      "correct": predicted == row["label"], "confidence": confidence,
                      "latency_s": time.perf_counter() - t0, "error": error}
            results.append(record)
            stream.write(json.dumps(record) + "\n")
            if i % 100 == 0:
                stream.flush()
                print(f"{i}/{len(rows)}", flush=True)
    by_config = collections.defaultdict(list)
    for result in results:
        by_config[result["config"]].append(result)
    summary = {"n": len(results), "accuracy": sum(r["correct"] for r in results) / len(results),
               "errors": sum(bool(r["error"]) for r in results),
               "by_config": {k: {"n": len(v), "accuracy": sum(r["correct"] for r in v) / len(v)}
                             for k, v in sorted(by_config.items())},
               "wall_s": time.perf_counter() - start,
               "model": "convaiinnovations/laya@55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
               "split": "dev", "prompt_version": "ruletaker-choice-v1",
               "max_len": 512, "head_max_len": 192,
               "test_used": False}
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
