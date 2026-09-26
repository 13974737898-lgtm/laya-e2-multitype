"""Serve the frozen E2 checkpoint through Laya's Jev-compatible API.

Launch with the project-local Laya runtime and PYTHONPATH pointed at the
pinned Laya checkout.  This service intentionally never routes to another
checkpoint, regardless of the client's model alias.
"""

import hashlib
import os
from pathlib import Path

import laya
from laya.serve import create_app

EXPECTED_CHECKPOINT_SHA256 = "e4e3ca110dd2f294e2b3c43dd7ef9afe0352ea397ca0e7e6f7fbfb05dccf7789"
MODEL_NAME = "laya-e2-multitype-seed20260925"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class FrozenE2Router:
    def __init__(self):
        raw = os.environ.get("E2_MODEL_PATH")
        if not raw:
            raise RuntimeError("E2_MODEL_PATH must name the frozen checkpoint export directory")
        self.path = Path(raw).resolve(strict=True)
        checkpoint = self.path / "model.safetensors"
        if sha256(checkpoint) != EXPECTED_CHECKPOINT_SHA256:
            raise RuntimeError("E2 checkpoint SHA256 mismatch")
        self.agent = laya.load(str(self.path), device=os.environ.get("LAYA_DEVICE") or "cpu")

    @property
    def loaded(self):
        return [MODEL_NAME]

    def predict(self, state, questions, model=None):
        # `model` is a wire-protocol alias; this service serves one frozen model.
        output = self.agent.predict(state, questions, max_len=512, head_max_len=192)
        output["model"] = MODEL_NAME
        return output


app = create_app(router=FrozenE2Router())
