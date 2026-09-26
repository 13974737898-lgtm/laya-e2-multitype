# Submitted to JevBench as issue #103

Submitted issue: https://github.com/fstandhartinger/jevbench/issues/103
The issue pins source revision `50c0012a6c2e4d40a9f1d5773c4546debf798a0f`.

**Title:** JevBench evaluation request: Laya E2 Multitype, frozen 421M open checkpoint

I would like to submit **Laya E2 Multitype** for a new JevBench evaluation. It
is a frozen derivative of the English `convaiinnovations/laya` checkpoint,
fine-tuned on independently generated policy, temporal, evidence and routing
decisions. It is a native typed-decision model and returns probabilities for
`choice`, `noul` and `score`; there is no LLM fallback, item-dependent routing,
or threshold tuning during inference.

- **Runnable code:** `https://github.com/13974737898-lgtm/laya-e2-multitype`
  at the source revision linked in the submitted issue. Fresh-checkout
  instructions are in `submission/README.md`.
- **Exact weights:** [v0.1.0 release asset](https://github.com/13974737898-lgtm/laya-e2-multitype/releases/download/v0.1.0/laya-e2-multitype-seed20260925.tar.gz).
  Archive size 777,062,797 bytes. Archive SHA256:
  `970c4ebbb1608d980500d8f23f1965b5b1de4ee0b556007d5702412bec1bb767`.
  Checkpoint SHA256:
  `e4e3ca110dd2f294e2b3c43dd7ef9afe0352ea397ca0e7e6f7fbfb05dccf7789`.
- **License:** Apache-2.0 for code and derivative weights; the base Laya code
  and checkpoint are also labeled Apache-2.0. The model card includes upstream
  attribution, training details and limits.
- **Runtime:** Laya 0.3.20, source commit
  `23a17522aa4942da6cce53a995a275760320b691`, Python project-local
  environment. The `submission/` wrapper uses Laya's own Jev-compatible
  `POST /v1/systemone` server and fixes `max_len=512`, `head_max_len=192`.
  A local run using JevBench's `TypeSafeAdapter` passed original `choice`,
  `noul` and `score` fixtures and matched direct checkpoint probabilities.
- **Training data and selection:** 9,600 self-authored generated train items;
  1,920 dev and 1,920 test items. Epoch 2 was selected by dev accuracy.
  Generator, data hashes, training script and run manifest are in the code
  repository. No JevBench item was used for gradient training or epoch
  selection.
- **Public JevBench disclosure:** We evaluated the base, E1 and frozen E2
  checkpoints on the older 231-item public slice. E1's public-set outcome
  influenced the decision to broaden E2's training tasks, so public items did
  affect the research trajectory. E2 scored 138/231 versus 134/231 for the
  base in our local diagnostic; the paired interval spans zero. This is not a
  v1.4 score. We have not seen or tested on sealed items.
- **Calibration caveat:** Laya 0.3.20 warns that some saved choice
  temperatures are outside its accepted range and clips them at load time.
  Our public-slice ECE was 0.186, so we do not claim independently calibrated
  probabilities. Please report the benchmark's calibration measurement as
  observed.

For a clean run, extract the release archive, set `E2_MODEL_PATH` to the
extracted `release/` directory, install pinned upstream Laya with its `serve`
extra in a project-local environment, then run `submission/start.sh`. The
service binds `127.0.0.1:8942` by default and responds at
`POST /v1/systemone`. `submission/README.md` gives the exact commands.

We prefer evaluator-controlled execution from the published code and weights
so the sealed item text need not be sent to our machine. If that is not
available, please specify the supported endpoint intake procedure before we
expose a remote service.
