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

Example local request:

```bash
curl -sS http://127.0.0.1:8942/v1/systemone \
  -H 'Content-Type: application/json' \
  -d '{"state":"The request is verified.","model":"jev-latest","questions":{"decision":{"type":"noul","instructions":"Is the request verified?"}}}'
```

The [JevBench submission instructions](https://www.benchmarkheaven.com/jev-models)
call for a GitHub issue containing a reproducible endpoint or runnable code,
exact model and license, and a disclosure of public JevBench item use. This
directory is a local runnable package, not a submitted or public endpoint.

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
The archived directory is the intended model asset for an eventual public
release. Publishing that asset and creating a JevBench issue are separate
external actions; neither has happened yet.
