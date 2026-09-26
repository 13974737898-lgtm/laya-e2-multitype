#!/usr/bin/env python3
"""Exercise the live E2 service through JevBench's own TypeSafe adapter."""
import argparse
import json
import math
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jevbench-root", required=True)
    ap.add_argument("--laya-root", required=True)
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--endpoint", default="http://127.0.0.1:8942")
    args = ap.parse_args()
    sys.path.insert(0, args.jevbench_root)
    sys.path.insert(0, args.laya_root)
    import laya
    from jevbench.adapters.base import build_question
    from jevbench.adapters.typesafe import TypeSafeAdapter
    from jevbench.tasks import Task

    tasks = [
        Task("fixture-choice", "policy", "Identity verified: yes. Risk flag: absent.",
             {"type": "choice", "instructions": "Which action fits?",
              "criteria": {"process": "Verified with no risk flag", "hold": "Missing verification",
                           "escalate": "Risk flag is present"}},
             ["process", "hold", "escalate"], "process", "public"),
        Task("fixture-noul", "policy", "The record is verified.",
             {"type": "noul", "instructions": "Is the record verified?"},
             ["no", "yes"], "yes", "public"),
        Task("fixture-score", "severity", "The service has a short delay.",
             {"type": "score", "instructions": "How severe is the issue?",
              "criteria": ["low", "medium", "high"]},
             ["0", "1", "2"], 0, "public"),
    ]
    adapter = TypeSafeAdapter(endpoint=args.endpoint, model="jev-latest", key_env="")
    direct = laya.load(args.model_path, device="cuda")
    report = []
    for task in tasks:
        task.validate()
        result = adapter.run(task)
        assert result.ok, (task.id, result.error)
        assert result.model == "laya-e2-multitype-seed20260925"
        assert set(result.probs) == set(task.labels)
        assert all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1
                   for v in result.probs.values())
        assert abs(sum(result.probs.values()) - 1.0) < 0.002
        assert result.usage.get("input_tokens", 0) > 0
        assert result.usage.get("output_tokens") == 0
        answer = direct.predict(task.state, {"decision": build_question(task)},
                                max_len=512, head_max_len=192)["answers"]["decision"]
        if task.question["type"] == "noul":
            direct_probs = {"yes": answer["noul"], "no": 1 - answer["noul"]}
        else:
            direct_probs = answer["probabilities"]
        assert all(abs(result.probs[k] - direct_probs[k]) < 0.0002 for k in task.labels)
        report.append({"id": task.id, "type": task.question["type"], "status": result.status,
                       "schema_valid": True, "direct_parity": True,
                       "latency_s": result.latency_s})
    print(json.dumps({"endpoint": args.endpoint, "cases": report}, indent=2))


if __name__ == "__main__":
    main()
