#!/usr/bin/env python3
"""Small supervised pilot on Laya's native choice head; test split is never opened."""
import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import torch
from safetensors.torch import save_file
from torch.utils.data import DataLoader

sys.path.insert(0, "/home/maolinqi/mlq/laya")
import laya
from laya.common import build_sequence, QTYPES

ROOT = Path(__file__).resolve().parent


def read_items(path, agent):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    items = []
    for row in rows:
        question = {"type": "choice",
                    "instructions": "Does the statement logically follow from the context? Statement: " + row["question"],
                    "criteria": {
                        "entailment": "The statement follows from the context.",
                        "not entailment": "The statement does not follow from the context."}}
        internal = agent._to_internal(question)
        ids, markers = build_sequence(agent.tok, row["context"], internal, 512, 192)
        assert len(markers) == 2
        items.append({"ids": ids, "markers": markers,
                      "label": 0 if row["label"] == "entailment" else 1,
                      "qtype": QTYPES["choice"]})
    return items


def collate(batch, pad):
    length = max(len(item["ids"]) for item in batch)
    ids = torch.full((len(batch), length), pad, dtype=torch.long)
    mask = torch.zeros_like(ids)
    markers = torch.tensor([item["markers"] for item in batch], dtype=torch.long)
    labels = torch.tensor([item["label"] for item in batch], dtype=torch.long)
    qtype = torch.full((len(batch),), QTYPES["choice"], dtype=torch.long)
    for i, item in enumerate(batch):
        ids[i, :len(item["ids"])] = torch.tensor(item["ids"])
        mask[i, :len(item["ids"])] = 1
    return ids, mask, markers, torch.ones_like(markers, dtype=torch.bool), qtype, labels


@torch.inference_mode()
def evaluate(model, loader):
    model.eval()
    correct = total = 0
    nll = 0.0
    for batch in loader:
        ids, mask, markers, marker_mask, qtype, labels = (x.to("cuda") for x in batch)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            logits, _ = model(ids, mask, markers, marker_mask, qtype)
        logits = logits.float()
        correct += (logits.argmax(-1) == labels).sum().item()
        nll += torch.nn.functional.cross_entropy(logits, labels, reduction="sum").item()
        total += len(labels)
    return {"n": total, "accuracy": correct / total, "nll": nll / total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260925)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--accum", type=int, default=4)
    args = parser.parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(4)
    agent = laya.load("/home/maolinqi/mlq/laya-jevbench-baseline/model", device="cuda")
    model = agent.model
    model.encoder.config.reference_compile = False
    model.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.head_checkpointing = True
    train = read_items(ROOT / "pilot" / "train.jsonl", agent)
    dev = read_items(ROOT / "pilot" / "dev.jsonl", agent)
    train_loader = DataLoader(train, batch_size=args.batch, shuffle=True,
                              generator=torch.Generator().manual_seed(args.seed),
                              collate_fn=lambda x: collate(x, agent.tok.pad_token_id))
    dev_loader = DataLoader(dev, batch_size=args.batch * 4, shuffle=False,
                            collate_fn=lambda x: collate(x, agent.tok.pad_token_id))
    run = ROOT / "runs" / args.run_name
    assert not run.exists(), "Refusing to overwrite an existing run"
    run.mkdir(parents=True)
    config = {**vars(args), "training_examples": len(train), "dev_examples": len(dev),
              "model_revision": "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
              "data_manifest": json.loads((ROOT / "pilot" / "manifest.json").read_text()),
              "objective": "hard-label supervised CE on native Laya choice head",
              "selection": "highest dev accuracy; tie lowest dev NLL", "test_used": False,
              "torch": torch.__version__}
    (run / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    params = [{"params": [p for n, p in model.named_parameters() if n.startswith("encoder.")], "lr": 2e-5},
              {"params": [p for n, p in model.named_parameters() if not n.startswith("encoder.")], "lr": 1e-4}]
    optimizer = torch.optim.AdamW(params, weight_decay=.01)
    total_updates = math.ceil(len(train_loader) / args.accum) * args.epochs
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_updates)
    best = None
    with (run / "metrics.jsonl").open("w") as stream:
        for epoch in range(1, args.epochs + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            running = 0.0
            started = time.perf_counter()
            for step, batch in enumerate(train_loader, 1):
                ids, mask, markers, marker_mask, qtype, labels = (x.to("cuda") for x in batch)
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    logits, act = model(ids, mask, markers, marker_mask, qtype)
                loss = torch.nn.functional.cross_entropy(logits.float(), labels)
                (loss / args.accum + 0.0 * act.sum()).backward()
                running += loss.item() * len(labels)
                if step % args.accum == 0 or step == len(train_loader):
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                if step % 100 == 0:
                    print(f"epoch={epoch} step={step}/{len(train_loader)} loss={loss.item():.4f}", flush=True)
            metrics = evaluate(model, dev_loader)
            metrics.update({"epoch": epoch, "train_loss": running / len(train),
                            "epoch_wall_s": time.perf_counter() - started})
            stream.write(json.dumps(metrics) + "\n")
            stream.flush()
            print(json.dumps(metrics), flush=True)
            if best is None or (metrics["accuracy"], -metrics["nll"]) > (best["accuracy"], -best["nll"]):
                best = metrics
                weights = {k: v.detach().to("cpu", dtype=torch.float16).contiguous()
                           for k, v in model.state_dict().items()}
                save_file(weights, run / "best.safetensors")
                (run / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print("done", flush=True)


if __name__ == "__main__":
    main()
