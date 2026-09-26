# E2 开源与 JevBench 提交准备状态

核对日期：2026-09-26。候选固定为 E2 第二轮权重，SHA256 `e4e3ca110dd2f294e2b3c43dd7ef9afe0352ea397ca0e7e6f7fbfb05dccf7789`。没有对 E3、JevBench 公开题或服务验收题重新训练、选择轮次或改变推理预算。

## 已完成的本机工作

- `submission/e2_service.py` 复用 Laya 0.3.20 的 Jev 兼容服务器，固定加载单一 E2 checkpoint，启动前核对权重哈希，固定 `max_len=512`、`head_max_len=192`。独立 tmux 生命周期由 `submission/start.sh` 和 `submission/stop.sh` 管理；默认只绑定 DGX `127.0.0.1:8942`。验收后已停止。
- 用 JevBench 仓库自带 `TypeSafeAdapter` 发出 choice、noul、score 三种原创新题请求；三种均 HTTP 200、标签与概率合法，和直接加载相同权重的概率逐项一致。实际结果见 `results/submission-readiness/release-acceptance.json`。这仅是接口验收，不是准确率或 sealed 验证。
- 在 DGX 建好无符号链接的自包含权重目录与 `777,062,797` 字节归档，归档 SHA256 `970c4ebbb1608d980500d8f23f1965b5b1de4ee0b556007d5702412bec1bb767`。文件清单、基础权重与运行代码版本见 `submission/release-manifest.json`。从自包含目录加载后再次通过同样的 HTTP 验收。
- `submission/MODEL_CARD.md` 写明 Apache-2.0 上游来源、E2 训练、公开题使用、效果与校准限制。研究仓库新增 Apache-2.0 `LICENSE`。`submission/JEVBENCH_ISSUE_DRAFT.md` 是尚未发送的提交草稿。

## 官方规则与仍缺的证据

[JevBench 当前提交说明](https://www.benchmarkheaven.com/jev-models)要求在其 GitHub 仓库开 issue，提供可复现端点或可运行代码、准确模型与许可、是否使用公开题。当前[榜单方法](https://github.com/fstandhartinger/jevbench/blob/main/docs/METHOD-v1.4.md)需要 534 道原版题与 308 道新 sealed 题，综合 Intelligence、Calibration、Speed、Cost。E2 仅有旧公开 231 题诊断，没有官方 sealed 分数，不能报告名次。

现有 GitHub 登录账号为 `13974737898-lgtm`；拟公开仓库 `laya-e2-multitype` 尚未创建。DGX 的 Hugging Face CLI 未登录，权重目前只在 DGX 本地持久目录；GitHub Release 可以作为一种归档目标，但尚未发布。没有建立公开端点，也没有向榜单发送 issue。向外发布代码/权重和提交 issue 是下一步的外部动作，应先确认使用哪个公开账号与仓库名称。

## 主要风险

Laya 加载该 checkpoint 时报告部分 choice 温度越界并夹取，因此输出概率不可宣称已独立校准；JevBench 旧公开集上的 ECE 为 0.186。基础 Laya 的官方 sealed 表现远低于公开题，E2 在 sealed 上可能同样退化。我们的运行用 DGX GB10 GPU，本机延迟不能直接作为榜单 Speed 分数。没有把 Banking77 的专项分类结果混入 E2。
