# E3 third-party data attribution

The E3 evaluation uses validation data from:

- [BoolQ, Google Research](https://huggingface.co/datasets/google/boolq), revision `35b264d03638db9f4ce671b711558bf7ff0f80d5`, identified by its dataset card as CC BY-SA 3.0. Original work: Christopher Clark et al., *BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions*, NAACL 2019.
- [ARC-Challenge, Allen Institute for AI](https://huggingface.co/datasets/allenai/ai2_arc), revision `210d026faf9955653af8916fad021475a3f00453`, identified by its dataset card as CC BY-SA 4.0. Original work: Peter Clark et al., *Think you have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge*, 2018.

`manifest.json` records exact file hashes and the 699-row selection. The source snapshots and transformed question text are excluded from Git; run `scripts/prepare_crosssource_e3.py` in an isolated environment with `pyarrow` to obtain the pinned files. Results and code are separate from the licenses of the original question text. Review attribution and share-alike requirements before redistributing any dataset copy.
