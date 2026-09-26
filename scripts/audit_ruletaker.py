#!/usr/bin/env python3
"""Audit a pinned RuleTaker mirror without reading or exposing answer keys elsewhere."""
import collections
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import pyarrow.parquet as pq


def normalized(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w]+", " ", value)).strip()


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    split_data = {}
    for split in ("train", "dev", "test"):
        paths = sorted((source / "data").glob(f"{split}-*.parquet"))
        assert len(paths) == 1, (split, paths)
        path = paths[0]
        labels = collections.Counter()
        configs = collections.Counter()
        pair_labels = collections.defaultdict(set)
        contexts = set()
        questions = set()
        lengths = []
        nulls = 0
        rows = 0
        parquet = pq.ParquetFile(path)
        assert parquet.schema_arrow.names == ["context", "question", "label", "config"]
        for batch in parquet.iter_batches(batch_size=8192):
            cols = batch.to_pydict()
            for context, question, label, config in zip(*(cols[k] for k in parquet.schema_arrow.names)):
                rows += 1
                if any(x is None for x in (context, question, label, config)):
                    nulls += 1
                    continue
                nc, nq = normalized(context), normalized(question)
                key = digest(nc + "\x1f" + nq)
                pair_labels[key].add(label)
                contexts.add(digest(nc))
                questions.add(digest(nq))
                lengths.append(len(context.split()) + len(question.split()))
                labels[label] += 1
                configs[config] += 1
        split_data[split] = {
            "file": path.name, "sha256": file_sha256(path), "rows": rows,
            "labels": dict(labels), "configs": dict(configs), "null_rows": nulls,
            "unique_context_question": len(pair_labels),
            "duplicate_pair_rows": rows - nulls - len(pair_labels),
            "conflicting_pair_labels": sum(len(x) > 1 for x in pair_labels.values()),
            "unique_contexts": len(contexts), "unique_questions": len(questions),
            "max_word_count": max(lengths) if lengths else None,
            "p95_word_count": sorted(lengths)[int(.95 * (len(lengths) - 1))] if lengths else None,
            "_pairs": set(pair_labels), "_contexts": contexts, "_questions": questions,
            "_pair_labels": pair_labels,
        }
    overlaps = {}
    for a, b in (("train", "dev"), ("train", "test"), ("dev", "test")):
        pa, pb = split_data[a], split_data[b]
        shared = pa["_pairs"] & pb["_pairs"]
        overlaps[f"{a}_{b}"] = {
            "same_context_question": len(shared),
            "same_context": len(pa["_contexts"] & pb["_contexts"]),
            "same_question": len(pa["_questions"] & pb["_questions"]),
            "conflicting_label_for_same_pair": sum(pa["_pair_labels"][k] != pb["_pair_labels"][k] for k in shared),
        }
    for data in split_data.values():
        for key in list(data):
            if key.startswith("_"):
                del data[key]
    report = {"normalization": "NFKC + casefold + punctuation/whitespace collapse",
              "splits": split_data, "overlap": overlaps}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"rows": {k: v["rows"] for k, v in split_data.items()},
                      "overlap": overlaps}, ensure_ascii=False))


if __name__ == "__main__":
    main()
