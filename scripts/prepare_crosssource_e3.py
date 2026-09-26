#!/usr/bin/env python3
"""Snapshot two independently authored validation sets for a frozen cross-source test."""
import hashlib
import json
import random
import time
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "crosssource-e3"
SEED = 20260926
SOURCES = [
    ("google/boolq", "default", "validation", 3270, "35b264d03638db9f4ce671b711558bf7ff0f80d5"),
    ("allenai/ai2_arc", "ARC-Challenge", "validation", 299, "210d026faf9955653af8916fad021475a3f00453"),
]


def get_json(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "laya-crosssource-e3/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (OUT / "manifest.json").exists(), "Refusing to overwrite a fixed snapshot"
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"version": "crosssource-e3-v1", "selection_seed": SEED, "sources": [], "outputs": {}}
    selected = []
    for repo, config, split, expected_n, expected_sha in SOURCES:
        before = get_json("https://huggingface.co/api/datasets/" + repo)["sha"]
        assert before == expected_sha, (repo, before)
        family = "boolq" if config == "default" else "arc_challenge"
        source_path = ("data/validation-00000-of-00001.parquet" if family == "boolq"
                       else "ARC-Challenge/validation-00000-of-00001.parquet")
        parquet_path = OUT / f"{family}-validation-source.parquet"
        source_url = f"https://huggingface.co/datasets/{repo}/resolve/{expected_sha}/{source_path}"
        req = urllib.request.Request(source_url, headers={"User-Agent": "laya-crosssource-e3/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response, parquet_path.open("wb") as target:
            while block := response.read(1024 * 1024):
                target.write(block)
        fetched = pq.read_table(parquet_path).to_pylist()
        after = get_json("https://huggingface.co/api/datasets/" + repo)["sha"]
        assert before == after and len(fetched) == expected_n
        raw_path = OUT / f"{family}-validation-source.jsonl"
        with raw_path.open("w") as stream:
            for row in fetched:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        manifest["sources"].append({"repo": repo, "revision": before, "config": config,
                                    "split": split, "rows": expected_n,
                                    "source_path": source_path,
                                    "parquet_snapshot": parquet_path.name,
                                    "parquet_sha256": digest(parquet_path),
                                    "source_snapshot": raw_path.name, "sha256": digest(raw_path)})
        if family == "boolq":
            indices = sorted(random.Random(SEED).sample(range(expected_n), 400))
            for idx in indices:
                row = fetched[idx]
                selected.append({"id": f"boolq:{idx}", "family": family, "source_row": idx,
                                 "state": row["passage"],
                                 "instructions": row["question"],
                                 "criteria": {"yes": "The answer is yes.", "no": "The answer is no."},
                                 "label": "yes" if row["answer"] else "no"})
        else:
            for idx, row in enumerate(fetched):
                labels = row["choices"]["label"]
                texts = row["choices"]["text"]
                assert len(labels) == len(texts) and len(labels) >= 2
                assert row["answerKey"] in labels and len(set(labels)) == len(labels)
                selected.append({"id": f"arc_challenge:{row['id']}", "family": family,
                                 "source_row": idx, "state": "",
                                 "instructions": row["question"],
                                 "criteria": dict(zip(labels, texts)), "label": row["answerKey"]})
    assert len(selected) == 699
    assert len({r["id"] for r in selected}) == len(selected)
    eval_path = OUT / "eval.jsonl"
    with eval_path.open("w") as stream:
        for row in selected:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest["outputs"] = {"eval_rows": len(selected), "eval_sha256": digest(eval_path),
                           "family_counts": {"boolq": 400, "arc_challenge": 299}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["outputs"]))


if __name__ == "__main__":
    main()
