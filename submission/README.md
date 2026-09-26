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

Clone this repository and download the [v0.1.0 release asset](https://github.com/13974737898-lgtm/laya-e2-multitype/releases/download/v0.1.0/laya-e2-multitype-seed20260925.tar.gz).
Verify the archive against
`release-manifest.json` before extracting it. The archive contains a complete
model directory, including tokenizer and encoder configuration. Keep that
directory outside the code checkout if convenient.

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
export E2_MODEL_PATH="/absolute/path/to/extracted/release"
export LAYA_DEVICE=cpu
./submission/start.sh
```

Run the commands from the root of this repository after cloning the upstream
source into `laya-upstream/`. The checked-out source and `.venv` are local to
this project; `start.sh` only launches the existing environment and never
installs packages. `tmux` is required by the lifecycle scripts. Use
`./submission/stop.sh` when finished. If extracting
the archive produces a differently named top-level directory, set
`E2_MODEL_PATH` to the directory containing `model.safetensors`.

Example local request:

```bash
curl -sS http://127.0.0.1:8942/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"state":"The request is verified.","model":"jev-latest","questions":{"decision":{"type":"noul","instructions":"Is the request verified?"}}}'
```

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
