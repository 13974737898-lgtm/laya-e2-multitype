---
license: apache-2.0
library_name: laya
pipeline_tag: text-classification
tags:
  - laya
  - jev-compatible
  - decision-model
  - experimental
---

# Laya E2 Multitype (frozen research checkpoint)

This is a 421M-parameter English Laya decision model fine-tuned from
[`convaiinnovations/laya`](https://huggingface.co/convaiinnovations/laya),
whose model card labels the base weights Apache-2.0. This derivative retains
the upstream attribution and uses Apache-2.0 for the released checkpoint.

## Intended use

Research on bounded typed decisions (`choice`, `noul`, `score`) and independent
evaluation of decision-model generalization. Use Laya 0.3.20 or the pinned
source commit `23a17522aa4942da6cce53a995a275760320b691`. Load the
checkpoint with `laya.load(path)` or run the fixed-checkpoint
`submission/e2_service.py` Jev-compatible server. The service uses
`max_len=512` and `head_max_len=192`.

## Training and model selection

- Base model: English root checkpoint of `convaiinnovations/laya`. Locally
  recorded base-weight SHA256:
  `891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c`.
- Data: 9,600 self-authored generated training tasks across policy, temporal,
  evidence and routing decisions; 1,920 development and 1,920 held-out tasks.
  The generated splits share a rule generator. Generator, selection seed and
  hashes are in `data/multitype-e2/`.
- Training: two epochs from base weights, seed `20260925`, batch 8,
  accumulation 4, encoder learning rate `2e-5`, other learning rate `1e-4`,
  hard-label cross-entropy. Epoch 2 was selected by development accuracy.
- Frozen checkpoint SHA256:
  `e4e3ca110dd2f294e2b3c43dd7ef9afe0352ea397ca0e7e6f7fbfb05dccf7789`.
  Size: 842,609,220 bytes. The exported `encoder/`, `tokenizer/`, and
  `rl_agent_config.json` accompany it.

## Observed results

| Diagnostic | Base Laya | This checkpoint |
|---|---:|---:|
| Same-generator E2 test, 1,920 tasks | 37.55% | 98.54% |
| JevBench older 231-item public slice | 58.01% | 59.74% |
| BoolQ validation sample, 400 questions | 75.75% | 79.25% |
| ARC-Challenge validation, 299 questions | 27.09% | 29.10% |

The 231-item JevBench gain was 4 questions with a paired 95% bootstrap interval
spanning zero. It is **not** a JevBench v1.4.2 score. The E2 test shares its
generator with training. BoolQ and ARC are public and may have been seen during
base pretraining. The checkpoint has not been measured on the v1.4 sealed set.

The model was **not** trained on JevBench public items, but those public items
were inspected in earlier project evaluations. E1's public-set result influenced
the decision to broaden E2 training tasks. No public JevBench item was used to
choose E2's epoch, thresholds or inference-time route.

## Probability and deployment limits

The current Laya runtime warns that some saved choice temperatures, including
`choice:11+`, fall outside its accepted range and are clipped at load time.
Treat affected confidence values as uncalibrated. On the 231 public JevBench
items, E2's ECE was 0.186 versus 0.094 for the base checkpoint. Do not describe
this model as independently calibrated. The English model has a 512-token
input limit; longer inputs may be truncated. The DGX evaluation used NVIDIA
GB10 and the project-local Laya environment.

## Reproduction

The repository contains training code, the generated data and hashes, fixed
experiment plans, per-item local results, and DGX run manifests. The
`submission/` directory contains the Jev-compatible service and an acceptance
script that checks `choice`, `noul`, and `score` through JevBench's own adapter.
Third-party BoolQ and ARC texts are downloaded from pinned source revisions
and are not included in this checkpoint.

## Attribution

Based on Convai Innovations' Apache-2.0 Laya code and weights. See
[`convaiinnovations/laya`](https://huggingface.co/convaiinnovations/laya) and
[`NandhaKishorM/laya`](https://github.com/NandhaKishorM/laya). The E2 training
task generator and fine-tuning code are part of this research repository.
