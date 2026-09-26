# Frozen Laya E2 Jev-compatible service

This is a fixed-checkpoint wrapper around Laya 0.3.20's `POST /v1/systemone`
server. It serves the E2 checkpoint selected on the E2 development set. It does
not select a model, prompt, threshold, or fallback based on the incoming item.
The wrapper checks the checkpoint SHA256 before loading and fixes
`max_len=512`, `head_max_len=192`, matching the E2 JevBench public diagnostic.

## DGX local use

Use the existing isolated Laya runtime. From this directory, run `./start.sh`
and use `./stop.sh` to stop only this service's tmux session. The default bind
is `127.0.0.1:8942`. `E2_BIND`, `E2_PORT`, `E2_MODEL_PATH`, `LAYA_SOURCE_ROOT`,
`LAYA_RUNTIME`, and `LAYA_DEVICE` can be set before launch. `LAYA_API_KEY` is
handled by Laya's server if an authenticated remote endpoint is later needed.
No endpoint is exposed publicly by these scripts.

## Reproduce from a fresh checkout

These commands use a project-local environment and run the server in the
foreground. They do not require tmux or access to our DGX. The archive
contains the complete model, tokenizer, and encoder configuration.

```bash
git clone https://github.com/13974737898-lgtm/laya-e2-multitype.git
cd laya-e2-multitype
curl -fL -o laya-e2-multitype-seed20260925.tar.gz \
  https://github.com/13974737898-lgtm/laya-e2-multitype/releases/download/v0.1.0/laya-e2-multitype-seed20260925.tar.gz
printf '%s  %s\n' '970c4ebbb1608d980500d8f23f1965b5b1de4ee0b556007d5702412bec1bb767' \
  laya-e2-multitype-seed20260925.tar.gz | sha256sum -c -
tar -xzf laya-e2-multitype-seed20260925.tar.gz
```

Create a dedicated Laya environment for this project. The following commands
illustrate the pinned upstream source and required serving dependencies; use a
CUDA-compatible PyTorch build for your own GPU and set `LAYA_DEVICE=cpu` when
running without one.

```bash
git clone https://github.com/NandhaKishorM/laya.git laya-upstream
git -C laya-upstream checkout 23a17522aa4942da6cce53a995a275760320b691
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e './laya-upstream[serve]'
export LAYA_SOURCE_ROOT="$PWD/laya-upstream"
export LAYA_RUNTIME="$PWD/.venv/bin/python"
export E2_MODEL_PATH="$PWD/release"
export LAYA_DEVICE=cpu
export PYTHONPATH="$PWD/laya-upstream"
export USE_TF=0
cd submission
../.venv/bin/python -m uvicorn e2_service:app --host 127.0.0.1 --port 8942 --workers 1
```

Run these commands from the repository root until `cd submission`. For a GPU,
install a CUDA-compatible PyTorch build in this environment and set
`LAYA_DEVICE=cuda`. The pinned checkout and `.venv` stay inside this project.
The optional `start.sh` and `stop.sh` manage a local tmux session instead.

Example local request:

```bash
curl -sS http://127.0.0.1:8942/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"state":"The request is verified.","model":"jev-latest","questions":{"decision":{"type":"noul","instructions":"Is the request verified?"}}}'
```

From a separate shell in a JevBench checkout, the official public diagnostic
uses its existing `typesafe` adapter:

```bash
python -m jevbench.cli run \
  --tasks datasets/public/easy.jsonl,datasets/public/original.jsonl,datasets/public/hard.jsonl \
  --adapter typesafe --endpoint http://127.0.0.1:8942 \
  --key-env '' --model jev-latest --cost-basis self_hosted --reserve-usd 0 \
  --results out/laya-e2-public.jsonl --raw-dir out/laya-e2-raw
```

Our earlier 231-item public run reported 138 correct. It is a diagnostic
identity check only, not an official or sealed score. The three original
fixture requests recorded in `results/submission-readiness/release-acceptance.json`
also passed the official adapter and matched direct checkpoint inference.

The [JevBench submission instructions](https://www.benchmarkheaven.com/jev-models)
call for a GitHub issue containing a reproducible endpoint or runnable code,
exact model and license, and a disclosure of public JevBench item use. This
directory is a publicly available runnable package, not a public endpoint.

## Acceptance and release files

`acceptance.py` sends three original fixtures through JevBench's own
`TypeSafeAdapter` and compares the service probabilities with direct
`laya.load(...).predict(...)` calls. The recorded result is
`results/submission-readiness/release-acceptance.json`. The checks cover
`choice`, `noul`, `score`, exact label sets, probability sums, usage and direct
checkpoint parity. They verify interface behavior; they are not a benchmark
score.

The portable model directory on DGX is indexed by
`submission/release-manifest.json`, with the model card in `MODEL_CARD.md`.
The archived directory is published as the [v0.1.0 release asset](https://github.com/13974737898-lgtm/laya-e2-multitype/releases/tag/v0.1.0).
