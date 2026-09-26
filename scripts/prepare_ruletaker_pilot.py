#!/usr/bin/env python3
"""Build fixed, unique, stratified RuleTaker pilot splits from pinned Parquet files."""
import collections
import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq
from audit_ruletaker import digest, file_sha256, normalized

SEED = "laya-ruletaker-pilot-20260925-v1"
QUOTAS = {"train": 625, "dev": 125, "test": 125}  # per nonredundant (config, label)


def main():
    source = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    report = {"seed": SEED, "quota_per_config_label": QUOTAS,
              "normalization": "NFKC + casefold + punctuation/whitespace collapse",
              "source_files": {}, "splits": {}}
    seen_across = set()
    for split in ("train", "dev", "test"):
        paths = sorted((source / "data").glob(f"{split}-*.parquet"))
        assert len(paths) == 1
        path = paths[0]
        report["source_files"][split] = {"name": path.name, "sha256": file_sha256(path)}
        unique_rows = {}
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(batch_size=8192):
            cols = batch.to_pydict()
            for context, question, label, config in zip(*(cols[k] for k in parquet.schema_arrow.names)):
                if config == "NatLang":
                    continue  # Its pairs overlap other configurations inconsistently across splits.
                key = digest(normalized(context) + "\x1f" + normalized(question))
                unique_rows.setdefault(key, {"context": context, "question": question,
                                             "label": label, "config": config, "pair_sha256": key})
        selected = collections.defaultdict(dict)
        for key, row in unique_rows.items():
            selected[(row["config"], row["label"])][key] = row
        counts = {f"{cfg}|{label}": len(rows) for (cfg, label), rows in selected.items()}
        assert len(selected) == 14 and not any(k.startswith("NatLang|") for k in counts), counts
        chosen = []
        for (config, label), rows in sorted(selected.items()):
            assert len(rows) >= QUOTAS[split], (split, config, label, len(rows))
            ranked = sorted(rows.values(), key=lambda row: digest(SEED + "|" + row["pair_sha256"]))
            chosen.extend(ranked[:QUOTAS[split]])
        chosen.sort(key=lambda row: (row["config"], row["label"], row["pair_sha256"]))
        keys = {row["pair_sha256"] for row in chosen}
        assert len(keys) == len(chosen) and not (seen_across & keys)
        seen_across.update(keys)
        output = out / f"{split}.jsonl"
        with output.open("w") as stream:
            for row in chosen:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        report["splits"][split] = {"rows": len(chosen), "sha256": file_sha256(output),
                                   "source_unique_by_config_label": counts}
    (out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v["rows"] for k, v in report["splits"].items()}))


if __name__ == "__main__":
    main()
